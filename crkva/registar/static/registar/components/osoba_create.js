/* ==========================================================================
   OSOBA-CREATE — inline "+ Додај нову особу" footer for Osoba select2s
   ==========================================================================
   Adds a sticky create-new row at the bottom of any select2 dropdown whose
   underlying <select> carries `data-osoba-create`. Clicking it opens the
   shared #osoba-modal pre-filled by splitting the typed query on the first
   space (Име vs Презиме).

   If the source <select> carries `data-osoba-default-pol="М"` or
   `data-osoba-default-pol="Ж"` (gender-restricted lookups like majka /
   otac), the matching Pol toggle button inside `#modal-pol-toggle` is
   activated, so the user does not have to repeat what the field already
   implied.
   ========================================================================== */

(function ($) {
    "use strict";
    if (!$) return;

    function parseName(q) {
        var trimmed = (q || "").trim();
        if (!trimmed) return { ime: "", prezime: "" };
        var idx = trimmed.indexOf(" ");
        if (idx < 0) return { ime: trimmed, prezime: "" };
        return {
            ime: trimmed.slice(0, idx).trim(),
            prezime: trimmed.slice(idx + 1).trim(),
        };
    }

    function applyDefaultPol(defaultPol) {
        if (defaultPol !== "М" && defaultPol !== "Ж") return;
        var group = document.getElementById("modal-pol-toggle");
        if (!group) return;
        var buttons = group.querySelectorAll(".tab-group__item");
        var matched = null;
        buttons.forEach(function (btn) {
            btn.classList.remove("is-active");
            if (btn.dataset && btn.dataset.value === defaultPol) {
                matched = btn;
            }
        });
        if (matched) {
            // Trigger click so modal.js records the toggleState too.
            matched.click();
        }
    }

    function attach($select) {
        if ($select.data("osobaCreateBound")) return;
        $select.data("osobaCreateBound", true);

        $select.on("select2:open.osobaCreate", function () {
            requestAnimationFrame(function () {
                var $dropdown = $(".select2-container--open .select2-dropdown");
                if (!$dropdown.length) return;
                if ($dropdown.find(".select2-create-new").length) return;

                var $footer = $(
                    '<div class="select2-create-new" role="button" tabindex="0">' +
                        '<i class="fa-solid fa-plus" aria-hidden="true"></i> ' +
                        '<span class="select2-create-new__label"></span>' +
                    "</div>"
                );
                $dropdown.append($footer);

                var $search = $dropdown.find(".select2-search__field");

                function refresh() {
                    var q = ($search.val() || "").trim();
                    $footer.find(".select2-create-new__label").text(
                        q ? 'Додај "' + q + '"' : "Додај нову особу"
                    );
                }
                refresh();
                $search.on("input.osobaCreate", refresh);

                $footer.on("mousedown touchstart", function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var parts = parseName($search.val());
                    var defaultPol = $select.attr("data-osoba-default-pol") || "";
                    $select.select2("close");
                    if (!window.osobaModal || typeof window.osobaModal.open !== "function") return;
                    window.osobaModal.open($select.attr("id"));
                    setTimeout(function () {
                        var imeEl = document.getElementById("modal-ime");
                        var prezimeEl = document.getElementById("modal-prezime");
                        if (imeEl) imeEl.value = parts.ime;
                        if (prezimeEl) prezimeEl.value = parts.prezime;
                        applyDefaultPol(defaultPol);
                        var focusEl = parts.prezime ? prezimeEl : imeEl;
                        if (focusEl) {
                            focusEl.focus();
                            try { focusEl.setSelectionRange(focusEl.value.length, focusEl.value.length); } catch (e) {}
                        }
                    }, 60);
                });
            });
        });
    }

    function init() {
        $("select[data-osoba-create]").each(function () { attach($(this)); });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})(window.jQuery);
