document.addEventListener("DOMContentLoaded", () => {
  // 先抓 element，再決定是否 parse
  const remainingEl = document.getElementById("remaining");
  let maxSlots = 0;

  if (remainingEl) {
    maxSlots = parseInt(remainingEl.textContent);
    const checkboxes = document.querySelectorAll(
      'input[name="selected_members"]'
    );

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const checkedCount = document.querySelectorAll(
          'input[name="selected_members"]:checked'
        ).length;
        const remaining = maxSlots - checkedCount;

        remainingEl.textContent = remaining;

        // 若已達上限，disable 其他未勾選的 checkbox
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

    // 點擊 dropzone → 開啟檔案選擇
    dropzone.addEventListener("click", () => {
      console.log(`🖱️ Dropzone 點擊觸發！ inputId=${inputId}`);
      fileInput.value = "";
      fileInput.click();
    });

    // 選擇完檔案後更新文字
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      console.log("📂 檔案選擇觸發 change：", file);

      if (file) {
        textEl.textContent = `已選擇：${file.name}`;
        dropzone.classList.remove("error");
      } else {
        textEl.textContent = textEl.dataset.defaultText || "點擊或拖曳上傳檔案";
      }
    });

    // 拖曳上傳樣式處理
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

  // ✅ 表單驗證：只有 group 角色會用到
  const form = document.querySelector(".submit-form");
  const proposalInput = document.getElementById("proposal_pdf");
  const proposalDropzone = proposalInput?.closest(".file-dropzone");
  const proposalLabel = document.getElementById("proposal_label");

  console.log("🔍 找到 proposalInput:", proposalInput);
  console.log("🔍 找到 proposalLabel:", proposalLabel);
  console.log("🔍 找到 proposalDropzone:", proposalDropzone);

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

  const disabledForm = document.querySelector(".disabled-form");
  if (disabledForm) {
    disabledForm.querySelectorAll("input, textarea, select, button").forEach((el) => {
      el.setAttribute("disabled", "disabled");
      el.style.pointerEvents = "none";
      el.style.backgroundColor = "#f8f9fa";
      el.style.opacity = "0.6";
    });

    // 禁用 dropzone 行為
    document.querySelectorAll(".file-dropzone").forEach((zone) => {
      zone.style.pointerEvents = "none";
      zone.style.opacity = "0.6";
    });
  }
});
