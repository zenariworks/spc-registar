/* ==========================================================================
   OSOBA-CREATE — inline "+ Додај нову особу" footer for Osoba select2s
   ==========================================================================
   Adds a sticky create-new row (select2_create_footer.js) at the bottom of
   any select2 dropdown whose underlying <select> carries
   `data-osoba-create`. Clicking it opens the shared #osoba-modal pre-filled
   by splitting the typed query on the first space (Име vs Презиме).

   If the source <select> carries `data-osoba-default-pol="М"` or
   `data-osoba-default-pol="Ж"` (gender-restricted lookups like majka /
   otac), the matching Pol toggle button inside `#modal-pol-toggle` is
   activated, so the user does not have to repeat what the field already
   implied. `data-osoba-parohijan-default` (default "1") does the same for
   `#modal-parohijan-toggle`. Toggles are activated with a real click so
   modal.js records the toggle state too.
   ========================================================================== */

(function ($) {
    const footer = window.Select2CreateFooter;
    if (!$ || !footer) return;

    const POL_VALUES = ["М", "Ж"];

    function parseName(q) {
        if (!q) return { ime: "", prezime: "" };
        const idx = q.indexOf(" ");
        if (idx < 0) return { ime: q, prezime: "" };
        return {
            ime: q.slice(0, idx).trim(),
            prezime: q.slice(idx + 1).trim(),
        };
    }

    function activateToggle(groupId, value) {
        const group = document.getElementById(groupId);
        if (!group) return;
        let matched = null;
        group.querySelectorAll(".tab-group__item").forEach(function (btn) {
            btn.classList.remove("is-active");
            if (btn.dataset.value === value) {
                matched = btn;
            }
        });
        if (matched) {
            matched.click();
        }
    }

    function prefillModal(parts, defaultPol, defaultParohijan) {
        const imeEl = document.querySelector("#osoba-modal #modal-ime");
        const prezimeEl = document.querySelector("#osoba-modal #modal-prezime");
        if (imeEl) imeEl.value = parts.ime;
        if (prezimeEl) prezimeEl.value = parts.prezime;
        if (POL_VALUES.includes(defaultPol)) {
            activateToggle("modal-pol-toggle", defaultPol);
        }
        activateToggle("modal-parohijan-toggle", defaultParohijan);
        const focusEl = parts.prezime ? prezimeEl : imeEl;
        if (focusEl) footer.focusAtEnd(focusEl);
    }

    function openModal($select, query) {
        if (!window.osobaModal || typeof window.osobaModal.open !== "function") return;
        const parts = parseName(query);
        const defaultPol = $select.attr("data-osoba-default-pol") || "";
        const defaultParohijan = $select.attr("data-osoba-parohijan-default") || "1";
        window.osobaModal.open($select.attr("id"));
        setTimeout(function () {
            prefillModal(parts, defaultPol, defaultParohijan);
        }, 60);
    }

    footer.onReady(function () {
        $("select[data-osoba-create]").each(function () {
            const $select = $(this);
            footer.attach($select, {
                namespace: "osobaCreate",
                label: "Додај нову особу",
                onCreate: function (query) {
                    openModal($select, query);
                },
            });
        });
    });
})(window.jQuery);
