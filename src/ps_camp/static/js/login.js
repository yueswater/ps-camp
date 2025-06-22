document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".auth-form");

    if (!form) return;

    // 自訂驗證，避免瀏覽器跳出原生提示泡泡
    form.addEventListener("submit", (e) => {
        const username = document.getElementById("username");
        const password = document.getElementById("password");

        // 去除前後空白後檢查
        const usernameEmpty = !username.value.trim();
        const passwordEmpty = !password.value.trim();

        if (usernameEmpty || passwordEmpty) {
            e.preventDefault(); // 阻止表單提交

            // 顯示 alert 或可改成自訂錯誤區塊
            alert("請輸入帳號與密碼");

            // 聚焦第一個有錯的欄位
            if (usernameEmpty) {
                username.focus();
            } else {
                password.focus();
            }

            return;
        }

        console.log("表單已送出");
    });

    // 如果伺服器回傳錯誤，聚焦錯誤欄位（後端會加上 .error class）
    const errorInput = document.querySelector("input.error");
    if (errorInput) {
        errorInput.scrollIntoView({ behavior: "smooth", block: "center" });
        errorInput.focus();
    }
});
