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

         Field inputs and toggle groups are looked up inside the modal, so
         several modals on one page may reuse ids such as "modal-ime".
         Opening a modal clears its inputs, errors and toggle selection.

   Global behaviours wired automatically:
     - Esc closes any open modal
     - Click on the overlay (not its child) closes
     - Enter inside a text input triggers save
   ========================================================================== */

(function () {
    const TOGGLE_ITEM = ".tab-group__item";
    const SAVE_FAILED = "Грешка при чувању. Покушајте поново.";

    const _openModals = new Set();
    const _resetHandlers = {};

    function _csrfToken() {
        const el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    function _textInputs(overlay) {
        return overlay.querySelectorAll("input[type=text]");
    }

    function _showError(overlay, msg) {
        const err = overlay.querySelector(".error-text");
        if (!err) return;
        err.textContent = msg;
        err.removeAttribute("hidden");
        err.style.display = "block";
    }

    function _hideError(overlay) {
        const err = overlay.querySelector(".error-text");
        if (!err) return;
        err.style.display = "none";
        err.setAttribute("hidden", "");
    }

    function _focusFirstInput(overlay) {
        setTimeout(() => {
            const first = overlay.querySelector("input[type=text]");
            if (first) first.focus();
        }, 50);
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
        _textInputs(overlay).forEach((i) => (i.value = ""));
        overlay
            .querySelectorAll(TOGGLE_ITEM + ".is-active")
            .forEach((b) => b.classList.remove("is-active"));
        _resetHandlers[modalId]?.();
        _hideError(overlay);
        _focusFirstInput(overlay);
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

    function _bindToggleGroups(overlay, toggleGroups, state) {
        Object.entries(toggleGroups).forEach(([fieldName, groupId]) => {
            const group = overlay.querySelector("#" + groupId);
            if (!group) return;
            const items = group.querySelectorAll(TOGGLE_ITEM);
            items.forEach((btn) => {
                btn.addEventListener("click", () => {
                    items.forEach((b) => b.classList.remove("is-active"));
                    btn.classList.add("is-active");
                    state[fieldName] = btn.dataset.value;
                });
            });
        });
    }

    function _bindEnterToSave(overlay, save) {
        _textInputs(overlay).forEach((input) => {
            input.addEventListener("keydown", (e) => {
                if (e.key !== "Enter") return;
                e.preventDefault();
                save();
            });
        });
    }

    function _readValues(overlay, fields, toggleState) {
        const values = {};
        for (const f of fields) {
            const el = overlay.querySelector("#modal-" + f);
            if (el) values[f] = el.value.trim();
        }
        return Object.assign(values, toggleState);
    }

    function _post(url, values) {
        const formData = new FormData();
        Object.entries(values).forEach(([k, v]) => formData.append(k, v || ""));
        return fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": _csrfToken() },
            body: formData,
        }).then((r) => r.json());
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

        const toggleState = {};
        _resetHandlers[modalId] = () => {
            Object.keys(toggleState).forEach((k) => delete toggleState[k]);
        };

        function save() {
            const values = _readValues(overlay, opts.fields, toggleState);
            if (opts.requiredFields.some((f) => !values[f])) {
                _showError(overlay, opts.requiredMessage);
                return;
            }
            _hideError(overlay);
            _post(opts.url, values)
                .then((data) => {
                    if (data.error) {
                        _showError(overlay, data.error);
                        return;
                    }
                    opts.onSuccess(data, overlay._targetFieldId);
                    close(modalId);
                })
                .catch(() => _showError(overlay, SAVE_FAILED));
        }

        _bindToggleGroups(overlay, opts.toggleGroups, toggleState);
        _bindEnterToSave(overlay, save);

        return {
            open: (targetFieldId) => open(modalId, targetFieldId),
            close: () => close(modalId),
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
        if (e.target.classList?.contains("modal-overlay")) {
            close(e.target.id);
        }
    });

    window.Modal = { open: open, close: close, bindForm: bindForm };
})();
