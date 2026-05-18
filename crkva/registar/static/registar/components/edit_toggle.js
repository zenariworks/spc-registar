/* ==========================================================================
   EDIT-TOGGLE — flip an info-page between view and edit mode in place
   ==========================================================================
   The detail templates render BOTH the static text spans and the form
   widgets for every editable row. A `data-mode` attribute on the page
   wrapper (set by the server: "view" or "edit") drives which is visible
   via the CSS in info.css.

   This script intercepts clicks on:
     - [data-action="enter-edit"]  : switch to edit mode (no page nav)
     - [data-action="cancel-edit"] : revert to view mode, reset form
   It also reinitializes select2 widgets that were hidden when the page
   loaded so they render at the correct width once revealed.
   ========================================================================== */

(function () {
    "use strict";

    function root() {
        return document.querySelector("[data-edit-toggle-root]");
    }

    function setMode(node, mode) {
        if (!node) return;
        node.setAttribute("data-mode", mode);
        if (mode === "edit") {
            reinitSelect2(node);
            // Hand focus to the first visible input for keyboard users.
            var first = node.querySelector(
                ".info-row--editable input:not([type=hidden]):not([disabled]),"
                + " .info-row--editable select:not([disabled]),"
                + " .info-row--editable textarea:not([disabled])"
            );
            if (first && typeof first.focus === "function") {
                try { first.focus({ preventScroll: true }); } catch (e) { first.focus(); }
            }
        }
    }

    function reinitSelect2(node) {
        if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.select2) return;
        var $ = window.jQuery;
        // select2 widgets initialised while hidden render with width 0;
        // tell them to recompute now that the row is visible.
        $(node).find("select.django-select2, select[data-autocomplete-light-function], select.select2-hidden-accessible").each(function () {
            var $sel = $(this);
            if ($sel.data("select2")) {
                try { $sel.select2("destroy"); } catch (e) { /* ignore */ }
            }
        });
        // django-select2 binds on document.ready; we trigger its init helper
        // if available, otherwise reapply the default constructor.
        if (typeof $.fn.djangoSelect2 === "function") {
            $(node).find("select.django-select2").djangoSelect2();
        } else {
            $(node).find("select.django-select2, select.select2-hidden-accessible").each(function () {
                try { $(this).select2(); } catch (e) { /* ignore */ }
            });
        }
    }

    function enterEditUrl(action) {
        var href = action.getAttribute("href");
        return href || null;
    }

    function viewUrl(node) {
        var href = node.getAttribute("data-view-url");
        return href || window.location.pathname;
    }

    function onClick(e) {
        var node = root();
        if (!node) return;
        var action = e.target.closest("[data-action]");
        if (!action || !node.contains(action)) return;

        if (action.dataset.action === "enter-edit") {
            e.preventDefault();
            setMode(node, "edit");
            var editHref = enterEditUrl(action);
            if (editHref && window.history && window.history.replaceState) {
                try { window.history.replaceState({}, "", editHref); } catch (err) { /* ignore */ }
            }
        } else if (action.dataset.action === "cancel-edit") {
            e.preventDefault();
            var form = node.querySelector("form") || (node.tagName === "FORM" ? node : null);
            if (form && typeof form.reset === "function") {
                form.reset();
                // Re-sync select2 + radios after reset.
                if (window.jQuery) {
                    window.jQuery(form).find("select").trigger("change");
                }
            }
            setMode(node, "view");
            var back = viewUrl(node);
            if (back && window.history && window.history.replaceState) {
                try { window.history.replaceState({}, "", back); } catch (err) { /* ignore */ }
            }
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
