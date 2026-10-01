/* ==========================================================================
   QUICK-CREATE — generic "+ Додај ново" footer for select2 widgets
   ==========================================================================
   Attaches a create-new row (select2_create_footer.js) to any select2 whose
   underlying <select> carries `data-create-modal="<modalId>"` (and optional
   `data-create-label`). The named modal must be bound via Modal.bindForm
   and registered in window.quickModals[<modalId>] (see _modal_hram.html /
   _modal_adresa_create).

   Model-agnostic counterpart of osoba_create.js: on click it opens the
   modal targeting the originating <select>, so Modal's default onSuccess
   appends the freshly-created {id,text} option and selects it. The typed
   query pre-fills the modal's first text input.
   ========================================================================== */

(function ($) {
    const footer = window.Select2CreateFooter;
    if (!$ || !footer) return;

    function prefillFirstInput(modalId, query) {
        if (!query) return;
        const overlay = document.getElementById(modalId);
        const first = overlay?.querySelector("input[type=text]");
        if (!first) return;
        first.value = query;
        footer.focusAtEnd(first);
    }

    function openModal($select, modalId, query) {
        const inst = window.quickModals?.[modalId];
        if (!inst || typeof inst.open !== "function") return;
        inst.open($select.attr("id"));
        setTimeout(function () {
            prefillFirstInput(modalId, query);
        }, 60);
    }

    footer.onReady(function () {
        $("select[data-create-modal]").each(function () {
            const $select = $(this);
            const modalId = $select.attr("data-create-modal");
            footer.attach($select, {
                namespace: "quickCreate",
                label: $select.attr("data-create-label") || "Додај ново",
                onCreate: function (query) {
                    openModal($select, modalId, query);
                },
            });
        });
    });
})(window.jQuery);
