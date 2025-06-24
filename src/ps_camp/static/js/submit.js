document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.querySelector("#proposal_pdf");
  const dropzone = document.querySelector("#dropzone");
  const textEl = document.querySelector("#fileLabel");

  // 點擊整個 dropzone 區域 → 開啟 file dialog
  if (dropzone && fileInput && textEl) {
    dropzone.addEventListener("click", () => {
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file) {
        textEl.textContent = `已選擇：${file.name}`;
        dropzone.classList.remove("error");
      } else {
        textEl.textContent = "點擊或拖曳上傳 PDF 檔案";
      }
    });
  }

  // 表單驗證
  const form = document.querySelector(".submit-form");

  if (form && fileInput && dropzone && textEl) {
    form.addEventListener("submit", (e) => {
      const file = fileInput.files[0];

      if (!file) {
        e.preventDefault();
        dropzone.classList.add("error");
        textEl.textContent = "⚠ 請先選擇一個 PDF 檔案再提交";
        return;
      }

      dropzone.classList.add("loading");
    });
  }
});
