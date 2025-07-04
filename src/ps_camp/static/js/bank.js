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

    modal?.addEventListener('click', e => {
        if (e.target === modal) modal.style.display = 'none';
    });

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

    // === 產生 QR Code（只放 account_number） ===
    openQrBtn?.addEventListener('click', () => {
        const qrTarget = document.getElementById('qr-code');
        qrTarget.innerHTML = '';

        const accountNumber = openQrBtn.dataset.account;

        console.log("🚀 產生 QR 內容（純帳號）：", accountNumber);

        new QRCode(qrTarget, {
            text: accountNumber,
            width: 180,
            height: 180
        });

        qrModal.style.display = 'flex';
    });

    closeQrBtn?.addEventListener('click', () => {
        qrModal.style.display = 'none';
    });

    // === 掃描 QR Code（讀帳號＋自動補人名）===
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

                    const scannedAccount = result.data;
                    console.log("📦 掃描帳號：", scannedAccount);

                    document.getElementById('show-transfer')?.click();  // 開 modal

                    setTimeout(() => {
                        const accountInput = document.querySelector('input[name="to_account_number"]');
                        const searchInput = document.getElementById('recipient-search');

                        console.log("🧪 accountInput 是否抓到？", accountInput);
                        console.log("🧪 searchInput 是否抓到？", searchInput);

                        if (accountInput) {
                            accountInput.value = scannedAccount;
                            console.log("✅ 已寫入收款帳號欄位");
                        } else {
                            console.warn("❌ 找不到收款帳號 input");
                        }

                        if (searchInput) {
                            fetch(`/api/lookup-user-by-account?q=${encodeURIComponent(scannedAccount)}`)
                                .then(r => r.json())
                                .then(res => {
                                    console.log("📋 查詢 API 回傳：", res);
                                    const fullname = res?.fullname;
                                    if (fullname) {
                                        searchInput.value = fullname;
                                        console.log("✅ 已寫入戶名：", fullname);
                                    } else {
                                        console.warn("⚠️ 查無 fullname 資料");
                                    }
                                });
                        }

                        amountInput?.focus();
                    }, 400);

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
        searchInput.addEventListener('compositionstart', () => { isComposing = true; });
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

    // === 金額變動時更新總計 ===
    function updateTotalAmount() {
        const amount = parseInt(amountInput.value, 10) || 0;
        const fee = 0;
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
