document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".auth-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            const username = document.getElementById("username").value.trim();
            const fullname = document.getElementById("fullname").value.trim();
            const password = document.getElementById("password").value.trim();
            const role = document.getElementById("role").value.trim();

            if (!username || !fullname || !password || !role) {
                alert("請完整填寫所有欄位");
                e.preventDefault();
            }
        });
    }
});
