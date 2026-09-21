/* RateLark PPP Pricing Localizer: interface. Uses window.RLPPP (engine.js) and window.LZString (lz-string). */
(function () {
  'use strict';
  var root = document.getElementById('tool-ppp-pricing-calculator');
  if (!root || !window.RLPPP) return;
  var E = window.RLPPP, LZ = window.LZString;
  var lang = document.documentElement.lang || 'en';
  var S = {};
  try { S = JSON.parse(root.getAttribute('data-i18n') || '{}'); } catch (e) {}
  var STORE = 'rl:ppp:v1';
  var $ = function (id) { return document.getElementById(id); };
  var el = {
    price: $('ppp-price'), cat: $('ppp-cat'), reg: $('ppp-region'), customWrap: $('ppp-custom-wrap'), custom: $('ppp-custom'),
    pass: $('ppp-pass'), passOut: $('ppp-pass-out'), floor: $('ppp-floor'), mode: $('ppp-mode'), cap: $('ppp-cap'),
    resLbl: $('ppp-res-l'), resBig: $('ppp-res-big'), stats: $('ppp-stats'), sum: $('ppp-sum'), sum2: $('ppp-sum2'),
    body: $('ppp-tbody'), assume: $('ppp-assume'), adv: $('ppp-adv'), toast: $('ppp-toast'), table: $('ppp-table'),
    share: $('ppp-share'), csv: $('ppp-csv'), codes: $('ppp-codes'), reset: $('ppp-reset'), fallback: $('ppp-fallback')
  };
  var data = null, state = null, toastT = null, saveT = null;
  var locale = lang + '-u-nu-latn';

  function fmt(str, vars) { return String(str || '').replace(/\{(\w+)\}/g, function (m, k) { return k in vars ? vars[k] : m; }); }
  var RTL = document.documentElement.dir === 'rtl';
  function iso(str) { return RTL ? '\u2066' + str + '\u2069' : str; }   // keep amounts intact inside right-to-left text
  function money(v, cur) {
    var dec = E.decimalsOf(cur);
    var base = { style: 'currency', currency: cur, minimumFractionDigits: Math.abs(v - Math.round(v)) < 1e-9 ? 0 : dec, maximumFractionDigits: dec };
    try {
      var out = new Intl.NumberFormat(locale, base).format(v);
      if (/^[A-Z]{3}[\s\u00a0]/.test(out) || /[\s\u00a0][A-Z]{3}$/.test(out)) {      // no symbol in this locale: try the short one
        base.currencyDisplay = 'narrowSymbol';
        out = new Intl.NumberFormat(locale, base).format(v);
      }
      return iso(out);
    } catch (e) { return iso(cur + ' ' + v); }
  }
  var names = null;
  function countryName(iso) {
    if (names === null) { try { names = new Intl.DisplayNames([lang], { type: 'region' }); } catch (e) { names = false; } }
    try { return (names && names.of(iso)) || iso; } catch (e) { return iso; }
  }

  // ---------- state ----------
  function defaults() { return { p: 29, c: 'saas', r: 'emerging', cs: [], pt: null, f: 30, m: 'charm', cap: true }; }
  function clean(x) {
    var d = defaults(), s = {};
    x = x && typeof x === 'object' ? x : {};
    s.p = isFinite(+x.p) && +x.p >= 0 && +x.p < 1e9 ? +x.p : d.p;
    s.c = E.CATEGORIES[x.c] ? x.c : d.c;
    s.r = E.REGIONS.indexOf(x.r) >= 0 || x.r === 'custom' ? x.r : d.r;
    s.cs = Array.isArray(x.cs) ? x.cs.filter(function (c) { return typeof c === 'string' && /^[A-Z]{2}$/.test(c); }).slice(0, 80) : [];
    s.pt = typeof x.pt === 'number' && x.pt >= 0 && x.pt <= 1 ? x.pt : null;
    s.f = isFinite(+x.f) ? Math.min(100, Math.max(0, +x.f)) : d.f;
    s.m = ['charm', 'round', 'exact'].indexOf(x.m) >= 0 ? x.m : d.m;
    s.cap = x.cap === false ? false : true;
    return s;
  }
  function fromHash() {
    var m = /[#&]s=([^&]+)/.exec(location.hash);
    if (!m || !LZ) return null;
    try { var j = LZ.decompressFromEncodedURIComponent(m[1]); return j ? clean(JSON.parse(j)) : null; } catch (e) { return null; }
  }
  function fromStore() { try { var j = localStorage.getItem(STORE); return j ? clean(JSON.parse(j)) : null; } catch (e) { return null; } }
  function persist() {
    clearTimeout(saveT);
    saveT = setTimeout(function () {
      var json = JSON.stringify(state);
      try { localStorage.setItem(STORE, json); } catch (e) {}
      if (LZ) { try { history.replaceState(null, '', '#s=' + LZ.compressToEncodedURIComponent(json)); } catch (e) {} }
    }, 150);
  }

  function input() {
    return { price: state.p, category: state.c, region: state.r, custom: state.cs, pass: state.pt, floor: state.f / 100, mode: state.m, cap: state.cap };
  }

  // ---------- controls -> state ----------
  function passNow() { return state.pt !== null ? state.pt : E.CATEGORIES[state.c].pass; }
  function writeControls() {
    el.price.value = state.p; el.cat.value = state.c; el.reg.value = state.r;
    el.pass.value = Math.round(passNow() * 100); el.passOut.textContent = Math.round(passNow() * 100) + '%';
    el.floor.value = state.f; el.mode.value = state.m; el.cap.checked = state.cap;
    el.customWrap.hidden = state.r !== 'custom';
    [].forEach.call(el.custom.querySelectorAll('input'), function (cb) { cb.checked = state.cs.indexOf(cb.value) >= 0; });
  }
  function readControls() {
    var p = parseFloat(el.price.value);
    state.p = isFinite(p) && p >= 0 ? p : 0;
    state.c = el.cat.value; state.r = el.reg.value;
    state.f = Math.min(100, Math.max(0, parseFloat(el.floor.value) || 0));
    state.m = el.mode.value; state.cap = el.cap.checked;
    state.cs = [].filter.call(el.custom.querySelectorAll('input'), function (cb) { return cb.checked; }).map(function (cb) { return cb.value; });
  }

  // ---------- render ----------
  var FEATURED = ['IN', 'BR', 'ID', 'NG', 'PH', 'MX', 'ZA', 'PK', 'VN'];
  function cell(tag, text, cls) { var c = document.createElement(tag); if (cls) c.className = cls; c.textContent = text; return c; }
  function render() {
    if (!data) return;
    var r = E.compute(input(), data), price = state.p;
    var usdFmt = function (v) { return money(v, 'USD'); };
    el.body.textContent = '';
    if (!r.rows.length) {
      el.resLbl.textContent = fmt(S.res_l, { country: '—' }); el.resBig.textContent = '—';
      el.sum.textContent = S.sum_empty; el.sum2.textContent = ''; el.stats.textContent = '';
      el.assume.hidden = true; return;
    }
    var f = r.rows[0];
    for (var i = 0; i < FEATURED.length; i++) {
      var hit = r.rows.filter(function (x) { return x.iso === FEATURED[i]; })[0];
      if (hit) { f = hit; break; }
    }
    el.resLbl.textContent = fmt(S.res_l, { country: countryName(f.iso) });
    el.resBig.textContent = money(f.local, f.cur);
    el.sum.textContent = f.pct > 0
      ? fmt(S.sum, { price: usdFmt(price), country: countryName(f.iso), local: money(f.local, f.cur), usd: usdFmt(f.usd), pct: f.pct + '%' })
      : fmt(S.sum_same, { country: countryName(f.iso), local: money(f.local, f.cur) });
    el.sum2.textContent = r.rows.length > 1 && r.avgPct > 0 ? fmt(S.sum_more, { n: r.rows.length, avg: r.avgPct + '%' }) : '';

    var top = r.rows[0];
    var stats = [[S.st_avg, r.avgPct + '%'], [S.st_top, top.pct + '% (' + countryName(top.iso) + ')'], [S.st_n, String(r.rows.length)], [S.st_floor, r.flagged ? String(r.flagged) : S.none_txt]];
    el.stats.textContent = '';
    stats.forEach(function (s) {
      var d = document.createElement('div'); var dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = s[0]; dd.textContent = s[1]; d.appendChild(dt); d.appendChild(dd); el.stats.appendChild(d);
    });

    r.rows.forEach(function (x) {
      var tr = document.createElement('tr');
      var c1 = cell('td', countryName(x.iso), 'pp-c'); if (x.atFloor) { var t = document.createElement('small'); t.className = 'pp-tag'; t.textContent = S.tag_floor; c1.appendChild(t); }
      tr.appendChild(c1);
      tr.appendChild(cell('td', money(x.local, x.cur), 'pp-p'));
      tr.appendChild(cell('td', usdFmt(x.usd), 'pp-u'));
      tr.appendChild(cell('td', (x.pct > 0 ? '−' : x.pct < 0 ? '+' : '') + Math.abs(x.pct) + '%', 'pp-d'));
      tr.appendChild(cell('td', x.coupon, 'pp-k'));
      el.body.appendChild(tr);
    });
    var pl = data.priceLevel && data.priceLevel.lastUpdated ? '' : '';
    var years = r.rows.map(function (x) { return data.countries[x.iso].year; });
    var yr = Math.max.apply(null, years);
    el.assume.textContent = fmt(S.assume, { plYear: yr, fxDate: data.fx.date, pass: Math.round(r.pass * 100) }) + ' ';
    var a = document.createElement('a'); a.href = '#ppp-adv'; a.textContent = S.assume_link;
    a.addEventListener('click', function () { el.adv.open = true; });
    el.assume.appendChild(a); el.assume.hidden = false;
    lastResult = r;
  }
  var lastResult = null;

  // ---------- actions ----------
  function say(msg) {
    el.toast.textContent = msg; clearTimeout(toastT);
    toastT = setTimeout(function () { el.toast.textContent = ''; }, 2600);
  }
  function copyText(text, okMsg) {
    var done = function () { say(okMsg); };
    var fallback = function () {
      el.fallback.hidden = false; el.fallback.value = text; el.fallback.focus(); el.fallback.select();
      var ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
      if (ok) { el.fallback.hidden = true; done(); } else { say(S.t_fail); }
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
  }
  function shareLink() {
    var json = JSON.stringify(state);
    var url = location.href.split('#')[0] + (LZ ? '#s=' + LZ.compressToEncodedURIComponent(json) : '');
    copyText(url, S.t_copied);
  }
  function downloadCsv() {
    if (!lastResult) return;
    var csv = '﻿' + E.toCSV(lastResult, countryName);
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    a.download = 'ratelark-ppp-prices.csv'; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500); say(S.t_csv);
  }

  // ---------- wiring ----------
  function buildCustomList() {
    var isos = Object.keys(data.countries).sort(function (a, b) { return countryName(a).localeCompare(countryName(b), lang); });
    el.custom.textContent = '';
    isos.forEach(function (iso) {
      var lab = document.createElement('label'); lab.className = 'pp-cb';
      var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = iso;
      var sp = document.createElement('span'); sp.textContent = countryName(iso);
      lab.appendChild(cb); lab.appendChild(sp); el.custom.appendChild(lab);
    });
  }
  function onChange(e) {
    var t = e && e.target;
    if (t === el.cat) state.pt = null;                       // a new category brings its own preset
    readControls();
    if (t === el.pass) { state.pt = el.pass.value / 100; el.passOut.textContent = el.pass.value + '%'; }
    if (state.r === 'custom' && !state.cs.length && t === el.reg) { state.cs = ['IN', 'BR']; }
    writeControls(); persist(); render();
  }
  function start() {
    state = fromHash() || fromStore() || defaults();
    buildCustomList(); writeControls(); render();
    ['input', 'change'].forEach(function (ev) { root.addEventListener(ev, function (e) { if (e.target.closest && e.target.closest('[data-p]')) onChange(e); }); });
    el.share.addEventListener('click', shareLink);
    el.csv.addEventListener('click', downloadCsv);
    el.codes.addEventListener('click', function () { if (lastResult) copyText(E.toCodes(lastResult, countryName), S.t_copied); });
    el.reset.addEventListener('click', function () { state = defaults(); writeControls(); persist(); render(); say(S.t_reset); });
    window.addEventListener('hashchange', function () { var h = fromHash(); if (h) { state = h; writeControls(); render(); } });
    persist();
  }

  fetch('/assets/data/ppp.json', { credentials: 'omit' }).then(function (r) { return r.json(); }).then(function (j) { data = j; start(); })
    .catch(function () { el.sum.textContent = S.t_fail; });
})();
