/* RateLark shell: language switching for plugin tool pages and the language hubs
   (the older tools have their own script). English lives at the site root, so the
   English hub is "/", not "/en/". */
(function () {
  'use strict';
  var sel = document.getElementById('lang');
  if (!sel) return;
  var slug = document.body.getAttribute('data-tool');
  var hub = document.body.hasAttribute('data-hub');
  if (!slug && !hub) return;
  sel.addEventListener('change', function (e) {
    var l = e.target.value;
    try { localStorage.setItem('fr:lang', JSON.stringify(l)); } catch (x) {}
    if (hub) {
      location.href = l === 'en' ? '/' : '/' + l + '/';
    } else {
      location.href = '/' + l + '/' + slug + '/' + (location.hash || '');
    }
  });
})();
