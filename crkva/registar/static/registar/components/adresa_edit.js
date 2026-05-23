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
            err.setAttribute("hidden", "");
        }
    }

    function showError(msg) {
        const err = document.querySelector("#adresa-modal .error-text");
        if (!err) return;
        err.textContent = msg;
        err.removeAttribute("hidden");
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

        // Build a small pencil button immediately to the right of the
        // .info-row__value wrapper holding this select.
        const $container = $select.closest(".info-row__value");
        if (!$container.length) return;
        if ($container.find(".adresa-edit-btn").length) return;

        const $btn = $(
            '<button type="button" class="adresa-edit-btn" ' +
                'data-tooltip="Измени адресу" aria-label="Измени адресу">' +
                '<i class="fa-solid fa-pen" aria-hidden="true"></i>' +
            "</button>"
        );
        $container.append($btn);

        $btn.on("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            const uid = currentAdresaUid($select);
            if (!uid) {
                showError("Прво изаберите адресу из листе.");
                if (window.Modal) Modal.open("adresa-modal");
                fillModalFields({});
                return;
            }
            // Pull the cached payload if it matches the current select value;
            // otherwise leave fields blank and let the user retype.
            const payload = getInitialPayload();
            fillModalFields(payload && payload.uid === uid ? payload : {});
            const modal = document.getElementById("adresa-modal");
            if (modal) {
                modal.dataset.targetFieldId = fieldId;
                modal.dataset.adresaUid = uid;
            }
            if (window.Modal) Modal.open("adresa-modal");
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

    function init() {
        $("select[data-adresa-edit]").each(function () { attach($(this)); });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})(window.jQuery);
