/* ==========================================================================
   EDIT-TOGGLE — flip an info-page between view and edit mode in place
   ==========================================================================
   The detail templates render BOTH the static text spans and the form
   widgets for every editable row. A `data-mode` attribute on the page
   wrapper (set by the server: "view" or "edit") drives which is visible
   via the CSS in info.css.

   This script intercepts clicks on:
     - [data-action="enter-edit"]  : switch to edit mode (no page nav) and
                                     replace the URL with the link's href
     - [data-action="cancel-edit"] : reset the form (re-syncing select2 via
                                     a change event), revert to view mode and
                                     replace the URL with data-view-url
   On entering edit mode, select2 widgets that were initialised while hidden
   (width 0) are rebuilt so they render at the correct width, and focus moves
   to the first visible editable field for keyboard users.
   ========================================================================== */

(function () {
    const FIRST_EDITABLE =
        ".info-row--editable input:not([type=hidden]):not([disabled])," +
        " .info-row--editable select:not([disabled])," +
        " .info-row--editable textarea:not([disabled])";
    const SELECT2_WIDGETS =
        "select.django-select2, select[data-autocomplete-light-function], select.select2-hidden-accessible";

    function root() {
        return document.querySelector("[data-edit-toggle-root]");
    }

    function replaceUrl(url) {
        if (!url) return;
        if (new URL(url, window.location.href).origin !== window.location.origin) return;
        window.history.replaceState({}, "", url);
    }

    function reinitSelect2(node) {
        const $ = window.jQuery;
        if (!$?.fn?.select2) return;
        $(node).find(SELECT2_WIDGETS).each(function () {
            const $sel = $(this);
            if ($sel.data("select2")) $sel.select2("destroy");
        });
        if (typeof $.fn.djangoSelect2 === "function") {
            $(node).find("select.django-select2").djangoSelect2();
        } else {
            $(node).find("select.django-select2, select.select2-hidden-accessible").select2();
        }
    }

    function setMode(node, mode) {
        node.setAttribute("data-mode", mode);
        if (mode !== "edit") return;
        reinitSelect2(node);
        const first = node.querySelector(FIRST_EDITABLE);
        if (first) first.focus({ preventScroll: true });
    }

    function resetForm(node) {
        const form = node.querySelector("form") || (node.tagName === "FORM" ? node : null);
        if (!form) return;
        form.reset();
        if (window.jQuery) window.jQuery(form).find("select").trigger("change");
    }

    function onClick(e) {
        const node = root();
        if (!node) return;
        const action = e.target.closest("[data-action]");
        if (!action || !node.contains(action)) return;

        if (action.dataset.action === "enter-edit") {
            e.preventDefault();
            setMode(node, "edit");
            replaceUrl(action.getAttribute("href"));
        } else if (action.dataset.action === "cancel-edit") {
            e.preventDefault();
            resetForm(node);
            setMode(node, "view");
            replaceUrl(node.getAttribute("data-view-url") || window.location.pathname);
        }
    }

    function init() {
        if (!root()) return;
        document.addEventListener("click", onClick);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
