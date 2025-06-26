document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".auth-form");
    const roleSelect = document.getElementById("role");
    const affFields = document.getElementById("affiliation-fields");
    const affSelect = document.getElementById("affiliation_id");
    const affTypeInput = document.getElementById("affiliation_type");

    function showFormError(message) {
        const errorBox = document.getElementById("form-error");
        if (!errorBox) return;
        errorBox.textContent = message;
        errorBox.style.display = "block";
        errorBox.classList.remove("hidden");
    }

    function clearFormError() {
        const errorBox = document.getElementById("form-error");
        if (!errorBox || errorBox.style.display === "none") return;

        //Add fade animation
        errorBox.classList.add("hidden");

        //Wait for the animation to truly hide
        setTimeout(() => {
            errorBox.style.display = "none";
            errorBox.classList.remove("hidden");
            errorBox.textContent = "";
        }, 300); //The time should be consistent with the transition of CSS
    }

    //Initialize: Show/hide affiliation fields based on the selected role
    function toggleAffiliationFields() {
        if (roleSelect.value === "member") {
            affFields.style.display = "block";
        } else {
            affFields.style.display = "none";
            //Clear values if not member
            affSelect.value = "";
            affTypeInput.value = "";
        }
    }

    toggleAffiliationFields(); //Initialize on page load

    //Change event: Update affiliation field visibility
    roleSelect.addEventListener("change", toggleAffiliationFields);

    //Change event: Update affiliation_type based on selected option
    affSelect.addEventListener("change", function () {
        const selected = this.options[this.selectedIndex];
        const type = selected.getAttribute("data-type");
        affTypeInput.value = type || "";
    });

    const passwordInput = document.getElementById("password");
    const passwordHint = document.getElementById("password-strength");

    function evaluatePasswordStrength(password) {
        if (password.length < 8) return "weak";

        const hasLower = /[a-z]/.test(password);
        const hasUpper = /[A-Z]/.test(password);
        const hasDigit = /[0-9]/.test(password);
        const hasSymbol = /[!@#$%^&*()_+{}\[\]:;"'<>?,./\\|-]/.test(password);

        const score = [hasLower, hasUpper, hasDigit, hasSymbol].filter(
            Boolean
        ).length;

        if (score <= 2) return "weak";
        if (score === 3) return "medium";
        return "strong";
    }

    if (passwordInput && passwordHint) {
        passwordInput.addEventListener("input", () => {
            const pwd = passwordInput.value;
            const level = evaluatePasswordStrength(pwd);

            passwordHint.textContent = pwd
                ? `密碼強度：${level === "weak" ? "弱" : level === "medium" ? "中" : "強"
                }`
                : "密碼強度：尚未輸入";

            passwordHint.className = `password-hint ${level}`;
        });
    }

    //Form validation before submission
    if (form) {
        form.addEventListener("submit", (e) => {
            const username = document.getElementById("username").value.trim();
            const fullname = document.getElementById("fullname").value.trim();
            const password = document.getElementById("password").value.trim();
            const role = roleSelect.value.trim();
            const strongPasswordRegex =
                /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+{}\[\]:;"'<>?,./\\|-]).{8,}$/;

            //Basic fields check
            if (!username || !fullname || !password || !role) {
                showFormError("請完整填寫所有欄位");
                e.preventDefault();
                return;
            }

            if (!strongPasswordRegex.test(password)) {
                showFormError("密碼需至少 8 字，且包含大小寫英文字母、數字與特殊符號");
                e.preventDefault();
                return;
            }

            //Additional check for member: must select affiliation
            if (role === "member") {
                const affType = affTypeInput.value.trim();
                const affId = affSelect.value.trim();

                if (!affType || !affId) {
                    showFormError("請選擇所屬政黨或利益團體");
                    e.preventDefault();
                    return;
                }
            }
        });
    }

    ["username", "fullname", "password", "affiliation_id"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", clearFormError);
    });

    roleSelect.addEventListener("change", clearFormError);
    affSelect.addEventListener("change", clearFormError);
});
