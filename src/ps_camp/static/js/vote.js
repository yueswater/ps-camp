document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".party-card").forEach(card => {
        card.addEventListener("click", () => {
            const input = card.querySelector("input[type=radio]");
            input.checked = true;
        });
    });
});
