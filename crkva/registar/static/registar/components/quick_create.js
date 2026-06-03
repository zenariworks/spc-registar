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
    "use strict";
    if (!$) return;

    function attach($select) {
        if ($select.data("quickCreateBound")) return;
        $select.data("quickCreateBound", true);

        var modalId = $select.attr("data-create-modal");
        var label = $select.attr("data-create-label") || "Додај ново";

        $select.on("select2:open.quickCreate", function () {
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
                        q ? 'Додај "' + q + '"' : label
                    );
                }
                refresh();
                $search.on("input.quickCreate", refresh);

                $footer.on("mousedown touchstart", function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var q = ($search.val() || "").trim();
                    $select.select2("close");
                    var inst = window.quickModals && window.quickModals[modalId];
                    if (!inst || typeof inst.open !== "function") return;
                    inst.open($select.attr("id"));
                    // Prefill the modal's first text input with the typed query.
                    setTimeout(function () {
                        var overlay = document.getElementById(modalId);
                        var first = overlay && overlay.querySelector("input[type=text]");
                        if (first && q) {
                            first.value = q;
                            first.focus();
                            try { first.setSelectionRange(q.length, q.length); } catch (e) {}
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
