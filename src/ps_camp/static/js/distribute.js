// distribute.js
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  const amountInput = document.getElementById("amount");

  form.addEventListener("submit", function (e) {
    const amount = parseInt(amountInput.value);
    if (isNaN(amount) || amount <= 0) {
      e.preventDefault();
      alert("請輸入有效的金額！");
    }
  });
});
