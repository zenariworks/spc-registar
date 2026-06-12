/* ==========================================================================
   QUICK-CREATE — generic "+ Додај ново" footer for select2 widgets
   ==========================================================================
   Attaches a create-new row to any select2 whose underlying <select> carries
   `data-create-modal="<modalId>"` (and optional `data-create-label`). The
   named modal must be bound via Modal.bindForm and registered in
   window.quickModals[<modalId>] (see _modal_hram.html / _modal_adresa_create).

   Mirrors osoba_create.js, but model-agnostic: on click it just opens the
   modal targeting the originating <select>, so Modal's default onSuccess
   appends the freshly-created {id,text} option and selects it.
   ========================================================================== */
(function ($) {
    if (!$) return;

    function attach($select) {
        if ($select.data("quickCreateBound")) return;
        $select.data("quickCreateBound", true);

        const modalId = $select.attr("data-create-modal");
        const label = $select.attr("data-create-label") || "Додај ново";

        $select.on("select2:open.quickCreate", function () {
            requestAnimationFrame(function () {
                const $dropdown = $(".select2-container--open .select2-dropdown");
                if (!$dropdown.length) return;
                if ($dropdown.find(".select2-create-new").length) return;

                const $footer = $(
                    '<div class="select2-create-new" role="button" tabindex="0">' +
                        '<i class="fa-solid fa-plus" aria-hidden="true"></i> ' +
                        '<span class="select2-create-new__label"></span>' +
                    "</div>"
                );
                $dropdown.append($footer);

                const $search = $dropdown.find(".select2-search__field");

                function refresh() {
                    const q = ($search.val() || "").trim();
                    $footer.find(".select2-create-new__label").text(
                        q ? 'Додај "' + q + '"' : label
                    );
                }
                refresh();
                $search.on("input.quickCreate", refresh);

                $footer.on("mousedown touchstart", function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const q = ($search.val() || "").trim();
                    $select.select2("close");
                    const inst = window.quickModals?.[modalId];
                    if (!inst || typeof inst.open !== "function") return;
                    inst.open($select.attr("id"));
                    // Prefill the modal's first text input with the typed query.
                    setTimeout(function () {
                        const overlay = document.getElementById(modalId);
                        const first = overlay?.querySelector("input[type=text]");
                        if (first && q) {
                            first.value = q;
                            first.focus();
                            try { first.setSelectionRange(q.length, q.length); } catch (_e) {}
                        }
                    }, 60);
                });
            });
        });
    }

    function init() {
        $("select[data-create-modal]").each(function () { attach($(this)); });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})(window.jQuery);
