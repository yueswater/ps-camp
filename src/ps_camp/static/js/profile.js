document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("profile-form");
    const oldPwd = document.getElementById("old_password");
    const newPwd = document.getElementById("new_password");
    const confirmPwd = document.getElementById("confirm_password");

    form.addEventListener("submit", function (e) {
        if (newPwd.value !== confirmPwd.value) {
            e.preventDefault();
            alert("新密碼與確認密碼不一致！");
        }
    });
});
