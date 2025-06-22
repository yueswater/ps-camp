document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".auth-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            // 可以視需要添加前端驗證
            console.log("表單已送出");
        });
    }
});
