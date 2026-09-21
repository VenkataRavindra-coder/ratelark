/* RateLark homepage: language-aware buttons and the directory filter (no 3D engine needed). */
// send the buttons to the visitor's language
(function () {
  const ok = ['en', 'es', 'pt', 'fr', 'de', 'hi', 'ar', 'zh', 'id'];
  let l = null;
  try { l = JSON.parse(localStorage.getItem('fr:lang')); } catch (e) {}
  if (!l) l = (navigator.language || 'en').slice(0, 2).toLowerCase();
  if (ok.indexOf(l) < 0) l = 'en';
  document.querySelectorAll('[data-tool]').forEach(a => { a.href = '/' + l + '/' + a.dataset.tool + '/'; });
})();

// directory filter (all / category); a filtered grid drops the featured layout so there are no gaps
(function () {
  var bento = document.getElementById('bento');
  if (!bento) return;
  var tiles = [].slice.call(bento.querySelectorAll('.tile'));
  document.querySelectorAll('.filters button').forEach(function (b) {
    b.addEventListener('click', function () {
      var cat = b.dataset.cat;
      document.querySelectorAll('.filters button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      tiles.forEach(function (t) { t.hidden = !(cat === 'all' || t.dataset.cat === cat); });
      bento.classList.toggle('flat', cat !== 'all');
    });
  });
})();

// the logo eases toward the pointer; a single loop runs only while it is still moving
(function () {
  var box = document.querySelector('.hero-mark'), tilt = box && box.querySelector('.tilt');
  if (!tilt || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var tx = 0, ty = 0, cx = 0, cy = 0, raf = 0;
  function frame() {
    cx += (tx - cx) * 0.1; cy += (ty - cy) * 0.1;
    tilt.style.setProperty('--ry', (cx * 26).toFixed(2) + 'deg');
    tilt.style.setProperty('--rx', (-cy * 16).toFixed(2) + 'deg');
    box.style.setProperty('--px', cx.toFixed(3));
    box.style.setProperty('--py', cy.toFixed(3));
    raf = (Math.abs(tx - cx) > 0.002 || Math.abs(ty - cy) > 0.002) ? requestAnimationFrame(frame) : 0;
  }
  function go() { if (!raf) raf = requestAnimationFrame(frame); }
  addEventListener('pointermove', function (e) {
    if (!innerWidth || !innerHeight) return;                     // never divide by a zero-size window
    var x = e.clientX / innerWidth - 0.5, y = e.clientY / innerHeight - 0.5;
    if (!isFinite(x) || !isFinite(y)) return;
    tx = Math.max(-0.5, Math.min(0.5, x)); ty = Math.max(-0.5, Math.min(0.5, y)); go();
  }, { passive: true });
  document.addEventListener('pointerleave', function () { tx = 0; ty = 0; go(); });
  document.addEventListener('visibilitychange', function () { if (document.hidden) { tx = 0; ty = 0; go(); } });
})();

// Tools dropdown: click to open, Escape or an outside click to close
(function () {
  var btn = document.getElementById('tools-btn'), panel = document.getElementById('tools-menu');
  if (!btn || !panel) return;
  function set(open) { panel.hidden = !open; btn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
  btn.addEventListener('click', function (e) { e.stopPropagation(); set(panel.hidden); });
  document.addEventListener('click', function (e) { if (!panel.hidden && !panel.contains(e.target) && e.target !== btn) set(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) { set(false); btn.focus(); } });
  panel.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
})();
