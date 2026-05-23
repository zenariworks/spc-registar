/* ==========================================================================
   MODAL — generic open/close + bindForm helper
   ==========================================================================
   Used by quick-add modals (e.g. osoba). One global `Modal` object.

   API:
     Modal.open(modalId, targetFieldId?)
         Show the modal. If targetFieldId is given, the Select2 widget with
         that id receives the new option on save.

     Modal.close(modalId)
         Hide the modal.

     var inst = Modal.bindForm(modalId, options)
         Bind a quick-add form. Returns { open, close, save } so existing
         inline onclick="osobaModal.open('id_dete')" calls keep working.

         options = {
             url:          "/api/brzi-unos-osobe/",  // POST endpoint
             fields:       ["ime", "prezime", "pol"],  // input ids: "modal-<field>"
             toggleGroups: { pol: "modal-pol-toggle" },  // optional: data-value toggle buttons
             requiredMessage: "Име и презиме су обавезни.",
             requiredFields: ["ime", "prezime"],
             onSuccess:    function(data, targetFieldId) { ... }
                           // default: appends new <option> to the Select2 widget
         }

   Global behaviours wired automatically:
     - Esc closes any open modal
     - Click on the overlay (not its child) closes
     - Enter inside a text input triggers save
   ========================================================================== */

(function () {
    "use strict";

    const _openModals = new Set();

    function _csrfToken() {
        const el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    function open(modalId, targetFieldId) {
        const overlay = document.getElementById(modalId);
        if (!overlay) return;
        overlay._targetFieldId = targetFieldId || null;
        // The overlay carries the HTML5 [hidden] attribute, which modali.css
        // pins to display:none !important. Inline style alone cannot win that
        // cascade — we have to drop the attribute too.
        overlay.removeAttribute("hidden");
        overlay.style.display = "flex";
        _openModals.add(modalId);
        // Clear inputs / errors
        overlay.querySelectorAll("input[type=text]").forEach((i) => (i.value = ""));
        overlay
            .querySelectorAll(".tab-group__item.is-active")
            .forEach((b) => b.classList.remove("is-active"));
        const err = overlay.querySelector(".error-text");
        if (err) { err.style.display = "none"; err.setAttribute("hidden", ""); }
        // Focus the first input
        setTimeout(() => {
            const first = overlay.querySelector("input[type=text]");
            if (first) first.focus();
        }, 50);
    }

    function close(modalId) {
        const overlay = document.getElementById(modalId);
        if (!overlay) return;
        overlay.style.display = "";
        overlay.setAttribute("hidden", "");
        overlay._targetFieldId = null;
        _openModals.delete(modalId);
    }

    function _defaultOnSuccess(data, targetFieldId) {
        if (!targetFieldId) return;
        const select = document.getElementById(targetFieldId);
        if (!select) return;
        const option = new Option(data.text, data.id, true, true);
        select.appendChild(option);
        if (window.jQuery) {
            jQuery(select).trigger("change");
        }
    }

    function bindForm(modalId, options) {
        const overlay = document.getElementById(modalId);
        if (!overlay) {
            console.warn("Modal.bindForm: no element with id", modalId);
            return null;
        }
        const opts = Object.assign(
            {
                url: "",
                fields: [],
                toggleGroups: {},
                requiredFields: [],
                requiredMessage: "Сва обавезна поља морају бити попуњена.",
                onSuccess: _defaultOnSuccess,
            },
            options || {},
        );

        // Wire tab-group items (e.g. pol: M/Ж)
        const toggleState = {};
        Object.entries(opts.toggleGroups).forEach(([fieldName, groupId]) => {
            const group = document.getElementById(groupId);
            if (!group) return;
            group.querySelectorAll(".tab-group__item").forEach((btn) => {
                btn.addEventListener("click", () => {
                    group
                        .querySelectorAll(".tab-group__item")
                        .forEach((b) => b.classList.remove("is-active"));
                    btn.classList.add("is-active");
                    toggleState[fieldName] = btn.dataset.value;
                });
            });
        });

        // Enter inside any text input → save
        overlay.querySelectorAll("input[type=text]").forEach((input) => {
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    save();
                }
            });
        });

        function _showError(msg) {
            const err = overlay.querySelector(".error-text");
            if (err) {
                err.textContent = msg;
                err.removeAttribute("hidden");
                err.style.display = "block";
            }
        }

        function save() {
            const values = {};
            for (const f of opts.fields) {
                const el = document.getElementById("modal-" + f);
                if (el) values[f] = el.value.trim();
            }
            Object.entries(toggleState).forEach(([k, v]) => {
                values[k] = v;
            });

            // Validate required
            const missing = opts.requiredFields.filter((f) => !values[f]);
            if (missing.length) {
                _showError(opts.requiredMessage);
                return;
            }
            _showError("");
            const err = overlay.querySelector(".error-text");
            if (err) { err.style.display = "none"; err.setAttribute("hidden", ""); }

            const formData = new FormData();
            Object.entries(values).forEach(([k, v]) => formData.append(k, v || ""));

            fetch(opts.url, {
                method: "POST",
                headers: { "X-CSRFToken": _csrfToken() },
                body: formData,
            })
                .then((r) => r.json())
                .then((data) => {
                    if (data.error) {
                        _showError(data.error);
                        return;
                    }
                    opts.onSuccess(data, overlay._targetFieldId);
                    close(modalId);
                })
                .catch(() => {
                    _showError("Грешка при чувању. Покушајте поново.");
                });
        }

        return {
            open: function (targetFieldId) {
                open(modalId, targetFieldId);
            },
            close: function () {
                close(modalId);
            },
            save: save,
        };
    }

    // Global Esc + overlay-click handlers
    document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape" || _openModals.size === 0) return;
        // Close the most recently opened modal
        const last = Array.from(_openModals).pop();
        close(last);
    });
    document.addEventListener("click", (e) => {
        if (e.target.classList && e.target.classList.contains("modal-overlay")) {
            close(e.target.id);
        }
    });

    window.Modal = { open: open, close: close, bindForm: bindForm };
})();
