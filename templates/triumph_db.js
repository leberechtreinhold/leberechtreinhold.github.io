(() => {
    const table = document.getElementById("army-table");
    const languageToggle = document.getElementById("language-toggle");
    const languageMenu = document.getElementById("language-menu");
    const languageCurrentFlag = document.getElementById("language-current-flag");
    const languageCurrentLabel = document.getElementById("language-current-label");
    const languageOptions = Array.from(document.querySelectorAll(".lang-option"));

    const tbody = table ? table.querySelector("tbody") : null;
    const headers = table
        ? Array.from(table.querySelectorAll("thead th.sortable"))
        : [];
    let currentSort = { col: 1, dir: "asc" };

    function applyLanguage(language) {
        const elements = document.querySelectorAll("[data-lang-en][data-lang-es]");
        elements.forEach((element) => {
            const value =
                language === "es"
                    ? element.dataset.langEs || ""
                    : element.dataset.langEn || "";

            const link = element.querySelector("a");
            if (link) {
                link.textContent = value;
            } else {
                element.textContent = value;
            }

            if (element.dataset.sortValue !== undefined) {
                element.dataset.sortValue = value.trim().toLowerCase();
            }
        });
    }

    function setActiveLanguage(language) {
        languageOptions.forEach((option) => {
            const isActive = option.dataset.lang === language;
            option.setAttribute("aria-selected", isActive ? "true" : "false");

            if (isActive && languageCurrentFlag && languageCurrentLabel) {
                languageCurrentFlag.src = option.dataset.flag || "";
                languageCurrentLabel.textContent = option.dataset.label || "";
            }
        });
    }

    function toggleLanguageMenu(forceOpen) {
        if (!languageMenu || !languageToggle) return;
        const shouldOpen =
            typeof forceOpen === "boolean"
                ? forceOpen
                : !languageMenu.classList.contains("is-open");
        languageMenu.classList.toggle("is-open", shouldOpen);
        languageToggle.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
    }

    function valueFor(row, col, type) {
        const cell = row.cells[col];
        const raw = (cell.dataset.sortValue || "").trim();

        if (type === "number") {
            if (raw === "") return Number.POSITIVE_INFINITY;
            const num = Number(raw);
            return Number.isNaN(num) ? Number.POSITIVE_INFINITY : num;
        }

        return raw.toLowerCase();
    }

    function updateIndicators() {
        headers.forEach((header) => {
            const indicator = header.querySelector(".sort-indicator");
            const col = Number(header.dataset.col);
            if (!indicator) return;

            if (col === currentSort.col) {
                indicator.textContent = currentSort.dir === "asc" ? "↑" : "↓";
            } else {
                indicator.textContent = "";
            }
        });
    }

    function sortBy(col, type, dir) {
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((a, b) => {
            const va = valueFor(a, col, type);
            const vb = valueFor(b, col, type);

            if (type === "number") {
                return dir === "asc" ? va - vb : vb - va;
            }

            return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
        });

        rows.forEach((row) => tbody.appendChild(row));
        currentSort = { col, dir };
        updateIndicators();
    }

    headers.forEach((header) => {
        header.addEventListener("click", () => {
            const col = Number(header.dataset.col);
            const type = header.dataset.type || "text";
            const dir =
                currentSort.col === col && currentSort.dir === "asc"
                    ? "desc"
                    : "asc";
            sortBy(col, type, dir);
        });
    });

    if (languageToggle) {
        languageToggle.addEventListener("click", () => {
            toggleLanguageMenu();
        });
    }

    languageOptions.forEach((option) => {
        option.addEventListener("click", () => {
            const language = option.dataset.lang || "en";
            setActiveLanguage(language);
            applyLanguage(language);
            toggleLanguageMenu(false);
        });
    });

    document.addEventListener("click", (event) => {
        const switcher = event.target.closest(".language-buttons");
        if (!switcher) {
            toggleLanguageMenu(false);
        }
    });

    if (table && tbody && headers.length > 0) {
        sortBy(1, "number", "asc");
    }
    setActiveLanguage("en");
    applyLanguage("en");
})();
