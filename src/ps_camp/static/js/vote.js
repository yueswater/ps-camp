document.addEventListener("DOMContentLoaded", () => {
  const partyCards = document.querySelectorAll(".party-box");

  // 動態處理政黨名稱換行（超過 7 字）
  document.querySelectorAll(".ballot-name-vertical").forEach((el) => {
    const name = el.dataset.name || "";
    if (name.length > 7) {
      const midpoint = Math.ceil(name.length / 2);
      el.innerHTML = name
        .split("")
        .map((char, i) => (i === midpoint ? "<br>" + char : char))
        .join("");
    } else {
      el.textContent = name;
    }
  });

  document.querySelectorAll(".ref-option").forEach((option) => {
    option.addEventListener("click", () => {
      const parent = option.closest(".referendum-options");
      const allOptions = parent.querySelectorAll(".ref-option");
      const input = option.querySelector("input");

      // 清除選取樣式
      allOptions.forEach((o) => o.classList.remove("selected"));
      option.classList.add("selected");

      // 勾選 radio
      if (input) input.checked = true;
    });
  });

  partyCards.forEach((card) => {
    card.addEventListener("click", () => {
      // 勾選 radio
      const input = card.querySelector("input[type=radio]");
      input.checked = true;

      // 清除所有卡片的 selected 樣式與動畫
      partyCards.forEach((c) => {
        c.classList.remove("selected");
        const stamp = c.querySelector(".stamp");
        if (stamp) {
          stamp.style.animation = "none";
          stamp.style.transform = "scale(0.3)";
          stamp.style.opacity = "0";
          stamp.style.top = "0";
          stamp.style.left = "0";
          stamp.offsetHeight; // force reflow
        }
      });

      // 隨機位置與角度（在 stamp-area 中）
      const stampArea = card.querySelector(".stamp-area");
      const stamp = card.querySelector(".stamp");

      if (stamp && stampArea) {
        const areaWidth = stampArea.clientWidth;
        const areaHeight = stampArea.clientHeight;

        const stampSize = 40; // stamp 寬高，與 CSS 對齊
        const maxTop = areaHeight - stampSize;
        const maxLeft = areaWidth - stampSize;

        const randTop = Math.floor(Math.random() * maxTop);
        const randLeft = Math.floor(Math.random() * maxLeft);
        const randRotate = Math.floor(Math.random() * 20) - 10;

        stamp.style.top = `${randTop}px`;
        stamp.style.left = `${randLeft}px`;
        stamp.style.transform = `scale(0.3) rotate(${randRotate}deg)`;
      }

      // 延遲觸發動畫與蓋章
      setTimeout(() => {
        if (stamp) {
          stamp.style.animation = "stampIn 0.4s ease forwards";
          stamp.style.animationDelay = "0.5s";
        }
        card.classList.add("selected");
      }, 50);
    });
  });
});
