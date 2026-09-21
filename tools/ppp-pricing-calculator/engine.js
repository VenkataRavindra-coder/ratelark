/*
 * RateLark PPP Pricing Localizer: calculation engine (pure functions, no DOM).
 *
 *   price level (PLR)  = local prices relative to the US (US = 1.0), from World Bank data
 *   factor             = 1 - pass * (1 - PLR)        pass = how much of the gap you pass on (0..1)
 *   floor              = lowest allowed share of the US price (margin guard)
 *   cap                = never charge more than the US price
 *   local price        = US price * factor * exchange rate, then rounded ("friendly" ending by default)
 */
(function (root) {
  'use strict';

  var CATEGORIES = {            // starting assumptions for how much of the price gap to pass on
    saas:     { pass: 0.80 },
    course:   { pass: 0.85 },
    download: { pass: 0.85 },
    service:  { pass: 0.60 }
  };
  var REGIONS = ['emerging', 'south_asia', 'sea', 'latam', 'africa', 'europe', 'all'];
  var DEFAULTS = { price: 29, category: 'saas', region: 'emerging', pass: null, floor: 0.3, mode: 'charm', cap: true, custom: [] };

  var decCache = {};
  function decimalsOf(cur) {
    if (!(cur in decCache)) {
      try { decCache[cur] = new Intl.NumberFormat('en', { style: 'currency', currency: cur }).resolvedOptions().maximumFractionDigits; }
      catch (e) { decCache[cur] = 2; }
    }
    return decCache[cur];
  }
  function clamp(x, lo, hi) { return Math.min(hi, Math.max(lo, x)); }
  function roundTo(x, d) { var m = Math.pow(10, d); return Math.round(x * m) / m; }

  // Round a local price. dir 'up' never returns less than x (used so the floor is respected).
  function roundLocal(x, cur, mode, dir) {
    var dec = decimalsOf(cur);
    if (!isFinite(x) || x <= 0) return 0;
    var up = dir === 'up', v;
    if (mode === 'exact') {
      v = roundTo(x, dec);
      if (up && v < x) v = roundTo(v + Math.pow(10, -dec), dec);
      return v;
    }
    var digits = Math.floor(Math.log10(x)) + 1;
    if (mode === 'round') {
      var s = x >= 100 ? Math.pow(10, digits - 2) : (x >= 1 ? 1 : Math.pow(10, -dec));
      v = up ? Math.ceil(x / s) * s : Math.round(x / s) * s;
      return roundTo(v, dec);
    }
    // charm: friendly endings
    if (x < 100 && dec > 0) {                        // 8.40 -> 8.99, 11.43 -> 11.99
      var f = Math.floor(x);
      v = x <= f + 0.99 ? f + 0.99 : f + 1.99;
      return roundTo(v, 2);
    }
    var step = x < 100 ? 5 : x < 1000 ? 50 : x < 10000 ? 100 : 0;   // ends in 4/9, 49/99, 99
    if (step) return Math.ceil((x + 1) / step) * step - 1;
    var t = Math.pow(10, digits - 3);                // big numbers (IDR, VND, NGN): clean 3-digit prices
    return Math.ceil(x / t) * t;
  }

  function passFor(input) {
    if (typeof input.pass === 'number') return clamp(input.pass, 0, 1);
    return (CATEGORIES[input.category] || CATEGORIES.saas).pass;
  }

  function selectCountries(input, data) {
    var all = Object.keys(data.countries);
    if (input.region === 'custom') return input.custom.filter(function (c) { return data.countries[c]; });
    if (input.region === 'all') return all;
    return all.filter(function (c) { return data.countries[c].regions.indexOf(input.region) >= 0; });
  }

  function couponCode(iso, pct) { return 'PPP-' + iso + '-' + Math.max(0, pct); }

  function compute(rawInput, data) {
    var input = {}, k;
    for (k in DEFAULTS) input[k] = rawInput && rawInput[k] !== undefined ? rawInput[k] : DEFAULTS[k];
    input.price = Math.max(0, Number(input.price) || 0);
    input.floor = clamp(Number(input.floor) || 0, 0, 1);
    var pass = passFor(input), rows = [], flagged = 0;

    selectCountries(input, data).forEach(function (iso) {
      var c = data.countries[iso];
      var factor = 1 - pass * (1 - c.plr);
      if (input.cap) factor = Math.min(1, factor);
      var atFloor = factor < input.floor;
      factor = Math.max(factor, input.floor);
      var exact = input.price * factor * c.fx;
      var local = roundLocal(exact, c.cur, input.mode, 'up');
      var usd = local / c.fx;
      var minUsd = input.price * input.floor;
      if (usd < minUsd - 1e-9) { local = roundLocal(minUsd * c.fx, c.cur, input.mode, 'up'); usd = local / c.fx; atFloor = true; }
      if (input.cap && usd > input.price * 1.005) {   // rounding pushed us above the US price: fall back to the plain amount
        local = roundLocal(input.price * c.fx, c.cur, 'exact', 'nearest'); usd = local / c.fx;
      }
      var discount = input.price > 0 ? 1 - usd / input.price : 0;
      var pct = Math.round(discount * 100);
      if (atFloor) flagged++;
      rows.push({ iso: iso, cur: c.cur, plr: c.plr, factor: factor, exact: exact, local: local, usd: usd, discount: discount, pct: pct, atFloor: atFloor, coupon: couponCode(iso, pct) });
    });
    rows.sort(function (a, b) { return b.discount - a.discount; });

    var avg = rows.length ? rows.reduce(function (s, r) { return s + r.discount; }, 0) / rows.length : 0;
    return { input: input, pass: pass, rows: rows, avgDiscount: avg, avgPct: Math.round(avg * 100), flagged: flagged };
  }

  function toCSV(result, countryName) {
    var q = function (s) { s = String(s); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    var lines = ['country_code,country,currency,local_price,usd_equivalent,discount_percent,coupon_code'];
    result.rows.forEach(function (r) {
      lines.push([r.iso, q(countryName(r.iso)), r.cur, r.local, roundTo(r.usd, 2), r.pct, r.coupon].join(','));
    });
    return lines.join('\n');
  }

  function toCodes(result, countryName) {
    return result.rows.filter(function (r) { return r.pct > 0; })
      .map(function (r) { return r.coupon + '\t' + r.pct + '%\t' + countryName(r.iso); }).join('\n');
  }

  root.RLPPP = { CATEGORIES: CATEGORIES, REGIONS: REGIONS, DEFAULTS: DEFAULTS, compute: compute, roundLocal: roundLocal, decimalsOf: decimalsOf, toCSV: toCSV, toCodes: toCodes, selectCountries: selectCountries };
})(typeof window !== 'undefined' ? window : globalThis);
