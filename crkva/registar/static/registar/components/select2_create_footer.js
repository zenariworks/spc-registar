/* ==========================================================================
   SELECT2-CREATE-FOOTER — shared "+ Додај …" row for select2 dropdowns
   ==========================================================================
   Used by osoba_create.js and quick_create.js. Exposes
   window.Select2CreateFooter:

     attach($select, { namespace, label, onCreate })
       Appends a sticky create-new row to the open dropdown of $select.
       The row reads 'Додај "<query>"' while the user types, `label` when
       the search is empty. On click it closes select2 and calls
       onCreate(query) with the trimmed search text. `namespace` scopes the
       jQuery events and the "<namespace>Bound" guard against double binding.

     focusAtEnd(el)
       Focuses an input and puts the caret after its value. Inputs whose
       type has no text selection (email, number…) are only focused.

     onReady(fn)
       Runs fn once the DOM is parsed (immediately if it already is).
   ========================================================================== */

(function ($) {
    if (!$) return;

    const SELECTABLE_TYPES = ["text", "search", "tel", "url", "password", "textarea"];

    function focusAtEnd(el) {
        el.focus();
        if (SELECTABLE_TYPES.includes(el.type)) {
            el.setSelectionRange(el.value.length, el.value.length);
        }
    }

    function onReady(fn) {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", fn);
        } else {
            fn();
        }
    }

    function buildFooter() {
        return $(
            '<div class="select2-create-new" role="button" tabindex="0">' +
                '<i class="fa-solid fa-plus" aria-hidden="true"></i> ' +
                '<span class="select2-create-new__label"></span>' +
            "</div>"
        );
    }

    function appendFooter($select, opts) {
        const $dropdown = $(".select2-container--open .select2-dropdown");
        if (!$dropdown.length) return;
        if ($dropdown.find(".select2-create-new").length) return;

        const $footer = buildFooter();
        $dropdown.append($footer);

        const $search = $dropdown.find(".select2-search__field");
        const query = function () {
            return ($search.val() || "").trim();
        };

        function refresh() {
            const q = query();
            $footer.find(".select2-create-new__label").text(
                q ? 'Додај "' + q + '"' : opts.label
            );
        }
        refresh();
        $search.on("input." + opts.namespace, refresh);

        $footer.on("mousedown touchstart", function (e) {
            e.preventDefault();
            e.stopPropagation();
            const q = query();
            $select.select2("close");
            opts.onCreate(q);
        });
    }

    function attach($select, opts) {
        const boundKey = opts.namespace + "Bound";
        if ($select.data(boundKey)) return;
        $select.data(boundKey, true);

        $select.on("select2:open." + opts.namespace, function () {
            requestAnimationFrame(function () {
                appendFooter($select, opts);
            });
        });
    }

    window.Select2CreateFooter = { attach, focusAtEnd, onReady };
})(window.jQuery);
