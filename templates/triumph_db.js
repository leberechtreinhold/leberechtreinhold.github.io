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
    let currentLang = "en";

    function applyLanguage(language) {
        currentLang = language;
        document.body.dataset.lang = language;
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

            if (element.dataset.sortValue !== undefined && element.dataset.ignoreLangForSort === undefined) {
                element.dataset.sortValue = value.trim().toLowerCase();
            }
        });
        if (typeof renderDropdown === "function" && armySearch && armySearch.value.trim()) {
            renderDropdown(armySearch.value);
        }
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

    function isArmyNumber(value) {
        // A value is an "Army number" if it's a bunch of digits followed by a letter, without spaces (e.g. "123a")
        // The number can also be a float, so it may contain a dot (e.g. "123.5a")
        return /^\d+(\.\d+)?[a-zA-Z]$/.test(value);
    }

    function compareArmyNumbers(a, b, dir) {
        const numA = parseFloat(a.match(/^(\d+(\.\d+)?)/)[1]);
        const numB = parseFloat(b.match(/^(\d+(\.\d+)?)/)[1]);

        if (numA !== numB) {
            return dir === "asc" ? numA - numB : numB - numA;
        }
        const letterA = a.match(/[a-zA-Z]$/)[0];
        const letterB = b.match(/[a-zA-Z]$/)[0];
        return dir === "asc" ? letterA.localeCompare(letterB) : letterB.localeCompare(letterA);
    }

    function sortBy(col, type, dir) {
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((a, b) => {
            const va = valueFor(a, col, type);
            const vb = valueFor(b, col, type);

            if (type === "number") {
                return dir === "asc" ? va - vb : vb - va;
            } else if (isArmyNumber(va) && isArmyNumber(vb)) {
                return compareArmyNumbers(va, vb, dir);
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

    const armySearch = document.getElementById("army-search");
    const armyDropdown = document.getElementById("army-search-dropdown");
    const ARMY_NAMES = {{ army_names | tojson }};
    let activeIndex = -1;

    if (table && tbody && headers.length > 0) {
        sortBy(1, "number", "asc");
    }
    setActiveLanguage("en");
    applyLanguage("en");

    function getArmyLabel(army) {
        return (currentLang === "es" && army.es) ? army.es : army.en;
    }

    function renderDropdown(query) {
        if (!armySearch || !armyDropdown) return;
        const q = query.trim().toLowerCase();
        if (!q) {
            closeDropdown();
            return;
        }
        const matches = ARMY_NAMES.filter((a) =>
            getArmyLabel(a).toLowerCase().includes(q)
        ).slice(0, 10);

        if (matches.length === 0) {
            closeDropdown();
            return;
        }

        activeIndex = -1;
        armyDropdown.innerHTML = "";
        matches.forEach((army, i) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "army-search-option";
            btn.textContent = getArmyLabel(army);
            btn.dataset.armyId = army.id;
            btn.addEventListener("mousedown", (e) => {
                e.preventDefault();
                window.location.href = "/army/" + army.id;
            });
            armyDropdown.appendChild(btn);
        });
        armyDropdown.classList.add("is-open");
    }

    function closeDropdown() {
        if (armyDropdown) {
            armyDropdown.classList.remove("is-open");
            armyDropdown.innerHTML = "";
        }
        activeIndex = -1;
    }

    function setActive(index) {
        const options = armyDropdown ? Array.from(armyDropdown.querySelectorAll(".army-search-option")) : [];
        options.forEach((opt, i) => opt.classList.toggle("is-active", i === index));
        activeIndex = index;
    }

    if (armySearch) {
        armySearch.addEventListener("input", () => renderDropdown(armySearch.value));

        armySearch.addEventListener("keydown", (e) => {
            const options = armyDropdown ? Array.from(armyDropdown.querySelectorAll(".army-search-option")) : [];
            if (e.key === "ArrowDown") {
                e.preventDefault();
                setActive(Math.min(activeIndex + 1, options.length - 1));
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActive(Math.max(activeIndex - 1, 0));
            } else if (e.key === "Enter" && activeIndex >= 0 && options[activeIndex]) {
                e.preventDefault();
                window.location.href = "/army/" + options[activeIndex].dataset.armyId;
            } else if (e.key === "Escape") {
                closeDropdown();
            }
        });

        armySearch.addEventListener("blur", () => setTimeout(closeDropdown, 150));
    }
})();
