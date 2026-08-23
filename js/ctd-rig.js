/**
 * ctd-rig.js — animació del CTD rosette que segueix el scroll.
 * Auto-inicialitzable: només cal <script src="js/ctd-rig.js" defer></script>
 * Pausa l'animació quan el rig no és visible (estalvi CPU).
 * Respecta prefers-reduced-motion.
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var rosette = document.getElementById('ctd-rosette');
  var cable = document.getElementById('ctd-cable');
  if (!rosette || !cable) return;

  var wake = document.getElementById('ctd-wake');
  var depth = document.getElementById('ctd-depth');
  var depthMobile = document.getElementById('ctd-depth-mobile');
  var sensor = document.getElementById('ctd-sensor');
  var rig = document.querySelector('.ctd-rig');

  if (reduceMotion) {
    // Sense animació: fixa el rig a posició mitjana
    var midY = (window.innerHeight - 187) * 0.5;
    rosette.style.transform = 'translateY(' + midY + 'px)';
    cable.style.height = midY + 'px';
    if (depth) depth.textContent = '600 m';
    if (depthMobile) depthMobile.textContent = '600 m';
    if (depth) depth.style.transform = 'translateY(' + (midY + 79) + 'px)';
    return;
  }

  var targetY = 0, currentY = 0;
  var rafId = null;
  var isVisible = true;

  function computeTarget() {
    var scrollTop = window.scrollY || document.documentElement.scrollTop;
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    var frac = docHeight > 0 ? Math.min(1, Math.max(0, scrollTop / docHeight)) : 0;
    var maxDrop = window.innerHeight - 187;
    targetY = frac * maxDrop;
    var depthText = Math.round(frac * 1200) + ' m';
    if (depth) depth.textContent = depthText;
    if (depthMobile) depthMobile.textContent = depthText;
  }

  function render() {
    currentY += (targetY - currentY) * 0.08;
    if (Math.abs(targetY - currentY) < 0.05) currentY = targetY;
    rosette.style.transform = 'translateY(' + currentY + 'px)';
    cable.style.height = currentY + 'px';
    if (wake) {
      var wakeH = Math.min(40, currentY);
      wake.style.height = wakeH + 'px';
      wake.style.top = (108 + currentY - wakeH) + 'px';
    }
    if (depth) depth.style.transform = 'translateY(' + (currentY + 79) + 'px)';
    rafId = requestAnimationFrame(render);
  }

  function startLoop() {
    if (rafId === null) {
      rafId = requestAnimationFrame(render);
    }
  }

  function stopLoop() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  // Pausar l'animació quan el rig no és visible (estalvi CPU)
  if (rig && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        isVisible = e.isIntersecting;
        if (isVisible) startLoop(); else stopLoop();
      });
    }, { threshold: 0 });
    io.observe(rig);
  }

  window.addEventListener('scroll', computeTarget, { passive: true });
  window.addEventListener('resize', computeTarget);
  computeTarget();
  startLoop();

  // Sensor flash al creuar seccions
  if (sensor && 'IntersectionObserver' in window) {
    var sio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          sensor.classList.remove('ctd-sensor-flash');
          void sensor.getBoundingClientRect();
          sensor.classList.add('ctd-sensor-flash');
        }
      });
    }, { threshold: 0, rootMargin: '-45% 0px -45% 0px' });
    document.querySelectorAll('h2.section').forEach(function (h) { sio.observe(h); });
  }
})();