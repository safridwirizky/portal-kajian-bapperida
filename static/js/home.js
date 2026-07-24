document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("searchInput");

    if (!input) return;

    const rows = document.querySelectorAll("#kajianTable tbody tr");
    const counter = document.getElementById("jumlahKajian");
    const emptyState = document.getElementById("searchEmptyState");
    const keywordText = document.getElementById("searchKeyword");
    const tableContainer = document.getElementById("tableContainer");

    function filterKajian() {

        const keyword = input.value
            .toLowerCase()
            .trim();

        let visible = 0;

        rows.forEach(row => {

            const text = row.dataset.search;

            const match = text.includes(keyword);

            row.style.display = match ? "" : "none";

            if (match) visible++;

        });

        counter.textContent = `Menampilkan ${visible} kajian`;

        if (visible === 0 && keyword !== "") {

            tableContainer.classList.add("d-none");
            emptyState.classList.remove("d-none");
            keywordText.textContent = `"${input.value}"`;

        } else {

            tableContainer.classList.remove("d-none");
            emptyState.classList.add("d-none");

        }

    }

    let timeout;

    input.addEventListener("input", () => {

        clearTimeout(timeout);
        timeout = setTimeout(filterKajian, 150);

    });

});

document.addEventListener("DOMContentLoaded", () => {
    document
        .querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(el => new bootstrap.Tooltip(el));
});
