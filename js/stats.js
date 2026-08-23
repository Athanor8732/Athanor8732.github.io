(function () {
  var scriptTag = document.currentScript;
  var path = scriptTag.getAttribute('data-path') || 'data/stats.json';
  fetch(path)
    .then(function (r) { return r.json(); })
    .then(function (stats) {
      document.querySelectorAll('[data-stat]').forEach(function (el) {
        var key = el.getAttribute('data-stat');
        if (stats[key] !== undefined) el.textContent = stats[key];
      });
    })
    .catch(function () {
      /* keep the static fallback text already in the HTML */
    });
})();
