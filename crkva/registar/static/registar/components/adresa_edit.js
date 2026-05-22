/* ==========================================================================
   ADRESA-EDIT — inline "Edit address" pencil + modal save handler
   ==========================================================================
   Wires a small pencil button next to any Adresa select2 (marked with
   `data-adresa-edit="1"`) that opens #adresa-modal pre-filled with the
   currently selected Adresa's fields.

   On save, POSTs to /api/brzi-izmena-adrese/<uid>/ and refreshes the
   select2's selected <option> label with the updated representation so the
   user sees the change immediately.

   Architecture mirrors osoba_create.js — both use Modal.bindForm but this
   one targets an existing row (PUT-semantics POST) rather than creating
   a new one. The endpoint UUID is taken from the select2's current value.
   ========================================================================== */

(function ($) {
    "use strict";
    if (!$) return;

    function csrfToken() {
        const el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    function getInitialPayload() {
        const node = document.getElementById("adresa-modal-initial");
        if (!node) return null;
        try {
            return JSON.parse(node.textContent);
        } catch (e) {
            return null;
        }
    }

    function fillModalFields(payload) {
        const map = {
            ulica: "modal-adresa-ulica",
            broj: "modal-adresa-broj",
            broj_stana: "modal-adresa-broj_stana",
            mesto: "modal-adresa-mesto",
        };
        Object.entries(map).forEach(function (entry) {
            const el = document.getElementById(entry[1]);
            if (el) el.value = (payload && payload[entry[0]]) || "";
        });
        const err = document.querySelector("#adresa-modal .error-text");
        if (err) {
            err.style.display = "none";
            err.textContent = "";
        }
    }

    function showError(msg) {
        const err = document.querySelector("#adresa-modal .error-text");
        if (!err) return;
        err.textContent = msg;
        err.style.display = "block";
    }

    function currentAdresaUid($select) {
        const v = $select.val();
        if (v) return v;
        const payload = getInitialPayload();
        return payload ? payload.uid : "";
    }

    function refreshSelectLabel($select, data) {
        const select = $select[0];
        if (!select) return;
        // Strip any existing options matching this uid so the new label wins.
        Array.from(select.options).forEach(function (opt) {
            if (opt.value === String(data.id)) opt.remove();
        });
        const option = new Option(data.text, data.id, true, true);
        select.appendChild(option);
        $select.trigger("change");
    }

    function attach($select) {
        if ($select.data("adresaEditBound")) return;
        $select.data("adresaEditBound", true);

        const fieldId = $select.attr("id");
        if (!fieldId) return;

        // The outer side pencil is intentionally NOT rendered any more.
        // Decoration of dropdown rows is handled by the body-level
        // observer AND this direct select2:open backup, in case the
        // observer does not fire (some select2 builds mount the dropdown
        // via documentFragment, which can miss MutationObserver).
        $select.on("select2:open.adresaEdit", function () {
            // Try immediately, again on next frame, then again after ajax settles.
            function findAndDecorate() {
                var dd = document.querySelector(".select2-container--open .select2-dropdown")
                      || document.querySelector(".select2-dropdown");
                if (dd) decorateDropdown(dd);
            }
            findAndDecorate();
            requestAnimationFrame(findAndDecorate);
            setTimeout(findAndDecorate, 200);
        });


        // Enter inside any modal input submits.
        document
            .querySelectorAll("#adresa-modal input[type=text]")
            .forEach(function (input) {
                input.addEventListener("keydown", function (ev) {
                    if (ev.key === "Enter") {
                        ev.preventDefault();
                        save();
                    }
                });
            });

        function save() {
            const modal = document.getElementById("adresa-modal");
            if (!modal) return;
            const uid = modal.dataset.adresaUid || currentAdresaUid($select);
            if (!uid) {
                showError("Нема изабране адресе за измену.");
                return;
            }
            const fd = new FormData();
            ["ulica", "broj", "broj_stana", "mesto"].forEach(function (f) {
                const el = document.getElementById("modal-adresa-" + f);
                fd.append(f, el ? el.value.trim() : "");
            });
            fetch("/api/brzi-izmena-adrese/" + uid + "/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken() },
                body: fd,
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.error) {
                        showError(data.error);
                        return;
                    }
                    refreshSelectLabel($select, data);
                    if (window.Modal) Modal.close("adresa-modal");
                })
                .catch(function () {
                    showError("Грешка при чувању. Покушајте поново.");
                });
        }

        // The save button is shared across attaches; only bind once.
        const saveBtn = document.getElementById("adresa-modal-save");
        if (saveBtn && !saveBtn.dataset.bound) {
            saveBtn.dataset.bound = "1";
            saveBtn.addEventListener("click", save);
        } else if (saveBtn) {
            // Re-attach the latest closure so saving routes to the active select.
            saveBtn.onclick = save;
        }
    }

    // Delegated handler for the dropdown-injected pencils. mousedown beats
    // select2's own click-to-select on the parent .select2-results__option.
    $(document).on("mousedown touchstart", ".adresa-dd-edit", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var uid = $(this).attr("data-uid");
        if (!uid) return;
        var dropdownEl = $(this).closest(".select2-dropdown")[0];
        var $select = dropdownEl
            ? findOwningSelect(dropdownEl)
            : $("select.django-select2[data-adresa-edit]").first();
        if ($select.length) {
            try { $select.select2("close"); } catch (err) {}
        }
        fetch("/api/brzi-izmena-adrese/" + uid + "/", { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.error) return;
                var modal = document.getElementById("adresa-modal");
                if (modal) {
                    modal.dataset.adresaUid = uid;
                    if ($select.length) modal.dataset.targetFieldId = $select.attr("id");
                }
                var map = {
                    ulica: "modal-adresa-ulica",
                    broj: "modal-adresa-broj",
                    broj_stana: "modal-adresa-broj_stana",
                    mesto: "modal-adresa-mesto",
                };
                Object.keys(map).forEach(function (k) {
                    var el = document.getElementById(map[k]);
                    if (el) el.value = (data && data[k]) || "";
                });
                var err = document.querySelector("#adresa-modal .error-text");
                if (err) { err.style.display = "none"; err.textContent = ""; }
                if (window.Modal) Modal.open("adresa-modal");
            });
    });

    // ------------------------------------------------------------------
    // Body-level dropdown decoration. Watches the document body for any
    // .select2-dropdown being added; when one appears, finds the owning
    // <select> via aria-owns and (if it has data-adresa-edit) decorates
    // every result row with an inline pencil. A nested observer on the
    // results <ul> keeps decorating as the rows are replaced on each
    // search keystroke. This avoids any timing race with select2 init.
    // ------------------------------------------------------------------
    function findOwningSelect(dropdownEl) {
        var $dropdown = $(dropdownEl);
        // 1) The results UL has id="select2-{selectId}-results".
        var ul = $dropdown.find(".select2-results__options")[0];
        if (ul && ul.id) {
            var m = ul.id.match(/^select2-(.+)-results$/);
            if (m) {
                var $s = $("#" + m[1]);
                if ($s.length) return $s;
            }
        }
        // 2) Fallback: match .select2-container--open[data-select2-id]
        //    against the <select data-select2-id="...">.
        var openSid = $(".select2-container--open").attr("data-select2-id") || "";
        if (openSid) {
            var $s2 = $("select[data-select2-id='" + openSid + "']");
            if ($s2.length) return $s2;
        }
        return $();
    }

    function decorateDropdown(dropdownEl) {
        if (!dropdownEl) return;
        var $select = findOwningSelect(dropdownEl);
        if (!$select.length || !$select.attr("data-adresa-edit")) return;
        var $dropdown = $(dropdownEl);

        function uidFromRow(li) {
            // 1) jQuery .data() (vanilla select2 stores here).
            var d = $(li).data("data");
            if (d && d.id) return String(d.id);
            // 2) select2 internal Utils.__cache (the canonical store).
            if ($.fn.select2 && $.fn.select2.amd && $.fn.select2.amd.require) {
                try {
                    var Utils = $.fn.select2.amd.require("select2/utils");
                    if (Utils && Utils.GetData) {
                        d = Utils.GetData(li, "data");
                        if (d && d.id) return String(d.id);
                    }
                } catch (e) {}
            }
            // 3) Fallback: id pattern "select2-XX-result-RRRR-{value}".
            var id = li.id || "";
            var m = id.match(/^select2-.+?-result-[^-]+-(.+)$/);
            if (m && m[1]) return m[1];
            return "";
        }
        function paint() {
            var rows = $dropdown.find(".select2-results__option");
            var added = 0;
            rows.each(function () {
                if (this.classList.contains("loading-results")) return;
                if (this.getAttribute("role") === "group") return;
                var uid = uidFromRow(this);
                if (!uid) return;
                if ($(this).find(".adresa-dd-edit").length) return;
                $(this).append(
                    '<button type="button" class="adresa-dd-edit" data-uid="' +
                        uid + '" data-tooltip="Измени адресу" ' +
                        'aria-label="Измени адресу">' +
                        '<i class="fa-solid fa-pen" aria-hidden="true"></i></button>'
                );
                added++;
            });
        }
        paint();

        // Observe the WHOLE dropdown subtree because select2 swaps the
        // results <ul> wholesale on each ajax refresh; observing only the
        // ul would orphan the observer on the next keystroke.
        if (!dropdownEl._adresaEditObs) {
            var ro = new MutationObserver(paint);
            ro.observe(dropdownEl, { childList: true, subtree: true });
            dropdownEl._adresaEditObs = ro;
        }
    }

    function startBodyObserver() {
        var bo = new MutationObserver(function (muts) {
            muts.forEach(function (m) {
                m.addedNodes.forEach(function (n) {
                    if (n.nodeType !== 1) return;
                    if (n.classList && n.classList.contains("select2-dropdown")) {
                        decorateDropdown(n);
                    } else if (n.querySelector) {
                        var inner = n.querySelector(".select2-dropdown");
                        if (inner) decorateDropdown(inner);
                    }
                });
            });
        });
        // Widen scope to <html> so we catch dropdowns mounted outside body too.
        bo.observe(document.documentElement, { childList: true, subtree: true });
        document.body._adresaDdObs = bo;
    }

    function init() {
        startBodyObserver();
        $("select[data-adresa-edit]").each(function () { attach($(this)); });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})(window.jQuery);
