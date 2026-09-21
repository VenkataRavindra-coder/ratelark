/* RateLark command palette: Cmd/Ctrl+K or "/" opens it. Data comes from /assets/tools-<lang>.json */
(function () {
  'use strict';
  var L = document.documentElement.lang || 'en';
  var data = null, loading = null, root = null, input = null, list = null, opener = null;
  var shown = [], sel = 0, isOpen = false;

  var norm = function (s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || '');

  function load() {
    if (data) return Promise.resolve(data);
    if (!loading) loading = fetch('/assets/tools-' + L + '.json', { credentials: 'omit' })
      .then(function (r) { return r.json(); })
      .catch(function () { return { ui: {}, tools: [], langs: [] }; })
      .then(function (j) { data = j; return j; });
    return loading;
  }

  function currentTool() {
    var m = location.pathname.match(/^\/[a-z]{2}\/([^/]+)\//);
    return m ? m[1] : 'hourly-rate';
  }

  function all() {
    var ui = data.ui || {}, out = [], t = currentTool();
    (data.tools || []).forEach(function (x) {
      out.push({ kind: 'tool', name: x.name, sub: x.desc, tag: x.cat, url: x.url, hay: norm([x.name, x.desc, x.cat, x.slug].join(' ')) });
    });
    (data.langs || []).forEach(function (g) {
      out.push({ kind: 'lang', name: g.name, sub: g.code.toUpperCase(), tag: ui.langs || 'Language', url: '/' + g.code + '/' + t + '/', hay: norm([g.name, g.code, ui.langs].join(' ')) });
    });
    out.push({ kind: 'page', name: ui.privacy || 'Privacy', sub: '', tag: '', url: '/privacy/', hay: norm(ui.privacy || 'privacy') });
    return out;
  }

  function rank(q) {
    var base = all();
    var toks = norm(q).split(/\s+/).filter(Boolean);
    if (!toks.length) return base;
    var res = [];
    base.forEach(function (it) {
      var s = 0, ok = true, nm = norm(it.name);
      toks.forEach(function (tk) {
        if (nm.indexOf(tk) === 0) s += 6;
        else if (nm.indexOf(tk) > 0) s += 4;
        else if (it.hay.indexOf(tk) >= 0) s += 2;
        else ok = false;
      });
      if (ok) res.push({ it: it, s: s + (it.kind === 'tool' ? 1 : 0) });
    });
    res.sort(function (a, b) { return b.s - a.s; });
    return res.map(function (r) { return r.it; });
  }

  function build() {
    root = document.createElement('div');
    root.className = 'pal'; root.hidden = true; root.dir = document.documentElement.dir || 'ltr';
    root.innerHTML =
      '<div class="pal-back" data-close></div>' +
      '<div class="pal-box" role="dialog" aria-modal="true">' +
      '<div class="pal-head"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>' +
      '<input class="pal-in" type="text" role="combobox" aria-expanded="true" aria-controls="pal-list" aria-autocomplete="list" autocomplete="off" autocapitalize="off" spellcheck="false">' +
      '<button type="button" class="pal-x" data-close>Esc</button></div>' +
      '<ul id="pal-list" class="pal-list" role="listbox"></ul></div>';
    document.body.appendChild(root);
    input = root.querySelector('.pal-in'); list = root.querySelector('.pal-list');
    root.addEventListener('click', function (e) { if (e.target.hasAttribute('data-close') || e.target.closest('[data-close]')) close(); });
    input.addEventListener('input', function () { sel = 0; paint(); });
    root.addEventListener('keydown', onKey);
    list.addEventListener('mousemove', function (e) {
      var li = e.target.closest('li[data-i]'); if (li && +li.dataset.i !== sel) { sel = +li.dataset.i; mark(); }
    });
    list.addEventListener('click', function (e) { var li = e.target.closest('li[data-i]'); if (li) go(+li.dataset.i); });
  }

  function paint() {
    var ui = data.ui || {};
    shown = rank(input.value);
    list.textContent = '';
    if (!shown.length) {
      var e = document.createElement('li'); e.className = 'pal-empty'; e.textContent = ui.none || 'No matches'; list.appendChild(e);
      input.removeAttribute('aria-activedescendant'); return;
    }
    shown.forEach(function (it, i) {
      var li = document.createElement('li'); li.id = 'pal-o' + i; li.setAttribute('role', 'option'); li.dataset.i = i;
      var a = document.createElement('span'); a.className = 'pal-t';
      var n = document.createElement('b'); n.textContent = it.name; a.appendChild(n);
      if (it.sub && it.kind === 'tool') { var d = document.createElement('small'); d.textContent = it.sub; a.appendChild(d); }
      li.appendChild(a);
      if (it.tag) { var g = document.createElement('span'); g.className = 'pal-g'; g.textContent = it.tag; li.appendChild(g); }
      list.appendChild(li);
    });
    mark();
  }

  function mark() {
    var opts = list.querySelectorAll('li[data-i]');
    opts.forEach(function (li, i) { li.setAttribute('aria-selected', i === sel ? 'true' : 'false'); });
    var cur = opts[sel];
    if (cur) { input.setAttribute('aria-activedescendant', cur.id); cur.scrollIntoView({ block: 'nearest' }); }
  }

  function go(i) { var it = shown[i]; if (it) location.href = it.url; }

  function onKey(e) {
    if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); if (shown.length) { sel = (sel + 1) % shown.length; mark(); } }
    else if (e.key === 'ArrowUp') { e.preventDefault(); if (shown.length) { sel = (sel - 1 + shown.length) % shown.length; mark(); } }
    else if (e.key === 'Home' && e.target === input && !input.value) { sel = 0; mark(); }
    else if (e.key === 'Enter') { e.preventDefault(); go(sel); }
    else if (e.key === 'Tab') { e.preventDefault(); (document.activeElement === input ? root.querySelector('.pal-x') : input).focus(); }
  }

  function open() {
    if (isOpen) return; isOpen = true; opener = document.activeElement;
    load().then(function () {
      if (!isOpen) return;
      if (!root) build();
      var ui = data.ui || {};
      input.placeholder = ui.ph || 'Search tools';
      root.querySelector('[role=dialog]').setAttribute('aria-label', ui.ph || 'Search tools');
      root.hidden = false; document.documentElement.classList.add('pal-open');
      input.value = ''; sel = 0; paint(); input.focus();
    });
  }
  function close() {
    if (!isOpen) return; isOpen = false;
    if (root) root.hidden = true;
    document.documentElement.classList.remove('pal-open');
    if (opener && opener.focus) opener.focus();
  }

  document.addEventListener('keydown', function (e) {
    var k = (e.key || '').toLowerCase();
    if ((e.metaKey || e.ctrlKey) && k === 'k') { e.preventDefault(); isOpen ? close() : open(); return; }
    if (k === '/' && !e.metaKey && !e.ctrlKey && !e.altKey && !isOpen) {
      var t = e.target, tag = t && t.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (t && t.isContentEditable)) return;
      e.preventDefault(); open();
    }
  });
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-palette]');
    if (b) { e.preventDefault(); open(); }
  });
  document.querySelectorAll('[data-palette] kbd').forEach(function (k) { k.textContent = isMac ? '⌘K' : 'Ctrl K'; });
  window.addEventListener('pageshow', function () { load(); });
})();
