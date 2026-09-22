/**
 * College Laboratory Equipment Booking and Return Portal
 * Client-side JavaScript helpers
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Set minimum date for Due Date pickers to today's date
    const dueDateInputs = document.querySelectorAll('input[type="date"][name="due_date"]');
    const today = new Date().toISOString().split("T")[0];
    dueDateInputs.forEach(function (input) {
        if (!input.getAttribute("min")) {
            input.setAttribute("min", today);
        }
    });

    // 3. Client-side Live Search & Category Filtering for Equipment Grid
    const searchInput = document.getElementById("equipmentSearchInput");
    const categoryFilter = document.getElementById("equipmentCategorySelect");
    const equipmentCards = document.querySelectorAll(".equipment-card-item");

    function filterEquipment() {
        if (!equipmentCards.length) return;

        const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : "";
        const selectedCategory = categoryFilter ? categoryFilter.value : "All";
        let visibleCount = 0;

        equipmentCards.forEach(function (card) {
            const name = card.getAttribute("data-name") || "";
            const category = card.getAttribute("data-category") || "";
            const description = card.getAttribute("data-description") || "";

            const matchesSearch = !searchTerm ||
                name.includes(searchTerm) ||
                description.includes(searchTerm) ||
                category.includes(searchTerm);

            const matchesCategory = selectedCategory === "All" || category === selectedCategory;

            if (matchesSearch && matchesCategory) {
                card.style.display = "";
                visibleCount++;
            } else {
                card.style.display = "none";
            }
        });

        // Show "no results" message if needed
        const noResultsEl = document.getElementById("noEquipmentMessage");
        if (noResultsEl) {
            noResultsEl.style.display = visibleCount === 0 ? "block" : "none";
        }
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterEquipment);
    }
    if (categoryFilter) {
        categoryFilter.addEventListener("change", filterEquipment);
    }

    // 4. Quantity Input Constraint Enforcement
    const qtyInput = document.getElementById("bookingQuantityInput");
    if (qtyInput) {
        qtyInput.addEventListener("input", function () {
            const max = parseInt(this.getAttribute("max"), 10);
            const min = parseInt(this.getAttribute("min"), 10) || 1;
            let val = parseInt(this.value, 10);

            if (val > max) {
                this.value = max;
            } else if (val < min && this.value !== "") {
                this.value = min;
            }
        });
    }
});

/**
 * Confirm item deletion before submitting form
 */
function confirmDelete(equipmentName) {
    return confirm(`Are you sure you want to delete "${equipmentName}"? This action cannot be undone.`);
}

/**
 * Confirm equipment return
 */
function confirmReturn(equipmentName) {
    return confirm(`Confirm return of "${equipmentName}" to the laboratory?`);
}
