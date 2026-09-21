#!/usr/bin/env python3
"""
Build the multi-page RateLark site from hourkit.html.

    python3 build.py https://yourdomain.com

Needs Python 3.8+ and BeautifulSoup:   pip install beautifulsoup4
Output goes to ./site  (63 pages: 9 languages x 7 tools, plus sitemap, robots, 404).
Run it again with your real domain BEFORE you deploy, so canonical links and
the sitemap point at the right place.
"""
import logo, bgart, copy, datetime, hashlib, html, json, os, re, shutil, sys
from bs4 import BeautifulSoup

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'https://YOUR-DOMAIN.com').rstrip('/')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'site')

LANGS = [('en','English','en','en_US'),('es','Español','es','es_ES'),('pt','Português','pt-BR','pt_BR'),
         ('fr','Français','fr','fr_FR'),('de','Deutsch','de','de_DE'),('hi','हिन्दी','hi','hi_IN'),
         ('ar','العربية','ar','ar_AE'),('zh','中文','zh-Hans','zh_CN'),('id','Bahasa Indonesia','id','id_ID')]
REG = json.load(open(os.path.join(HERE, 'tools.json'), encoding='utf-8'))
TOOLS = [t['slug'] for t in REG]
PLUGINS = {}    # slug -> {lang: strings}; plugin tools live in tools/<slug>/ (tool.json, engine.js, ui.js, tool.css)
for _t in REG:
    if _t.get('plugin'):
        PLUGINS[_t['slug']] = json.load(open(os.path.join(HERE, 'tools', _t['slug'], 'tool.json'), encoding='utf-8'))['i18n']
UI = {
 'en': dict(ph='Search tools, languages\u2026', none='No matches', langs='Language', privacy='Privacy', search='Search', all='All tools'),
 'es': dict(ph='Buscar herramientas, idiomas\u2026', none='Sin resultados', langs='Idioma', privacy='Privacidad', search='Buscar', all='Todas'),
 'pt': dict(ph='Buscar ferramentas, idiomas\u2026', none='Sem resultados', langs='Idioma', privacy='Privacidade', search='Buscar', all='Todas'),
 'fr': dict(ph='Rechercher un outil, une langue\u2026', none='Aucun r\u00e9sultat', langs='Langue', privacy='Confidentialit\u00e9', search='Rechercher', all='Tous les outils'),
 'de': dict(ph='Tools, Sprachen suchen\u2026', none='Keine Treffer', langs='Sprache', privacy='Datenschutz', search='Suchen', all='Alle Tools'),
 'hi': dict(ph='\u091f\u0942\u0932 \u092f\u093e \u092d\u093e\u0937\u093e \u0916\u094b\u091c\u0947\u0902\u2026', none='\u0915\u094b\u0908 \u092a\u0930\u093f\u0923\u093e\u092e \u0928\u0939\u0940\u0902', langs='\u092d\u093e\u0937\u093e', privacy='\u0917\u094b\u092a\u0928\u0940\u092f\u0924\u093e', search='\u0916\u094b\u091c\u0947\u0902', all='\u0938\u092d\u0940 \u091f\u0942\u0932'),
 'ar': dict(ph='\u0627\u0628\u062d\u062b \u0639\u0646 \u0623\u062f\u0627\u0629 \u0623\u0648 \u0644\u063a\u0629\u2026', none='\u0644\u0627 \u062a\u0648\u062c\u062f \u0646\u062a\u0627\u0626\u062c', langs='\u0627\u0644\u0644\u063a\u0629', privacy='\u0627\u0644\u062e\u0635\u0648\u0635\u064a\u0629', search='\u0628\u062d\u062b', all='\u0643\u0644 \u0627\u0644\u0623\u062f\u0648\u0627\u062a'),
 'zh': dict(ph='\u641c\u7d22\u5de5\u5177\u6216\u8bed\u8a00\u2026', none='\u65e0\u7ed3\u679c', langs='\u8bed\u8a00', privacy='\u9690\u79c1', search='\u641c\u7d22', all='\u5168\u90e8\u5de5\u5177'),
 'id': dict(ph='Cari alat atau bahasa\u2026', none='Tidak ada hasil', langs='Bahasa', privacy='Privasi', search='Cari', all='Semua alat'),
}
CATS = {
 'price':   {'en': 'Price your work', 'es': 'Fija tu precio', 'pt': 'Precifique seu trabalho', 'fr': 'Fixer vos prix', 'de': 'Preise festlegen', 'hi': '\u0915\u093e\u092e \u0915\u0940 \u0915\u0940\u092e\u0924 \u0924\u092f \u0915\u0930\u0947\u0902', 'ar': '\u0633\u0639\u0651\u0631 \u0639\u0645\u0644\u0643', 'zh': '\u4e3a\u5de5\u4f5c\u5b9a\u4ef7', 'id': 'Tentukan harga kerja'},
 'getpaid': {'en': 'Get paid', 'es': 'Cobra', 'pt': 'Receba', 'fr': 'Se faire payer', 'de': 'Bezahlt werden', 'hi': '\u092d\u0941\u0917\u0924\u093e\u0928 \u092a\u093e\u090f\u0901', 'ar': '\u0627\u062d\u0635\u0644 \u0639\u0644\u0649 \u0623\u062c\u0631\u0643', 'zh': '\u6536\u6b3e', 'id': 'Terima pembayaran'},
 'global':  {'en': 'Sell globally', 'es': 'Vende globalmente', 'pt': 'Venda globalmente', 'fr': "Vendre \u00e0 l'international", 'de': 'Weltweit verkaufen', 'hi': '\u0926\u0941\u0928\u093f\u092f\u093e \u092d\u0930 \u092e\u0947\u0902 \u092c\u0947\u091a\u0947\u0902', 'ar': '\u0628\u0639 \u0639\u0627\u0644\u0645\u064a\u064b\u0627', 'zh': '\u5168\u7403\u9500\u552e', 'id': 'Jual ke seluruh dunia'},
 'tax':     {'en': 'Tax & money', 'es': 'Impuestos y dinero', 'pt': 'Impostos e dinheiro', 'fr': 'Imp\u00f4ts et argent', 'de': 'Steuern & Geld', 'hi': '\u0915\u0930 \u0914\u0930 \u092a\u0948\u0938\u093e', 'ar': '\u0627\u0644\u0636\u0631\u0627\u0626\u0628 \u0648\u0627\u0644\u0645\u0627\u0644', 'zh': '\u7a0e\u52a1\u4e0e\u8d44\u91d1', 'id': 'Pajak & uang'},
}
ICONS = {
 'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 'file': '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',
 'receipt': '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
 'percent': '<path d="M19 5L5 19"/><circle cx="7.5" cy="7.5" r="2"/><circle cx="16.5" cy="16.5" r="2"/>',
 'repeat': '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>',
 'alarm': '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2"/><path d="M5 3L2 6M22 6l-3-3"/>',
 'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18"/>',
 'landmark': '<path d="M3 21h18"/><path d="M5 21V10M9 21V10M15 21V10M19 21V10"/><path d="M2 10l10-7 10 7"/>',
}
CONTACT_EMAIL = 'hello@ratelark.com'
CONTACT_LABEL = {'en': 'Contact', 'es': 'Contacto', 'pt': 'Contato', 'fr': 'Contact', 'de': 'Kontakt', 'hi': '\u0938\u0902\u092a\u0930\u094d\u0915',
                 'ar': '\u0627\u062a\u0635\u0644 \u0628\u0646\u0627', 'zh': '\u8054\u7cfb\u6211\u4eec', 'id': 'Kontak'}
def icon_svg(name, size=22):
    return ('<svg viewBox="0 0 24 24" width="%d" height="%d" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % (size, size, ICONS.get(name, ICONS['file'])))
TODAY = datetime.date.today().isoformat()
TODAY = datetime.date.today().isoformat()
SEL = ('.tab,.cur>span,h1,h2,.head p,.l,.hint,.mini,dt,.lbl,.note,summary,'
       '.about p,details p,.btn,.suf,option,footer p')

src = open(os.path.join(HERE, 'hourkit.html'), encoding='utf-8').read()
soup = BeautifulSoup(src, 'html.parser')

css = soup.find('style').get_text()
main_js = i18n_js = None
for sc in soup.find_all('script'):
    if sc.get('type') == 'application/ld+json':
        continue
    txt = sc.get_text()
    if txt.lstrip().startswith('window.FR_EN'):
        i18n_js = txt
    else:
        main_js = txt
assert css and main_js and i18n_js, 'could not find css/js in hourkit.html'

m = re.search(r'window\.FR_EN=(\[.*?\]);window\.FR_L=(\{.*\});', i18n_js, re.S)
EN = json.loads(m.group(1)); L = json.loads(m.group(2))
MAPS = {'en': {}}
for code, *_ in LANGS[1:]:
    MAPS[code] = {k: v for k, v in zip(EN, L[code]) if v}

tm = re.search(r"const TITLES=\{(.*?)\};", main_js, re.S)
TITLES = dict(re.findall(r"'([^']+)':'((?:[^'\\]|\\.)*)'", tm.group(1)))

header = soup.find('header', class_='top')
nav_src = soup.find('nav', class_='tabs')
footer = soup.find('footer')
main = soup.find('main')
sections = {s['id'][5:]: s for s in main.find_all('section', recursive=False)}
share = main.find('div', class_='share')
fallback = main.find('textarea', id='fallback')
tab_labels = {b['data-tool']: b.get_text().strip() for b in nav_src.find_all('button')}
fonts = soup.find('link', href=re.compile('fonts.googleapis.com/css2'))['href']
assert set(sections) == set(t for t in TOOLS if t not in PLUGINS), sections.keys()


def translate(root, mp):
    """Same rule the browser script uses: swap the text of matching leaf elements."""
    if not mp:
        return
    for el in root.select(SEL):
        if el.has_attr('data-dyn') or el.find(True):
            continue
        if el.find_parent(class_='doc') or el.find_parent(id='cur') or el.find_parent(id='lang'):
            continue
        key = el.get_text().strip()
        if key in mp:
            el.string = mp[key]
    for el in root.select('[placeholder]'):
        if not el.has_attr('data-dyn') and el['placeholder'] in mp:
            el['placeholder'] = mp[el['placeholder']]


def tr(text, lang):
    return MAPS[lang].get(text, text)


def alternates(tool):
    out = []
    for code, _, hl, _ in LANGS:
        out.append('<link rel="alternate" hreflang="%s" href="%s/%s/%s/">' % (hl, BASE, code, tool))
    out.append('<link rel="alternate" hreflang="x-default" href="%s/en/%s/">' % (BASE, tool))
    return '\n'.join(out)


def tool_name(lang, slug):
    if slug in PLUGINS:
        return PLUGINS[slug][lang]['name']
    return MAPS[lang].get(tab_labels[slug], tab_labels[slug])


def tool_desc(lang, slug):
    if slug in PLUGINS:
        return PLUGINS[slug][lang]['desc']
    d = sections[slug].find(class_='head').find('p').get_text().strip()
    return MAPS[lang].get(d, d)


def render_ppp(lang, T):
    """Server-side markup for the PPP Pricing Localizer (the interface script fills in the numbers)."""
    q = lambda x: html.escape(x, quote=True)
    ui_keys = ['res_l', 'st_avg', 'st_top', 'st_n', 'st_floor', 'none_txt', 'sum', 'sum_same', 'sum_more', 'sum_empty', 'tag_floor',
               't_copied', 't_csv', 't_reset', 't_fail', 'assume', 'assume_link']
    blob = q(json.dumps({k: T[k] for k in ui_keys}, ensure_ascii=False))
    opt = lambda pairs: ''.join('<option value="%s">%s</option>' % (v, q(l)) for v, l in pairs)
    cats = opt([(k, T['cat_' + k]) for k in ('saas', 'course', 'download', 'service')])
    regs = opt([(k, T['reg_' + k]) for k in ('emerging', 'south_asia', 'sea', 'latam', 'africa', 'europe', 'all', 'custom')])
    modes = opt([(k, T['mode_' + k]) for k in ('charm', 'round', 'exact')])
    ths = ''.join('<th scope="col">%s</th>' % q(T[k]) for k in ('th_country', 'th_price', 'th_usd', 'th_disc', 'th_code'))
    return f"""<section id="tool-ppp-pricing-calculator" data-i18n="{blob}">
<div class="head">
<h1>{q(T['h1'])}</h1>
<p>{q(T['lead'])}</p>
</div>
<div class="layout">
<div class="side">
<div aria-live="polite" class="result">
<div class="lbl" id="ppp-res-l">&nbsp;</div>
<div class="big"><span id="ppp-res-big">—</span></div>
</div>
<dl class="stats" id="ppp-stats"></dl>
</div>
<div class="inputs sheet">
<label class="field"><span class="l">{q(T['price_l'])}</span>
<div class="inp"><span class="pre">$</span><input data-p id="ppp-price" inputmode="decimal" min="0" step="any" type="number" value="29"></div>
<span class="hint">{q(T['price_h'])}</span></label>
<label class="field"><span class="l">{q(T['cat_l'])}</span><select class="ctl" data-p id="ppp-cat">{cats}</select></label>
<label class="field"><span class="l">{q(T['reg_l'])}</span><select class="ctl" data-p id="ppp-region">{regs}</select></label>
<div class="field" id="ppp-custom-wrap" hidden><span class="l">{q(T['custom_l'])}</span><div class="pp-custom" id="ppp-custom" data-p></div></div>
</div>
</div>
<div class="sheet" id="ppp-results">
<p class="pp-sum" id="ppp-sum" aria-live="polite"></p>
<p class="pp-sum2" id="ppp-sum2"></p>
<h2>{q(T['tbl_h'])}</h2>
<div class="pp-wrap"><table class="pp-table" id="ppp-table"><thead><tr>{ths}</tr></thead><tbody id="ppp-tbody"></tbody></table></div>
<div class="pp-actions">
<button class="btn" id="ppp-share" type="button">{q(T['btn_share'])}</button>
<button class="btn alt" id="ppp-csv" type="button">{q(T['btn_csv'])}</button>
<button class="btn alt" id="ppp-codes" type="button">{q(T['btn_codes'])}</button>
<button class="btn alt" id="ppp-reset" type="button">{q(T['btn_reset'])}</button>
<span id="ppp-toast" role="status"></span>
</div>
<p class="pp-note" id="ppp-assume" hidden></p>
<p class="pp-note">{q(T['codes_note'])}</p>
<textarea aria-label="Text to copy" class="ctl" hidden id="ppp-fallback" readonly rows="3"></textarea>
</div>
<details class="sheet" id="ppp-adv">
<summary>{q(T['adv_t'])}</summary>
<div class="inputs">
<label class="field"><span class="l">{q(T['adv_pass_l'])}</span>
<div class="pp-inline"><input class="pp-range" data-p id="ppp-pass" max="100" min="0" step="5" type="range" value="80"><output id="ppp-pass-out" for="ppp-pass">80%</output></div>
<span class="hint">{q(T['adv_pass_h'])}</span></label>
<label class="field"><span class="l">{q(T['adv_floor_l'])}</span>
<div class="inp"><input data-p id="ppp-floor" inputmode="decimal" max="100" min="0" step="5" type="number" value="30"><span class="suf">%</span></div>
<span class="hint">{q(T['adv_floor_h'])}</span></label>
<label class="field"><span class="l">{q(T['adv_mode_l'])}</span><select class="ctl" data-p id="ppp-mode">{modes}</select></label>
<label class="pp-check"><input data-p id="ppp-cap" type="checkbox" checked><span>{q(T['adv_cap_l'])}</span></label>
<p class="pp-note">{q(T['adv_data'])}</p>
</div>
</details>
<div class="about sheet">
<h2>{q(T['about_h'])}</h2>
<p>{q(T['about_p'])}</p>
<details><summary>{q(T['faq1_q'])}</summary><p>{q(T['faq1_a'])}</p></details>
<details><summary>{q(T['faq2_q'])}</summary><p>{q(T['faq2_a'])}</p></details>
</div>
</section>"""


PLUGIN_RENDER = {'ppp-pricing-calculator': render_ppp}


def plugin_parts(lang, tool):
    T = PLUGINS[tool][lang]
    sec = BeautifulSoup(PLUGIN_RENDER[tool](lang, T), 'html.parser')
    faq = [{'@type': 'Question', 'name': T[k + '_q'], 'acceptedAnswer': {'@type': 'Answer', 'text': T[k + '_a']}} for k in ('faq1', 'faq2')]
    return sec, BeautifulSoup('', 'html.parser'), BeautifulSoup('', 'html.parser'), T['desc'], T['title'] + ' | RateLark', faq


def build_page(lang, tool):
    mp = MAPS[lang]
    name, hl, locale = next((n, h, l) for c, n, h, l in LANGS if c == lang)
    dirn = 'rtl' if lang == 'ar' else 'ltr'

    hdr = copy.copy(header)
    hdr.find('a', class_='brand')['href'] = '/'
    _brand = hdr.find('a', class_='brand')
    for _n in list(_brand.contents):
        if isinstance(_n, str):
            _n.extract()
    _brand.append(BeautifulSoup('<span class="wm">Rate<span class="lk">Lark</span></span>', 'html.parser'))
    opt = hdr.find('select', id='lang').find('option', value=lang)
    opt['selected'] = 'selected'
    translate(hdr, mp)
    ui = UI[lang]
    kb = BeautifulSoup('<button type="button" class="kbtn" data-palette aria-label="%s"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg><span class="kt">%s</span><kbd>Ctrl K</kbd></button>' % (ui['search'], ui['search']), 'html.parser')
    hdr.find('div', class_='pick').insert(0, kb)

    nav = BeautifulSoup('<nav class="tabs" aria-label="Freelancer tools"></nav>', 'html.parser').nav
    home_tab = BeautifulSoup('<a class="tab tab-home" href="/#tools"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg><span>%s</span></a>' % ui['all'], 'html.parser')
    nav.append(home_tab)
    for t in TOOLS:
        a = BeautifulSoup('<a class="tab"></a>', 'html.parser').a
        a['id'] = 'tab-' + t
        a['href'] = '../%s/' % t
        if t == tool:
            a['aria-current'] = 'page'
        a.string = tool_name(lang, t)
        nav.append(a)

    if tool in PLUGINS:
        sec, sh, fb, description, title, faq = plugin_parts(lang, tool)
        cur = hdr.find('select', id='cur')
        if cur is not None and cur.find_parent('label') is not None:
            cur.find_parent('label').decompose()          # the currency picker belongs to the calculators that use it
    else:
        sec = copy.copy(sections[tool])
        for attr in ('hidden', 'role', 'aria-labelledby'):
            if sec.has_attr(attr):
                del sec[attr]
        translate(sec, mp)
        desc_el = sec.find(class_='head').find('p')
        description = desc_el.get_text().strip()

        sh = copy.copy(share); translate(sh, mp)
        fb = copy.copy(fallback)
    ft = copy.copy(footer); translate(ft, mp)
    langs_nav = BeautifulSoup('<nav class="langs" aria-label="Languages"></nav>', 'html.parser').nav
    for code, nm, h, _ in LANGS:
        a = BeautifulSoup('<a></a>', 'html.parser').a
        a['href'] = '../../%s/%s/' % (code, tool)
        a['hreflang'] = h
        a['lang'] = code
        if code == lang:
            a['aria-current'] = 'true'
        a.string = nm
        langs_nav.append(a)
    ft.insert(0, langs_nav)
    ft.append(BeautifulSoup('<p><a href="/privacy/">Privacy</a> &middot; <a href="mailto:%s">%s</a></p>' % (CONTACT_EMAIL, CONTACT_LABEL[lang]), 'html.parser'))

    if tool not in PLUGINS:
        title = tr(TITLES[tool], lang)
        faq = []
        for d in sec.find_all('details'):
            q = d.find('summary'); a = d.find('p')
            if q and a:
                faq.append({'@type': 'Question', 'name': q.get_text().strip(),
                            'acceptedAnswer': {'@type': 'Answer', 'text': a.get_text().strip()}})
    url = '%s/%s/%s/' % (BASE, lang, tool)
    ld = [{'@context': 'https://schema.org', '@type': 'WebApplication', 'name': title.split(' | ')[0],
           'url': url, 'inLanguage': hl, 'applicationCategory': 'BusinessApplication',
           'operatingSystem': 'Any', 'description': description,
           'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}}]
    if faq:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': faq})

    if tool in PLUGINS:
        scripts = ('<script src="../../assets/lz-string.min.js?v={0}" defer></script>\n'
                   '<script src="../../assets/tools/{1}/engine.js?v={2}" defer></script>\n'
                   '<script src="../../assets/tools/{1}/ui.js?v={3}" defer></script>\n'
                   '<script src="../../assets/shell.js?v={4}" defer></script>').format(
            VER['lz-string.min.js'], tool, VER['engine:' + tool], VER['ui:' + tool], VER['shell.js'])
    else:
        scripts = ('<script src="../../assets/i18n.js?v={0}"></script>\n'
                   '<script src="../../assets/app.js?v={1}"></script>').format(VER['i18n.js'], VER['app.js'])
    _r = next(t for t in REG if t['slug'] == tool)
    kicker = ('<div class="kicker"><span class="ico">%s</span><span class="cat">%s</span></div>'
              % (icon_svg(_r['icon']), html.escape(CATS[_r['cat']][lang])))
    e = lambda x: html.escape(x, quote=True)
    page = f'''<!doctype html>
<html lang="{lang}" dir="{dirn}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
{alternates(tool)}
<meta property="og:type" content="website">
<meta property="og:site_name" content="RateLark">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{locale}">
<meta property="og:image" content="{BASE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{BASE}/og.png">
<meta name="theme-color" content="#EDF1F5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1622" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{e(fonts)}">
<link rel="stylesheet" href="../../assets/app.css?v={VER['app.css']}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')}</script>
</head>
<body data-tool="{tool}">
<div class="tfx" aria-hidden="true"><i class="arc l"></i><i class="arc r"></i></div>
{hdr}
{nav}
<main id="main">
{kicker}
{sec}
{sh}
{fb}
</main>
{ft}
{scripts}
<script src="../../assets/palette.js?v={VER['palette.js']}" defer></script>
</body>
</html>
'''
    return page


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(text)


shutil.rmtree(OUT, ignore_errors=True)
extra_css = '''
a.tab{text-decoration:none}
.tab[aria-current="page"]{color:var(--ink);border-bottom-color:var(--ink)}
.langs{display:flex;flex-wrap:wrap;gap:.4rem 1rem;margin:0 0 .9rem}
.langs a{color:var(--muted)}
.langs a[aria-current="true"]{color:var(--ink);font-weight:600;text-decoration:none}
'''
PAL_CSS = open(os.path.join(HERE, 'palette.css'), encoding='utf-8').read()
PAL_JS = open(os.path.join(HERE, 'palette.js'), encoding='utf-8').read()
PLUGIN_CSS = ''.join(open(os.path.join(HERE, 'tools', t, 'tool.css'), encoding='utf-8').read() for t in PLUGINS)
SHELL_JS = open(os.path.join(HERE, 'shell.js'), encoding='utf-8').read()
LZ_JS = open(os.path.join(HERE, 'tools', 'ppp-pricing-calculator', 'lz-string.min.js'), encoding='utf-8').read()
_css = css + extra_css + bgart.css() + PAL_CSS + PLUGIN_CSS
VER = {n: hashlib.sha1(t.encode()).hexdigest()[:8] for n, t in
       (('app.css', _css), ('i18n.js', i18n_js), ('app.js', main_js), ('palette.js', PAL_JS), ('shell.js', SHELL_JS), ('lz-string.min.js', LZ_JS))}
for _t in PLUGINS:
    for _f in ('engine', 'ui'):
        VER['%s:%s' % (_f, _t)] = hashlib.sha1(open(os.path.join(HERE, 'tools', _t, _f + '.js'), 'rb').read()).hexdigest()[:8]
write('assets/app.css', _css)
write('assets/i18n.js', i18n_js)
write('assets/app.js', main_js)
write('assets/palette.js', PAL_JS)
write('assets/palette.css', PAL_CSS)
write('assets/shell.js', SHELL_JS)
write('assets/lz-string.min.js', LZ_JS)
for _t in PLUGINS:
    for _f in ('engine.js', 'ui.js'):
        write('assets/tools/%s/%s' % (_t, _f), open(os.path.join(HERE, 'tools', _t, _f), encoding='utf-8').read())
write('assets/data/ppp.json', open(os.path.join(HERE, 'data', 'ppp.json'), encoding='utf-8').read())

# per-language search index for the command palette (names + descriptions come from the translated pages)
for code, nm, _, _ in LANGS:
    mp = MAPS[code]
    tl = []
    for t in REG:
        tl.append({'slug': t['slug'], 'name': tool_name(code, t['slug']), 'desc': tool_desc(code, t['slug']),
                   'cat': CATS[t['cat']][code], 'url': '/%s/%s/' % (code, t['slug'])})
    write('assets/tools-%s.json' % code, json.dumps({'ui': UI[code], 'tools': tl,
          'langs': [{'code': c, 'name': n} for c, n, _, _ in LANGS]}, ensure_ascii=False))

count = 0
for code, *_ in LANGS:
    for tool in TOOLS:
        write('%s/%s/index.html' % (code, tool), build_page(code, tool))
        count += 1

# sitemap with hreflang alternates
urls = []
for code, *_ in LANGS:
    for tool in TOOLS:
        alts = ''.join('<xhtml:link rel="alternate" hreflang="%s" href="%s/%s/%s/"/>' % (h, BASE, c, tool)
                       for c, _, h, _ in LANGS)
        alts += '<xhtml:link rel="alternate" hreflang="x-default" href="%s/en/%s/"/>' % (BASE, tool)
        urls.append('<url><loc>%s/%s/%s/</loc><lastmod>%s</lastmod>%s</url>' % (BASE, code, tool, TODAY, alts))
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
      + '\n'.join(urls) + '\n</urlset>\n')
write('robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % BASE)
write('.nojekyll', '')

HEAD_COMMON = f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#EDF1F5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1622" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/plain.css">"""
write('assets/plain.css', 'html{background:#03050a}body{font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;max-width:36rem;margin:3rem auto;padding:0 1rem;color:#F2F5FA;background:radial-gradient(ellipse 90vw 40vh at 50% -12vh,rgba(79,124,255,.45),transparent 70%),#03050a;min-height:100vh}\n'
      'a{color:#FFD84D}li{margin:.4rem 0}h1{font-size:1.9rem;margin:0 0 .5rem}h2{font-size:1.15rem;margin:1.6rem 0 .3rem}p{color:#C3CCDD}\n')

e = lambda x: html.escape(x, quote=True)
# root page: cinematic dark landing with a 3D lark (assets/hero.*)
TOOL_LABELS = [('hourly-rate', 'Hourly rate'), ('quote', 'Project quote'), ('invoice', 'Invoice'),
               ('markup-margin', 'Markup & margin'), ('retainer', 'Retainer vs hourly'),
               ('late-fee', 'Late fee'), ('tax', 'Tax set-aside')]
chips = ''.join('<li><a data-tool="%s" href="/en/%s/">%s</a></li>' % (t, t, n) for t, n in TOOL_LABELS)
DESC_EN = {t['slug']: tool_desc('en', t['slug']) for t in REG}
def tile(t):
    slug = t['slug']
    label = dict(TOOL_LABELS).get(slug) or tool_name('en', slug)
    return ('<a class="tile t-%s" data-cat="%s" data-tool="%s" href="/en/%s/">'
            '<span class="tile-top"><span class="ico">%s</span><span class="cat">%s</span></span>'
            '<span class="tile-body"><h3>%s</h3><p>%s</p></span>'
            '<span class="ex"><i>Example</i>%s</span></a>'
            % (t['size'], t['cat'], slug, slug, icon_svg(t['icon']), CATS[t['cat']]['en'], label, e(DESC_EN[slug]), e(t['sample'])))
bento = ''.join(tile(t) for t in REG)
CHEV = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
def _cats():
    order = []
    for t in REG:
        if t['cat'] not in order: order.append(t['cat'])
    return order
def mega_html():
    cols = ''
    for c in _cats():
        items = ''.join('<li><a data-tool="%s" href="/en/%s/"><span class="ico">%s</span><span class="mi"><b>%s</b><small>%s</small></span></a></li>'
                        % (t['slug'], t['slug'], icon_svg(t['icon'], 20), e(tool_name('en', t['slug'])), e(tool_desc('en', t['slug'])))
                        for t in REG if t['cat'] == c)
        cols += '<div class="mc"><h3>%s</h3><ul>%s</ul></div>' % (e(CATS[c]['en']), items)
    return cols
def footer_tools():
    out = ''
    for c in _cats():
        out += '<div class="fc"><h3>%s</h3><ul>%s</ul></div>' % (e(CATS[c]['en']), ''.join(
            '<li><a data-tool="%s" href="/en/%s/">%s</a></li>' % (t['slug'], t['slug'], e(tool_name('en', t['slug']))) for t in REG if t['cat'] == c))
    return out
cat_order = []
for t in REG:
    if t['cat'] not in cat_order: cat_order.append(t['cat'])
filters = '<button type="button" data-cat="all" aria-pressed="true">All</button>' + ''.join(
    '<button type="button" data-cat="%s" aria-pressed="false">%s</button>' % (c, CATS[c]['en']) for c in cat_order)
langs = ''.join('<a href="/%s/hourly-rate/" hreflang="%s" lang="%s">%s</a>' % (c, h, c, n) for c, n, h, _ in LANGS)
shutil.copy(os.path.join(HERE, 'hero.js'), os.path.join(OUT, 'assets', 'hero.js'))
shutil.copy(os.path.join(HERE, 'hero.css'), os.path.join(OUT, 'assets', 'hero.css'))
LAYERS = logo.hero_art()
MEGA = mega_html()
FOOTER_TOOLS = footer_tools()
LANGLIS = ''.join('<li><a href="/%s/hourly-rate/" hreflang="%s" lang="%s">%s</a></li>' % (c, h, c, n) for c, n, h, _ in LANGS)
write('index.html', f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#05070b">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<title>RateLark: free tools for freelancers</title>
<meta name="description" content="Hourly rate, project quote, invoice, markup and margin, retainer, late fee and tax tools for freelancers, in 9 languages. Free, private, no sign-up.">
<link rel="canonical" href="{BASE}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="RateLark">
<meta property="og:title" content="RateLark: free tools for freelancers">
<meta property="og:description" content="Price your work, send the invoice, set aside the tax. Seven free tools in 9 languages.">
<meta property="og:url" content="{BASE}/">
<meta property="og:image" content="{BASE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{e(fonts)}">
<link rel="stylesheet" href="/assets/hero.css">
<link rel="stylesheet" href="/assets/palette.css">
</head>
<body>
<div class="fx" aria-hidden="true"><i class="arc l"></i><i class="arc r"></i></div>
<header class="nav">
  <a class="brand" href="/"><span class="mark" aria-hidden="true"></span><span class="wm">Rate<span class="lk">Lark</span></span></a>
  <ul class="links"><li class="has-menu"><button type="button" class="menu-btn" id="tools-btn" aria-expanded="false" aria-controls="tools-menu">Tools {CHEV}</button><div class="mega" id="tools-menu" role="region" aria-label="All tools" hidden><div class="mega-in">{MEGA}</div><a class="mega-all" data-tool="hourly-rate" href="/en/hourly-rate/">Open the tool pages &rarr;</a></div></li><li><a href="#why">Why RateLark</a></li><li><a href="#langs">Languages</a></li><li><a href="/privacy/">Privacy</a></li></ul>
  <div class="navr"><button type="button" class="kbtn" data-palette aria-label="Search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg><span class="kt">Search</span><kbd>Ctrl K</kbd></button><a class="pill" data-tool="hourly-rate" href="/en/hourly-rate/">Try it</a></div>
</header>
<main class="stage">
  <div class="ghost" aria-hidden="true">Rate<span class="lk">Lark</span></div>
  <div class="hero-mark" aria-hidden="true"><div class="tilt">{LAYERS}</div></div>
  <div class="hud h1" aria-hidden="true">Free tools<b>{len(REG)}</b></div>
  <div class="hud h2" aria-hidden="true">Languages<b>9</b></div>
  <div class="hud h3" aria-hidden="true">Sign-ups needed<b>0</b></div>
  <section class="copy">
    <span class="tag">Freelance pricing, quote, invoice and tax tools in one place.</span>
    <h1>Freelancing <em>without</em> borders</h1>
    <p class="lead">Work out your rate, price the project, send the invoice and set aside the tax. Free tools in 9 languages. Nothing you type leaves your browser.</p>
    <div class="cta"><a class="pill light" data-tool="hourly-rate" href="/en/hourly-rate/">Get started</a><a class="pill solid" data-tool="invoice" href="/en/invoice/">Make an invoice</a></div>
  </section>
</main>
<section class="why" id="why" aria-labelledby="why-h">
  <h2 id="why-h">Built to be used in a minute</h2>
  <ul>
    <li><span class="wi">{icon_svg('clock', 22)}</span><b>Free, with no sign-up</b><p>Open a tool and the answer is already on screen. No account, no email, no card.</p></li>
    <li><span class="wi">{icon_svg('receipt', 22)}</span><b>Private by design</b><p>Every calculation runs in your browser. What you type is never uploaded.</p></li>
    <li><span class="wi">{icon_svg('globe', 22)}</span><b>Made for the world</b><p>Nine languages, 19 currencies and tax rules for the US, UK, Canada and Australia.</p></li>
  </ul>
  <div class="why-cta"><a class="pill light" data-tool="hourly-rate" href="/en/hourly-rate/">Get started</a><button type="button" class="pill" data-palette>Search every tool <kbd>Ctrl K</kbd></button></div>
</section>
<footer class="foot2" id="langs">
  <div class="fgrid">
    <div class="fc fbrand"><a class="brand" href="/"><span class="mark" aria-hidden="true"></span><span class="wm">Rate<span class="lk">Lark</span></span></a><p>Freelance pricing, quote, invoice and tax tools in one place.</p></div>
    {FOOTER_TOOLS}
    <div class="fc"><h3>Languages</h3><ul>{LANGLIS}</ul></div>
    <div class="fc"><h3>Company</h3><ul><li><a href="/privacy/">Privacy</a></li><li><a href="mailto:{CONTACT_EMAIL}">Contact</a></li></ul></div>
  </div>
  <p class="fine">&copy; RateLark. Results are estimates, not tax, financial or legal advice.</p>
</footer>
<script type="module" src="/assets/hero.js"></script>
<script src="/assets/palette.js" defer></script>
</body>
</html>
""")

write('404.html', f"""<!doctype html><html lang="en"><head>
{HEAD_COMMON}
<title>Page not found | RateLark</title><meta name="robots" content="noindex"></head>
<body><h1>Page not found</h1><p>That page does not exist. <a href="/">Go to RateLark</a></p></body></html>
""")

write('privacy/index.html', f"""<!doctype html><html lang="en"><head>
{HEAD_COMMON}
<title>Privacy | RateLark</title>
<meta name="description" content="RateLark does not collect, upload or sell anything you type. Here is exactly what the site does and does not do.">
<link rel="canonical" href="{BASE}/privacy/">
</head>
<body>
<h1>Privacy</h1>
<p>Last updated {TODAY}.</p>
<h2>What you type stays on your device</h2>
<p>RateLark's calculators run entirely in your browser. The numbers, names and invoice details you enter are never sent to us or to anyone else.</p>
<h2>What is stored in your browser</h2>
<p>To remember your choices, RateLark saves your language and currency in your browser's local storage. It never leaves your device. Clear your site data to remove it. RateLark sets no cookies.</p>
<h2>No tracking</h2>
<p>RateLark has no analytics, advertising or tracking scripts.</p>
<h2>Third parties</h2>
<p>Pages load fonts from Google Fonts, so Google receives your IP address and browser details when a page loads. The site is served by a hosting provider, which may keep standard server logs (IP address, page requested, time).</p>
<h2>Contact</h2>
<p>Questions, corrections or feedback: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. When you email us we receive your message and your email address, and we use them only to reply. Mail to this address is forwarded through Cloudflare's email routing.</p>
<h2>Not advice</h2>
<p>Results are estimates, not tax, financial or legal advice. Check the rates and rules that apply to you.</p>
<p><a href="/">Back to RateLark</a></p>
</body></html>
""")
_sm = open(os.path.join(OUT, 'sitemap.xml'), encoding='utf-8').read().replace(
    '</urlset>', '<url><loc>%s/privacy/</loc><lastmod>%s</lastmod></url>\n</urlset>' % (BASE, TODAY))
write('sitemap.xml', _sm)

write('site.webmanifest', json.dumps({
    'name': 'RateLark', 'short_name': 'RateLark', 'start_url': '/', 'display': 'browser',
    'background_color': '#EDF1F5', 'theme_color': '#EDF1F5',
    'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, indent=2))

STATIC = os.path.join(HERE, 'static')
for f in os.listdir(STATIC):
    shutil.copy(os.path.join(STATIC, f), os.path.join(OUT, f))

# security + caching headers (Cloudflare Pages and Netlify both read _headers)
write('_headers', """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
/assets/*
  Cache-Control: public, max-age=86400
""")
print('built %d pages for %s into %s' % (count, BASE, OUT))
