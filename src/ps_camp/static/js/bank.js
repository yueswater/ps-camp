document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('transfer-modal');
    const showBtn = document.getElementById('show-transfer');
    const cancelBtn = document.getElementById('cancel-transfer-btn');
    const form = document.getElementById('transfer-form');
    const balanceDom = document.getElementById('balance');

    const searchInput = document.getElementById('recipient-search');
    const suggestionsBox = document.getElementById('search-suggestions');
    const accountInput = document.querySelector('input[name="to_account_number"]');
    const amountInput = document.querySelector('input[name="amount"]');
    const feeAmountSpan = document.querySelector('.fee-amount');
    const totalAmountSpan = document.querySelector('.total-amount');
    const qrModal = document.getElementById('qr-modal');
    const openQrBtn = document.getElementById('generate-qr');
    const closeQrBtn = document.getElementById('close-qr-modal');
    const scanModal = document.getElementById('qr-scan-modal');
    const scanBtn = document.getElementById('scan-qr');
    const closeScanBtn = document.getElementById('close-qr-scan');
    const video = document.getElementById('qr-video');
    let scanStream;

    // === 開啟 modal ===
    showBtn?.addEventListener('click', () => {
        form.reset();
        suggestionsBox.innerHTML = '';
        suggestionsBox.style.display = 'none';
        modal.style.display = 'flex';
        updateTotalAmount();
    });

    ['cancel-transfer-btn', 'cancel-transfer'].forEach(id => {
        document.getElementById(id)?.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    });

    // === 關閉 modal ===
    cancelBtn?.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    modal?.addEventListener('click', e => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // === 提交表單 ===
    form?.addEventListener('submit', e => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(form).entries());
        if (!data.to_account_number || !data.amount) return;

        SandstormApp.showLoading();
        fetch('/api/bank/transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(r => r.json())
            .then(res => {
                SandstormApp.hideLoading();
                if (res.success) {
                    SandstormApp.showNotification('轉帳成功', 'success');
                    if (balanceDom) balanceDom.textContent = res.new_balance;
                    setTimeout(() => location.reload(), 800);
                } else {
                    SandstormApp.showNotification(res.message || '轉帳失敗', 'error');
                }
            })
            .catch(() => {
                SandstormApp.hideLoading();
                SandstormApp.showNotification('伺服器錯誤，請稍後再試', 'error');
            });
    });

    openQrBtn?.addEventListener('click', () => {
        const qrTarget = document.getElementById('qr-code');
        qrTarget.innerHTML = '';
        new QRCode(qrTarget, {
            text: '{{ account.account_number }}',
            width: 180,
            height: 180
        });
        qrModal.style.display = 'flex';
    });

    closeQrBtn?.addEventListener('click', () => {
        qrModal.style.display = 'none';
    });

    scanBtn?.addEventListener('click', async () => {
        scanModal.style.display = 'flex';
        scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        video.srcObject = scanStream;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        const scanLoop = () => {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const result = jsQR(imageData.data, canvas.width, canvas.height);
                if (result) {
                    scanStream.getTracks().forEach(track => track.stop());
                    scanModal.style.display = 'none';

                    accountInput.value = result.data;
                    scanModal.style.display = 'none';

                    document.getElementById('show-transfer')?.click();
                    setTimeout(() => {
                        document.querySelector('input[name="amount"]')?.focus();
                    }, 200);
                    
                    return;
                }
            }
            requestAnimationFrame(scanLoop);
        };

        scanLoop();
    });

    closeScanBtn?.addEventListener('click', () => {
        scanModal.style.display = 'none';
        if (scanStream) scanStream.getTracks().forEach(track => track.stop());
    });

    // === 自動補全搜尋 ===
    let isComposing = false;

    if (searchInput && suggestionsBox && accountInput) {
        searchInput.addEventListener('compositionstart', () => {
            isComposing = true;
        });

        searchInput.addEventListener('compositionend', () => {
            isComposing = false;
            handleSearch();
        });

        searchInput.addEventListener('input', () => {
            if (!isComposing) handleSearch();
        });

        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
                suggestionsBox.innerHTML = '';
                suggestionsBox.style.display = 'none';
            }
        });
    }

    async function handleSearch() {
        const query = searchInput.value.trim();
        if (query.length < 1) {
            suggestionsBox.innerHTML = '';
            suggestionsBox.style.display = 'none';
            return;
        }

        try {
            const res = await fetch(`/api/search-users?q=${encodeURIComponent(query)}`);
            const users = await res.json();

            suggestionsBox.innerHTML = '';

            if (users.length === 0) {
                const noneItem = document.createElement('div');
                noneItem.className = 'autocomplete-item';
                noneItem.textContent = '找不到相關使用者';
                noneItem.style.color = '#888';
                suggestionsBox.appendChild(noneItem);
                suggestionsBox.style.display = 'block';
                return;
            }

            users.forEach((user) => {
                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                item.textContent = `${user.fullname}（${user.username}）`;
                item.addEventListener('click', () => {
                    accountInput.value = user.account_number;
                    searchInput.value = user.fullname;
                    suggestionsBox.innerHTML = '';
                    suggestionsBox.style.display = 'none';
                });
                suggestionsBox.appendChild(item);
            });

            suggestionsBox.style.display = 'block';
        } catch (err) {
            suggestionsBox.innerHTML = '';
            suggestionsBox.style.display = 'none';
        }
    }

    // === 即時更新總計金額（含手續費） ===
    function updateTotalAmount() {
        const amount = parseInt(amountInput.value, 10) || 0;
        const fee = 0;  // 若未來有手續費可改
        const total = amount + fee;

        if (feeAmountSpan) {
            feeAmountSpan.textContent = `NT$ ${fee.toLocaleString()}`;
        }

        if (totalAmountSpan) {
            totalAmountSpan.textContent = `NT$ ${total.toLocaleString()}`;
            totalAmountSpan.dataset.amount = total;
        }
    }

    amountInput?.addEventListener('input', updateTotalAmount);
});
