document.addEventListener("DOMContentLoaded", () => {
  // 處理所有 file-dropzone 區塊
  const dropzones = document.querySelectorAll(".file-dropzone");

  dropzones.forEach(dropzone => {
    const inputId = dropzone.dataset.inputId;
    const labelId = dropzone.dataset.labelId;
    const fileInput = document.getElementById(inputId);
    const textEl = document.getElementById(labelId);

    if (!fileInput || !textEl) return;

    // 點擊 dropzone → 開啟檔案選擇
    dropzone.addEventListener("click", () => {
      fileInput.click();
    });

    // 選擇完檔案後更新文字
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file) {
        textEl.textContent = `已選擇：${file.name}`;
        dropzone.classList.remove("error");
      } else {
        textEl.textContent = textEl.dataset.defaultText || "點擊或拖曳上傳檔案";
      }
    });

    // 拖曳上傳樣式處理（可選）
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
      if (file) {
        fileInput.files = e.dataTransfer.files;
        textEl.textContent = `已選擇：${file.name}`;
      }
    });
  });

  // 表單驗證（僅檢查公投案 PDF 是否有上傳）
  const form = document.querySelector(".submit-form");
  const proposalInput = document.getElementById("proposal_pdf");
  const proposalDropzone = proposalInput?.closest(".file-dropzone");
  const proposalLabel = document.getElementById("proposal_label");

  if (form && proposalInput && proposalDropzone && proposalLabel) {
    form.addEventListener("submit", (e) => {
      const file = proposalInput.files[0];
      if (!file) {
        e.preventDefault();
        proposalDropzone.classList.add("error");
        proposalLabel.textContent = "⚠ 請先選擇一個 PDF 檔案再提交";
        return;
      }

      proposalDropzone.classList.add("loading");
    });
  }
});
