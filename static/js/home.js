document.addEventListener("DOMContentLoaded", () => {
    initSearch();
    initTooltips();
    initRowClick();
    initActionButtons();
});

function initSearch() {
    const input = document.getElementById("searchInput");

    if (!input) return;

    const rows = document.querySelectorAll("#kajianTable tbody tr");
    const counter = document.getElementById("jumlahKajian");
    const emptyState = document.getElementById("searchEmptyState");
    const keywordText = document.getElementById("searchKeyword");
    const tableContainer = document.getElementById("tableContainer");

    function filterKajian() {
        const keyword = input.value.toLowerCase().trim();

        let visible = 0;

        rows.forEach((row) => {
            const match = row.dataset.search.includes(keyword);

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
}

function initTooltips() {
    document.querySelectorAll(".text-clamp").forEach((el) => {
        const isTruncated =
            el.scrollHeight > el.clientHeight ||
            el.scrollWidth > el.clientWidth;

        if (!isTruncated) {
            el.removeAttribute("title");
            el.removeAttribute("data-bs-toggle");
            return;
        }

        new bootstrap.Tooltip(el);
    });
}

function initRowClick() {
    document.querySelectorAll(".kajian-row").forEach((row) => {
        row.addEventListener("click", () => {
            window.location.href = row.dataset.href;
        });
    });
}

function initActionButtons() {

    document.querySelectorAll(".btn-aksi").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    });

    document.querySelectorAll(".form-hapus").forEach((form) => {

        form.addEventListener("click", (e) => {
            e.stopPropagation();
        });

        form.addEventListener("submit", (e) => {

            const confirmed = confirm(
                "Hapus kajian beserta seluruh dokumennya?"
            );

            if (!confirmed) {
                e.preventDefault();
            }

        });

    });

}
