/**
 * reveal.js — animació de scroll-reveal per als elements .reveal.
 * Auto-inicialitzable: només cal <script src="js/reveal.js" defer></script>
 * Respecta prefers-reduced-motion (no oculta res si l'usuari demana menys moviment).
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  if (reduceMotion || !('IntersectionObserver' in window)) {
    // Sense animació: mostra tot immediatament
    els.forEach(function (el) { el.classList.add('is-visible'); });
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(function (el) { io.observe(el); });
})();