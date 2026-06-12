/* Print a remote certificate (krstenica / vencanica) without leaving the
   current list page. On click:
     1. lazy-load the certificate stylesheet (cached via <link>)
     2. fetch the detail page HTML
     3. lift the .krstenica / .vencanica node into the current document
     4. call window.print()
     5. clean up on afterprint

   Triggered by any element carrying data-print-cert. Attributes:
     data-print-cert            URL of the detail page
     data-print-cert-selector   CSS selector for the certificate node
     data-print-css             optional URL of the certificate stylesheet
                                (lazy-loaded once; cached by URL)
*/
(function () {
    const loadedCss = {};

    function loadCSS(href) {
        if (!href) return Promise.resolve();
        if (loadedCss[href]) return loadedCss[href];
        loadedCss[href] = new Promise(function (resolve, reject) {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = href;
            link.setAttribute("data-print-css", href);
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
        return loadedCss[href];
    }

    function printRemote(detailUrl, selector, cssUrl) {
        return Promise.all([
            loadCSS(cssUrl),
            fetch(detailUrl, { credentials: "same-origin" }).then(function (r) {
                return r.text();
            }),
        ]).then(function (results) {
            const html = results[1];
            const doc = new DOMParser().parseFromString(html, "text/html");
            const node = doc.querySelector(selector);
            if (!node) {
                window.alert("Сертификат није пронађен. Покушај поново.");
                return;
            }
            const wrap = document.createElement("div");
            wrap.id = "print-cert-wrap";
            wrap.appendChild(node);
            document.body.appendChild(wrap);
            document.body.classList.add("printing-cert");
            const cleanup = function () {
                wrap.remove();
                document.body.classList.remove("printing-cert");
                window.removeEventListener("afterprint", cleanup);
            };
            window.addEventListener("afterprint", cleanup);
            window.print();
        }).catch(function () {
            window.alert("Грешка при штампању.");
        });
    }

    document.addEventListener("click", function (ev) {
        const btn = ev.target.closest("[data-print-cert]");
        if (!btn) return;
        ev.preventDefault();
        const url = btn.getAttribute("data-print-cert");
        const sel = btn.getAttribute("data-print-cert-selector") || ".krstenica";
        const css = btn.getAttribute("data-print-css") || null;
        printRemote(url, sel, css);
    });
})();
