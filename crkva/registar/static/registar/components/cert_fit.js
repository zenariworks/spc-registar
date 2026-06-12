/* Fit .krstenica / .vencanica to its container width on screen so the
   210x297mm preview is visible on narrow viewports (mobile, sidebar
   collapsed, etc). Print stylesheet overrides this back to the full
   geometry. */
(function () {
    function natural(cert) {
        if (cert.dataset.natW) {
            return { w: Number.parseFloat(cert.dataset.natW), h: Number.parseFloat(cert.dataset.natH) };
        }
        const prev = cert.style.transform;
        const prevMb = cert.style.marginBottom;
        cert.style.transform = "";
        cert.style.marginBottom = "";
        const w = cert.offsetWidth;
        const h = cert.offsetHeight;
        cert.style.transform = prev;
        cert.style.marginBottom = prevMb;
        if (w > 0) {
            cert.dataset.natW = w;
            cert.dataset.natH = h;
        }
        return { w: w, h: h };
    }

    function fitCert(cert) {
        if (cert.offsetParent === null) return; // hidden tab
        const n = natural(cert);
        if (!n.w) return;
        const avail = cert.parentElement.clientWidth;
        const scale = Math.min(1, avail / n.w);
        cert.style.transformOrigin = "top left";
        cert.style.transform = scale < 1 ? "scale(" + scale + ")" : "";
        cert.style.marginBottom = scale < 1 ? (-(n.h * (1 - scale))) + "px" : "";
    }

    function fitAll() {
        document.querySelectorAll(".krstenica, .vencanica").forEach(fitCert);
    }

    let raf = null;
    function schedule() {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(fitAll);
    }

    window.addEventListener("resize", schedule);
    document.addEventListener("DOMContentLoaded", schedule);
    window.addEventListener("load", schedule);

    // Re-fit when user switches tabs (cert panel may have been hidden at load).
    document.addEventListener("change", function (e) {
        const t = e.target;
        if (t && t.tagName === "INPUT" && t.type === "radio" && t.closest(".tab-group__nav")) {
            schedule();
        }
    });
})();
