/* ==========================================================================
   ADRESA-EDIT — inline "Edit address" pencil + modal save handler
   ==========================================================================
   Decorates every result row of an Adresa select2 (the <select> carries
   `data-adresa-edit="1"`) with a pencil button. The pencil fetches the
   address from /api/brzi-izmena-adrese/<uid>/ and opens #adresa-modal
   pre-filled with its fields.

   On save, POSTs to the same endpoint and refreshes the selected <option>
   label of the select that opened the modal, so the user sees the change
   immediately. If the modal was not opened from a pencil, the address uid
   falls back to the select's current value, then to the
   #adresa-modal-initial JSON block (Domacinstvo edit page).

   Rows are decorated by a body-level MutationObserver (catches dropdowns
   as select2 mounts them) plus a select2:open backup for builds that mount
   the dropdown via a documentFragment. A per-dropdown observer keeps
   re-decorating while select2 swaps the results list on each keystroke;
   it is disconnected on select2:close so repeated opens do not leak
   observers. The outer side pencil is intentionally not rendered.

   The modal's Save button and Enter key are bound once, not per select.
   ========================================================================== */

(function ($) {
    if (!$) return;

    const MODAL_ID = "adresa-modal";
    const API_URL = "/api/brzi-izmena-adrese/";
    const FIELDS = ["ulica", "broj", "broj_stana", "mesto"];

    function csrfToken() {
        const el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    function initialPayload() {
        const node = document.getElementById("adresa-modal-initial");
        if (!node) return null;
        try {
            return JSON.parse(node.textContent);
        } catch (_e) {
            return null;
        }
    }

    function fieldInput(field) {
        return document.getElementById("modal-adresa-" + field);
    }

    function errorBox() {
        return document.querySelector("#" + MODAL_ID + " .error-text");
    }

    function hideError() {
        const err = errorBox();
        if (!err) return;
        err.style.display = "none";
        err.textContent = "";
        err.setAttribute("hidden", "");
    }

    function showError(msg) {
        const err = errorBox();
        if (!err) return;
        err.textContent = msg;
        err.removeAttribute("hidden");
        err.style.display = "block";
    }

    function fillFields(data) {
        FIELDS.forEach(function (field) {
            const el = fieldInput(field);
            if (el) el.value = data?.[field] || "";
        });
        hideError();
    }

    function readFields() {
        const fd = new FormData();
        FIELDS.forEach(function (field) {
            const el = fieldInput(field);
            fd.append(field, el ? el.value.trim() : "");
        });
        return fd;
    }

    function refreshSelectLabel($select, data) {
        const select = $select[0];
        if (!select) return;
        Array.from(select.options).forEach(function (opt) {
            if (opt.value === String(data.id)) opt.remove();
        });
        select.appendChild(new Option(data.text, data.id, true, true));
        $select.trigger("change");
    }

    function targetSelect(modal) {
        const target = modal.dataset.targetFieldId
            ? document.getElementById(modal.dataset.targetFieldId)
            : null;
        return target ? $(target) : $("select[data-adresa-edit][id]").first();
    }

    function save() {
        const modal = document.getElementById(MODAL_ID);
        if (!modal) return;
        const $select = targetSelect(modal);
        const uid = modal.dataset.adresaUid || $select.val() || initialPayload()?.uid;
        if (!uid) {
            showError("Нема изабране адресе за измену.");
            return;
        }
        fetch(API_URL + uid + "/", {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken() },
            body: readFields(),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    showError(data.error);
                    return;
                }
                refreshSelectLabel($select, data);
                if (window.Modal) Modal.close(MODAL_ID);
            })
            .catch(function () {
                showError("Грешка при чувању. Покушајте поново.");
            });
    }

    function bindModal() {
        document
            .querySelectorAll("#" + MODAL_ID + " input[type=text]")
            .forEach(function (input) {
                input.addEventListener("keydown", function (ev) {
                    if (ev.key === "Enter") {
                        ev.preventDefault();
                        save();
                    }
                });
            });
        const saveBtn = document.getElementById("adresa-modal-save");
        if (saveBtn) saveBtn.addEventListener("click", save);
    }

    function closeSelect2($select) {
        if ($select?.hasClass("select2-hidden-accessible")) {
            $select.select2("close");
        }
    }

    function openEditModal(uid, $select) {
        if (!uid) return;
        closeSelect2($select);
        fetch(API_URL + uid + "/", { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data?.error) return;
                const modal = document.getElementById(MODAL_ID);
                if (modal) {
                    modal.dataset.adresaUid = uid;
                    if ($select?.length) modal.dataset.targetFieldId = $select.attr("id");
                }
                if (window.Modal) Modal.open(MODAL_ID);
                fillFields(data);
            });
    }

    function findOwningSelect(dropdownEl) {
        const ul = $(dropdownEl).find(".select2-results__options")[0];
        const m = ul?.id?.match(/^select2-(.+)-results$/);
        if (m) {
            const $s = $("#" + m[1]);
            if ($s.length) return $s;
        }
        const openSid = $(".select2-container--open").attr("data-select2-id") || "";
        if (openSid) {
            const $s2 = $("select[data-select2-id='" + openSid + "']");
            if ($s2.length) return $s2;
        }
        return $();
    }

    function uidFromSelect2Cache(li) {
        const amd = $.fn.select2?.amd;
        if (!amd?.require) return "";
        let utils;
        try {
            utils = amd.require("select2/utils");
        } catch (_e) {
            return "";
        }
        const d = utils?.GetData?.(li, "data");
        return d?.id ? String(d.id) : "";
    }

    function uidFromRow(li) {
        const d = $(li).data("data");
        if (d?.id) return String(d.id);
        const cached = uidFromSelect2Cache(li);
        if (cached) return cached;
        const m = (li.id || "").match(/^select2-.+?-result-[^-]+-(.+)$/);
        return m?.[1] || "";
    }

    function swallow(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
    }

    function createPencil(uid, $select) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "adresa-dd-edit";
        btn.setAttribute("data-uid", uid);
        btn.setAttribute("data-tooltip", "Измени адресу");
        btn.setAttribute("aria-label", "Измени адресу");
        btn.innerHTML = '<i class="fa-solid fa-pen" aria-hidden="true"></i>';
        function onPress(e) {
            swallow(e);
            openEditModal(uid, $select);
        }
        btn.addEventListener("mousedown", onPress, true);
        btn.addEventListener("touchstart", onPress, true);
        btn.addEventListener("click", swallow, true);
        return btn;
    }

    function isDecoratableRow(li) {
        return (
            !li.classList.contains("loading-results") &&
            li.getAttribute("role") !== "group" &&
            !li.querySelector(".adresa-dd-edit")
        );
    }

    function paintRows($dropdown, $select) {
        $dropdown.find(".select2-results__option").each(function () {
            if (!isDecoratableRow(this)) return;
            const uid = uidFromRow(this);
            if (uid) this.appendChild(createPencil(uid, $select));
        });
    }

    function decorateDropdown(dropdownEl) {
        if (!dropdownEl) return;
        const $select = findOwningSelect(dropdownEl);
        if (!$select.length || !$select.attr("data-adresa-edit")) return;
        const paint = function () {
            paintRows($(dropdownEl), $select);
        };
        paint();
        if (!dropdownEl._adresaEditObs) {
            const ro = new MutationObserver(paint);
            ro.observe(dropdownEl, { childList: true, subtree: true });
            dropdownEl._adresaEditObs = ro;
        }
    }

    function decorateOpenDropdown() {
        const dd =
            document.querySelector(".select2-container--open .select2-dropdown") ||
            document.querySelector(".select2-dropdown");
        if (dd) decorateDropdown(dd);
    }

    function attach($select) {
        if ($select.data("adresaEditBound")) return;
        $select.data("adresaEditBound", true);

        $select.on("select2:open.adresaEdit", function () {
            decorateOpenDropdown();
            requestAnimationFrame(decorateOpenDropdown);
            setTimeout(decorateOpenDropdown, 200);
        });

        $select.on("select2:close.adresaEdit", function () {
            const dd = document.querySelector(".select2-dropdown");
            if (dd?._adresaEditObs) {
                dd._adresaEditObs.disconnect();
                dd._adresaEditObs = null;
            }
        });
    }

    function decorateAddedNode(n) {
        if (n.nodeType !== 1) return;
        if (n.classList.contains("select2-dropdown")) {
            decorateDropdown(n);
            return;
        }
        const inner = n.querySelector(".select2-dropdown");
        if (inner) decorateDropdown(inner);
    }

    function startBodyObserver() {
        const bo = new MutationObserver(function (muts) {
            muts.forEach(function (m) {
                m.addedNodes.forEach(decorateAddedNode);
            });
        });
        bo.observe(document.documentElement, { childList: true, subtree: true });
        document.body._adresaDdObs = bo;
    }

    function init() {
        startBodyObserver();
        const $selects = $("select[data-adresa-edit][id]");
        $selects.each(function () {
            attach($(this));
        });
        if ($selects.length) bindModal();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})(window.jQuery);
