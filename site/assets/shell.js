/* RateLark shell for plugin tool pages: language switching (the older tools have their own script). */
(function () {
  'use strict';
  var sel = document.getElementById('lang');
  var slug = document.body.getAttribute('data-tool');
  if (!sel || !slug) return;
  sel.addEventListener('change', function (e) {
    var l = e.target.value;
    try { localStorage.setItem('fr:lang', JSON.stringify(l)); } catch (x) {}
    location.href = '/' + l + '/' + slug + '/' + (location.hash || '');
  });
})();
