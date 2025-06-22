document.addEventListener('DOMContentLoaded', () => {
    const modal      = document.getElementById('transfer-modal');
    const showBtn    = document.getElementById('show-transfer');
    const cancelBtn  = document.getElementById('cancel-transfer');
    const form       = document.getElementById('transfer-form');
    const balanceDom = document.getElementById('balance');

    // 開啟轉帳視窗
    showBtn?.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

    // 關閉
    cancelBtn?.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    // 點 overlay 關閉
    modal?.addEventListener('click', e => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // 送出轉帳
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
                // 即時更新餘額
                if (balanceDom) balanceDom.textContent = res.new_balance;
                // 可選：即時 Append 交易到表格
                setTimeout(() => location.reload(), 800);
            } else {
                SandstormApp.showNotification(res.message || '轉帳失敗', 'error');
            }
        })
        .catch(() => {
            SandstormApp.hideLoading();
            SandstormApp.showNotification('伺服器錯誤，請稍後再試', 'error');
        })
        .finally(() => {
            modal.style.display = 'none';
            form.reset();
        });
    });
});
