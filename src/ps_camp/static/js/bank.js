document.addEventListener('DOMContentLoaded', () => {
    const modal      = document.getElementById('transfer-modal');
    const showBtn    = document.getElementById('show-transfer');
    const cancelBtn  = document.getElementById('cancel-transfer');
    const form       = document.getElementById('transfer-form');
    const balanceDom = document.getElementById('balance');

    // ===== 開關 modal =====
    showBtn?.addEventListener('click', () => {
        form.reset();
        const suggestionsBox = document.getElementById('search-suggestions');
        if (suggestionsBox) suggestionsBox.innerHTML = '';
        modal.style.display = 'flex';
    });

    cancelBtn?.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    modal?.addEventListener('click', e => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // ===== 提交轉帳 =====
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

    // ===== 模糊搜尋區（含注音輸入支援 + Debug） =====
    const searchInput = document.getElementById('recipient-search');
    const suggestionsBox = document.getElementById('search-suggestions');
    const accountInput = document.querySelector('input[name="to_account_number"]');

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
            if (!isComposing) {

                handleSearch();
            }
        });

        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
                suggestionsBox.innerHTML = '';
            }
        });
    }

    async function handleSearch() {
        const query = searchInput.value.trim();

        if (query.length < 1) {
            suggestionsBox.innerHTML = '';

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
                return;
            }

            users.forEach((user, i) => {

                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                item.textContent = `${user.fullname}（${user.username}）`;

                item.addEventListener('click', () => {

                    accountInput.value = user.account_number;
                    searchInput.value = user.fullname;
                    suggestionsBox.innerHTML = '';
                });

                suggestionsBox.appendChild(item);
            });
        } catch (err) {

            suggestionsBox.innerHTML = '';
        }
    }
});
