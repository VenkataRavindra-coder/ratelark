/* RateLark tool-to-tool handoff (Stage 4): carries a value from one calculator into the next
   via localStorage, using the same "fr:" key prefix app.js's own store already reads on load.
   Self-contained (app.js wraps its own state in an IIFE, so this can't reach into it directly). */
(function () {
  'use strict';
  function val(id) {
    var el = document.getElementById(id);
    var n = el ? parseFloat(el.value) : NaN;
    return isFinite(n) ? n : 0;
  }
  function put(key, value) {
    try { localStorage.setItem('fr:' + key, JSON.stringify(value)); } catch (e) {}
  }
  function round2(n) { return Math.round(n * 100) / 100; }
  function wire(id, run) {
    var b = document.getElementById(id);
    if (!b) return;
    b.addEventListener('click', function (e) {
      e.preventDefault();
      run();
      location.href = b.getAttribute('href');
    });
  }

  // Hourly rate -> Quote: same formula as hourly() in app.js
  wire('connect-to-quote', function () {
    var T = val('h-income'), E = val('h-exp');
    var tr = Math.min(Math.max(val('h-tax'), 0), 90) / 100;
    var off = Math.min(Math.max(val('h-off'), 0), 52), hpw = val('h-hours');
    var hours = (52 - off) * hpw, profit = T / (1 - tr), rev = profit + E;
    var rate = hours > 0 ? rev / hours : 0;
    put('f:q-rate', round2(rate));
  });

  // Quote -> Invoice: same formula as quote() in app.js, added as a new line item
  wire('connect-to-invoice', function () {
    var h = val('q-hours'), r = val('q-rate'), x = val('q-exp'), b = val('q-buf') / 100;
    var d = Math.min(Math.max(val('q-disc'), 0), 100) / 100;
    var labour = h * r, buf = labour * b, sub = labour + buf + x, disc = sub * d, total = sub - disc;
    var items;
    try { items = JSON.parse(localStorage.getItem('fr:items')); } catch (e) { items = null; }
    if (!Array.isArray(items)) items = [];
    var label = document.body.dataset.quoteLabel || 'Project quote';
    items.push({ d: label, q: 1, p: round2(total) });
    put('items', items);
  });

  // Invoice -> Late fee: carries the invoice's grand total (subtotal + tax) as the overdue amount
  wire('connect-to-latefee', function () {
    var tax = val('i-tax');
    var items;
    try { items = JSON.parse(localStorage.getItem('fr:items')); } catch (e) { items = null; }
    if (!Array.isArray(items)) items = [];
    var sub = items.reduce(function (s, it) { return s + (+it.q || 0) * (+it.p || 0); }, 0);
    var total = sub + sub * tax / 100;
    put('f:l-amt', round2(total));
  });
})();
