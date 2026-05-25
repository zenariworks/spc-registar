/* Print a remote certificate (krstenica / vencanica) without leaving the
   current list page. Fetches the detail page, lifts the .krstenica /
   .vencanica node into the current document, calls window.print(), and
   cleans up after the print dialog closes. */
(function () {
    function printRemote(url, selector) {
        fetch(url, { credentials: "same-origin" })
            .then(function (r) { return r.text(); })
            .then(function (html) {
                var doc = new DOMParser().parseFromString(html, "text/html");
                var node = doc.querySelector(selector);
                if (!node) {
                    window.alert("Сертификат није пронађен. Покушај поново.");
                    return;
                }
                var wrap = document.createElement("div");
                wrap.id = "print-cert-wrap";
                wrap.appendChild(node);
                document.body.appendChild(wrap);
                document.body.classList.add("printing-cert");
                var cleanup = function () {
                    wrap.remove();
                    document.body.classList.remove("printing-cert");
                    window.removeEventListener("afterprint", cleanup);
                };
                window.addEventListener("afterprint", cleanup);
                window.print();
            })
            .catch(function () { window.alert("Грешка при штампању."); });
    }

    document.addEventListener("click", function (ev) {
        var btn = ev.target.closest("[data-print-cert]");
        if (!btn) return;
        ev.preventDefault();
        var url = btn.getAttribute("data-print-cert");
        var sel = btn.getAttribute("data-print-cert-selector") || ".krstenica";
        printRemote(url, sel);
    });
})();
