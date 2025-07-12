document.addEventListener("DOMContentLoaded", () => {
  // 名額限制處理
  const remainingEl = document.getElementById("remaining");
  let maxSlots = 0;

  if (remainingEl) {
    maxSlots = parseInt(remainingEl.textContent);
    const checkboxes = document.querySelectorAll('input[name="selected_members"]');

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const checkedCount = document.querySelectorAll('input[name="selected_members"]:checked').length;
        const remaining = maxSlots - checkedCount;
        remainingEl.textContent = remaining;

        checkboxes.forEach((cb) => {
          if (!cb.checked) {
            cb.disabled = remaining <= 0;
          }
        });
      });
    });
  }

  // Dropzone 行為處理
  const dropzones = document.querySelectorAll(".file-dropzone");

  dropzones.forEach((dropzone) => {
    const inputId = dropzone.dataset.inputId;
    const labelId = dropzone.dataset.labelId;
    const fileInput = document.getElementById(inputId);
    const textEl = document.getElementById(labelId);

    if (!fileInput || !textEl) return;

    dropzone.addEventListener("click", () => {
      fileInput.value = "";
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file) {
        textEl.textContent = `已選擇：${file.name}`;
        dropzone.classList.remove("error");
      } else {
        textEl.textContent = textEl.dataset.defaultText || "點擊或拖曳上傳檔案";
      }
    });

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

  // group 專用公投表單驗證
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
        proposalLabel.textContent = "請先選擇一個 PDF 檔案再提交";
        return;
      }

      proposalDropzone.classList.add("loading");
    });
  }

  // 禁用 .disabled-form 區塊內所有互動元件
  document.querySelectorAll(".disabled-form").forEach((formEl) => {
    formEl.querySelectorAll("input, textarea, select, button").forEach((el) => {
      el.setAttribute("disabled", "disabled");
      el.style.pointerEvents = "none";
      el.style.backgroundColor = "#f8f9fa";
      el.style.opacity = "0.6";
    });

    formEl.querySelectorAll(".file-dropzone").forEach((zone) => {
      zone.style.pointerEvents = "none";
      zone.style.opacity = "0.6";
    });
  });
});
