document.addEventListener("DOMContentLoaded", function () {
    // 🔸 Modal 開關邏輯
    const avatar = document.getElementById("avatar");
    const modal = document.getElementById("avatar-modal");
    const closeBtn = modal?.querySelector(".close");

    avatar?.addEventListener("click", () => {
        if (modal) modal.style.display = "block";
    });

    closeBtn?.addEventListener("click", () => {
        modal.style.display = "none";
    });

    window.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });

    // 🔸 密碼一致性檢查
    const form = document.getElementById("profile-form");
    const newPwd = document.getElementById("new_password");
    const confirmPwd = document.getElementById("confirm_password");

    form?.addEventListener("submit", function (e) {
        if (newPwd?.value !== confirmPwd?.value) {
            e.preventDefault();
            alert("新密碼與確認密碼不一致！");
        }
    });

    // 🔸 Dropzone 上傳 + 預覽功能
    const dropzone = document.getElementById("avatar-dropzone");
    const fileInput = document.getElementById("avatar-input");
    const previewContainer = document.getElementById("preview-container");
    const previewImg = document.getElementById("preview-img");

    if (dropzone && fileInput && previewContainer && previewImg) {
        dropzone.addEventListener("click", () => fileInput.click());

        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });

        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("dragover");
        });

        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
        });

        fileInput.addEventListener("change", () => {
            const file = fileInput.files[0];
            if (file) handleFile(file);
        });

        function handleFile(file) {
            if (!file.type.startsWith("image/")) {
                alert("請選擇圖片檔案！");
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                previewContainer.style.display = "block";
                dropzone.style.display = "none";
            };
            reader.readAsDataURL(file);
        }
    }
});
