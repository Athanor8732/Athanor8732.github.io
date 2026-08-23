(function () {
  var list = document.querySelector('.pub-list');
  if (!list) return;
  var path = (document.currentScript.getAttribute('data-path') || 'data/publications.json');

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function renderCard(p) {
    var meta = '';
    var jline = '<b>' + esc(p.journal) + '</b>';
    if (p.volume) jline += ', ' + esc(p.volume);
    if (p.issue) jline += '(' + esc(p.issue) + ')';
    if (p.pages) jline += ', ' + esc(p.pages);
    meta += '<span>' + jline + '</span>';
    meta += '<span>' + esc(p.year) + '</span>';
    var q = '';
    if (p.jif && p.quartile) q = 'JIF ' + esc(p.jif) + ' · ' + esc(p.quartile);
    else if (p.quartile) q = esc(p.quartile);
    else if (p.jif) q = 'JIF ' + esc(p.jif);
    if (q) meta += '<span>' + q + '</span>';
    meta += '<span>cites: ' + esc(p.citations) + '</span>';
    if (p.doi) {
      meta += '<a class="doi" href="https://doi.org/' + esc(p.doi) +
        '" target="_blank" rel="noopener">DOI →</a>';
    }
    // p.authors és HTML curat (conté <b>); no s'escapa
    return '<div class="pub-card">' +
      '<p class="authors">' + p.authors + '</p>' +
      '<p class="title">' + esc(p.title) + '</p>' +
      '<div class="meta">' + meta + '</div>' +
      '</div>';
  }

  fetch(path)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var pubs = data && data.publications ? data.publications : [];
      if (!pubs.length) return;
      list.innerHTML = pubs.map(renderCard).join('');
    })
    .catch(function () {
      /* si falla la càrrega, es manté la llista estàtica del HTML com a fallback */
    });
})();