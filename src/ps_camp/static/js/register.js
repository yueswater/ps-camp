document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".auth-form");
    const roleSelect = document.getElementById("role");
    const affFields = document.getElementById("affiliation-fields");
    const affSelect = document.getElementById("affiliation_id");
    const affTypeInput = document.getElementById("affiliation_type");

    // Initialize: Show/hide affiliation fields based on the selected role
    function toggleAffiliationFields() {
        if (roleSelect.value === "member") {
            affFields.style.display = "block";
        } else {
            affFields.style.display = "none";
            // Clear values if not member
            affSelect.value = "";
            affTypeInput.value = "";
        }
    }

    toggleAffiliationFields(); // Initialize on page load

    // Change event: Update affiliation field visibility
    roleSelect.addEventListener("change", toggleAffiliationFields);

    // Change event: Update affiliation_type based on selected option
    affSelect.addEventListener("change", function () {
        const selected = this.options[this.selectedIndex];
        const type = selected.getAttribute("data-type");
        affTypeInput.value = type || "";
    });

    // Form validation before submission
    if (form) {
        form.addEventListener("submit", (e) => {
            const username = document.getElementById("username").value.trim();
            const fullname = document.getElementById("fullname").value.trim();
            const password = document.getElementById("password").value.trim();
            const role = roleSelect.value.trim();

            // Basic fields check
            if (!username || !fullname || !password || !role) {
                alert("請完整填寫所有欄位");
                e.preventDefault();
                return;
            }

            // Additional check for member: must select affiliation
            if (role === "member") {
                const affType = affTypeInput.value.trim();
                const affId = affSelect.value.trim();

                if (!affType || !affId) {
                    alert("請選擇所屬政黨或利益團體");
                    e.preventDefault();
                    return;
                }
            }
        });
    }
});
