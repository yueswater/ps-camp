document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  form.addEventListener("submit", () => {
    form.classList.add("is-submitting");
  });
});
