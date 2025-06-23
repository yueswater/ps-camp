document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector('.error-page');
    const redirectUrl = container.dataset.redirectUrl;
    let seconds = 5;

    const countdownEl = document.getElementById('countdown');
    const interval = setInterval(() => {
        seconds--;
        countdownEl.textContent = seconds;
        if (seconds === 0) {
            clearInterval(interval);
            window.location.href = redirectUrl;
        }
    }, 1000);
});
