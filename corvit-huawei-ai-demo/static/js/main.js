/**
 * Corvit Huawei AI Demo — site-wide behaviour.
 * Mobile nav toggle + a small scroll-reveal effect. Runs on every page
 * (included from base.html); page-specific logic lives in predictor.js
 * and charts.js instead.
 */
(function () {
  "use strict";

  function initNavToggle() {
    var toggle = document.getElementById("nav-toggle");
    var nav = document.getElementById("primary-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    // Close the menu after navigating (mobile), and on outside click.
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });

    document.addEventListener("click", function (event) {
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(event.target) || toggle.contains(event.target)) return;
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  function initScrollReveal() {
    var targets = document.querySelectorAll(
      ".feature-card, .step-item, .card, .predictor-card, .metric-tile"
    );
    if (!targets.length) return;

    targets.forEach(function (el) {
      el.classList.add("reveal");
    });

    if (!("IntersectionObserver" in window)) {
      // No IO support: just show everything, no progressive enhancement lost.
      targets.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    targets.forEach(function (el) {
      observer.observe(el);
    });

    // Safety net: a full-page screenshot/print, or a viewport resize that
    // doesn't fire fresh intersection checks, can otherwise leave
    // below-the-fold content permanently at opacity 0. Normal scrolling
    // reveals everything well before this fires; this only catches the
    // non-interactive-rendering edge case so content is never lost.
    window.setTimeout(function () {
      targets.forEach(function (el) {
        el.classList.add("is-visible");
      });
      observer.disconnect();
    }, 1500);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNavToggle();
    initScrollReveal();
  });
})();
