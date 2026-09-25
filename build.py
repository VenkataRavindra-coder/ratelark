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
from tax_i18n_data import TAX_I18N

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
# Stage 2: keyword URL slugs. Internal tool ids (used for sections, TITLES, nav ids, i18n
# lookups) stay unchanged; only the public URL path changes. 'tax' and 'ppp-pricing-calculator'
# are intentionally absent (tax is replaced by four country pages in Stage 3; ppp keeps its slug).
URL_SLUG = {
 'hourly-rate': 'freelance-hourly-rate-calculator',
 'quote': 'project-quote-calculator',
 'invoice': 'invoice-generator',
 'markup-margin': 'markup-margin-calculator',
 'retainer': 'retainer-vs-hourly-calculator',
 'late-fee': 'late-payment-fee-calculator',
}
def url_slug(t):
    return URL_SLUG.get(t, t)


# Stage 3: the single tax tool (country picker) becomes four fixed-country pages sharing the
# same #tool-tax markup/JS, filtered per country at build time. The internal id 'tax' still
# exists (hourkit.html section, TOOLS/REG entry, nav tab) and its URL now points at the US page,
# the largest audience and first-listed country in the brief.
TAX_SLUG = {
 'us': 'us-freelance-tax-calculator',
 'uk': 'uk-self-employed-tax-calculator',
 'ca': 'canada-self-employed-tax-calculator',
 'au': 'australia-sole-trader-tax-calculator',
}
URL_SLUG['tax'] = TAX_SLUG['us']
TAX_SOURCES = json.load(open(os.path.join(HERE, 'data', 'tax-sources.json'), encoding='utf-8'))
# small chrome labels on the tax pages (Sources box heading, Other-countries box heading,
# "Rates for X, last checked Y." note), translated for all 9 languages.
TAX_UI = {
 'en': dict(sources='Sources', other='Other countries', rates='Rates for %(y)s, last checked %(m)s.'),
 'es': dict(sources='Fuentes', other='Otros países', rates='Tarifas de %(y)s, última verificación: %(m)s.'),
 'pt': dict(sources='Fontes', other='Outros países', rates='Taxas de %(y)s, última verificação: %(m)s.'),
 'fr': dict(sources='Sources', other='Autres pays', rates='Taux pour %(y)s, dernière vérification : %(m)s.'),
 'de': dict(sources='Quellen', other='Andere Länder', rates='Sätze für %(y)s, zuletzt geprüft: %(m)s.'),
 'hi': dict(sources='स्रोत', other='अन्य देश', rates='%(y)s की दरें, अंतिम बार जांचा गया: %(m)s।'),
 'ar': dict(sources='المصادر', other='دول أخرى', rates='معدلات %(y)s، آخر تحقق: %(m)s.'),
 'zh': dict(sources='数据来源', other='其他国家', rates='%(y)s税率，最近核实于%(m)s。'),
 'id': dict(sources='Sumber', other='Negara lain', rates='Tarif untuk %(y)s, terakhir diperiksa: %(m)s.'),
}
# English-only for this pass (see brief: "English first"); FAQ facts are verified against the
# official sources in tax-sources.json, not guessed (see the commit message / session notes for
# what was checked and when).
TAX_PAGE = {
 'us': dict(
   title='US Freelance Tax Calculator (Self-Employment Tax, 2026)',
   faq_h2='How self-employment tax works',
   desc='Estimate self-employment tax and income tax on your freelance profit and how much to set aside each quarter.',
   intro='Work out federal self-employment tax on your freelance profit, plus a rough income-tax set-aside, and see what to put away each quarter.',
   faqs=[
     ('How much is self-employment tax in 2026?',
      'Self-employment tax is 15.3% of 92.35% of your net profit from self-employment: 12.4% Social Security up to the $184,500 wage base, plus 2.9% Medicare with no cap. You owe no self-employment tax if your net earnings are under $400.'),
     ('When are 2026 estimated tax payments due?',
      'For the 2026 calendar year: April 15, June 15 and September 15, 2026, then January 15, 2027. A payment is on time if it is made by the next business day when the date falls on a weekend or holiday.'),
     ('Is this tax advice?',
      'No. It is an estimate for planning. It ignores the standard deduction, credits and state rules, so use it as a set-aside guide, not a return — an accountant can tell you what you really owe.'),
   ]),
 'uk': dict(
   title='UK Self-Employed Tax Calculator (2026/27)',
   faq_h2='How this estimate works',
   desc='Estimate income tax and Class 4 National Insurance on your self-employed profit for 2026/27.',
   intro='Work out income tax and Class 4 National Insurance on your self-employed profit for the 2026/27 tax year, and see what to set aside.',
   faqs=[
     ('What are the Class 4 National Insurance rates for 2026/27?',
      '6% on profits between £12,570 and £50,270, and 2% above that. This is on top of income tax; Class 2 National Insurance is not included in this calculator.'),
     ('When do I pay my Self Assessment bill?',
      'The balance for the tax year is due by 31 January. If HMRC asks for payments on account, they are due by 31 January and 31 July, each usually half of the previous year’s bill.'),
     ('Is this tax advice?',
      'No. It is an estimate for planning purposes only. An accountant can tell you exactly what you owe and confirm your payment dates.'),
   ]),
 'ca': dict(
   title='Canada Self-Employed Tax Calculator (2026)',
   faq_h2='How this estimate works',
   desc='Estimate federal tax, CPP and provincial tax on your self-employed income for 2026.',
   intro='Work out federal income tax and self-employed CPP contributions on your 2026 self-employed income, plus the provincial rate you enter.',
   faqs=[
     ('How much CPP do self-employed people pay in 2026?',
      '11.9% on earnings between $3,500 and $74,600 (the base plus the first CPP enhancement), plus 8% on earnings between $74,600 and $85,000 (CPP2). Self-employed people pay both the employee and employer portions, and half of what you pay is deducted from your income for tax purposes.'),
     ('When are my taxes due?',
      'Self-employed individuals have until June 15, 2026 to file, but any balance owing for 2025 is still due by April 30, 2026. If you must pay by instalments, the usual due dates are March 15, June 15, September 15 and December 15.'),
     ('Is this tax advice?',
      'No. It is a planning estimate that excludes EI, GST/HST, Quebec’s separate system and most credits beyond the basic personal amount. An accountant or the CRA can confirm exactly what you owe.'),
   ]),
 'au': dict(
   title='Australia Sole Trader Tax Calculator (2026-27)',
   faq_h2='How this estimate works',
   desc='Estimate income tax and the Medicare levy on your sole trader income for 2026-27.',
   intro='Work out income tax and the Medicare levy on your sole trader income for the 2026-27 income year, and see what to set aside.',
   faqs=[
     ('What are the 2026-27 resident tax rates?',
      'Nothing on the first $18,200, 15% up to $45,000, 30% up to $135,000, 37% up to $190,000, and 45% above that, plus the 2% Medicare levy on taxable income. The low-income Medicare levy reduction is not included here.'),
     ('When are PAYG instalments due?',
      'For quarterly sole traders: 28 October, 28 February, 28 April and 28 July, each covering the quarter just ended.'),
     ('Is this tax advice?',
      'No. It is a planning estimate that excludes offsets like LITO, HELP repayments, the Medicare levy surcharge and GST. Check with the ATO or an accountant for your exact obligations.'),
   ]),
}


CONTACT_EMAIL = 'hello@ratelark.com'
CONTACT_LABEL = {'en': 'Contact', 'es': 'Contacto', 'pt': 'Contato', 'fr': 'Contact', 'de': 'Kontakt', 'hi': '\u0938\u0902\u092a\u0930\u094d\u0915',
                 'ar': '\u0627\u062a\u0635\u0644 \u0628\u0646\u0627', 'zh': '\u8054\u7cfb\u6211\u4eec', 'id': 'Kontak'}
# per-language hub page (/{lang}/) chrome: H1 and meta description. Card copy reuses tool_name()/tool_desc().
HUB_H1 = {
 'en': 'Freelance Pricing, Quote, Invoice and Tax Tools',
 'es': 'Herramientas de precios, presupuestos, facturas e impuestos para freelancers',
 'pt': 'Ferramentas de pre\u00e7o, or\u00e7amento, fatura e imposto para freelancers',
 'fr': 'Outils de tarification, devis, facturation et imp\u00f4ts pour freelances',
 'de': 'Preis-, Angebots-, Rechnungs- und Steuertools f\u00fcr Freelancer',
 'hi': '\u092b\u094d\u0930\u0940\u0932\u093e\u0902\u0938\u0930\u094b\u0902 \u0915\u0947 \u0932\u093f\u090f \u092a\u094d\u0930\u093e\u0907\u0938\u093f\u0902\u0917, \u0915\u094b\u091f\u0947\u0936\u0928, \u0907\u0928\u0935\u0949\u0907\u0938 \u0914\u0930 \u091f\u0948\u0915\u094d\u0938 \u091f\u0942\u0932\u094d\u0938',
 'ar': '\u0623\u062f\u0648\u0627\u062a \u062a\u0633\u0639\u064a\u0631 \u0648\u0639\u0631\u0648\u0636 \u0623\u0633\u0639\u0627\u0631 \u0648\u0641\u0648\u0627\u062a\u064a\u0631 \u0648\u0636\u0631\u0627\u0626\u0628 \u0644\u0644\u0645\u0633\u062a\u0642\u0644\u064a\u0646',
 'zh': '\u4e3a\u81ea\u7531\u804c\u4e1a\u8005\u63d0\u4f9b\u7684\u5b9a\u4ef7\u3001\u62a5\u4ef7\u3001\u53d1\u7968\u548c\u7a0e\u52a1\u5de5\u5177',
 'id': 'Alat penetapan harga, penawaran, invoice, dan pajak untuk freelancer',
}
HUB_DESC = {
 'en': 'Free, private calculators for freelancers: hourly rate, project quotes, invoices, markup, retainers, late fees and tax set-aside. No sign-up.',
 'es': 'Calculadoras gratuitas y privadas para freelancers: tarifa por hora, presupuestos de proyectos, facturas, markup, tarifas fijas y ahorro de impuestos. Sin registro.',
 'pt': 'Calculadoras gratuitas e privadas para freelancers: valor da hora, or\u00e7amentos de projetos, faturas, markup, retainers e imposto a reservar. Sem cadastro.',
 'fr': "Calculateurs gratuits et priv\u00e9s pour freelances\u00a0: taux horaire, devis de projets, factures, majoration, forfaits et imp\u00f4ts \u00e0 provisionner. Sans inscription.",
 'de': 'Kostenlose, private Rechner f\u00fcr Freelancer: Stundensatz, Projektangebote, Rechnungen, Aufschlag, Pauschalen und Steuerr\u00fccklage. Ohne Anmeldung.',
 'hi': '\u092b\u094d\u0930\u0940\u0932\u093e\u0902\u0938\u0930\u094b\u0902 \u0915\u0947 \u0932\u093f\u090f \u092e\u0941\u092b\u094d\u0924, \u0928\u093f\u091c\u0940 \u0915\u0948\u0932\u094d\u0915\u0941\u0932\u0947\u091f\u0930: \u0918\u0902\u091f\u0947 \u0915\u0940 \u0926\u0930, \u092a\u094d\u0930\u094b\u091c\u0947\u0915\u094d\u091f \u0915\u094b\u091f\u0947\u0936\u0928, \u0907\u0928\u0935\u0949\u0907\u0938, \u092e\u093e\u0930\u094d\u0915\u0905\u092a, \u0930\u093f\u091f\u0947\u0928\u0930 \u0914\u0930 \u091f\u0948\u0915\u094d\u0938 \u0938\u0947\u091f-\u0905\u0938\u093e\u0907\u0928\u0964 \u092c\u093f\u0928\u093e \u0938\u093e\u0907\u0928-\u0905\u092a\u0964',
 'ar': '\u062d\u0627\u0633\u0628\u0627\u062a \u0645\u062c\u0627\u0646\u064a\u0629 \u0648\u062e\u0627\u0635\u0629 \u0644\u0644\u0645\u0633\u062a\u0642\u0644\u064a\u0646: \u0633\u0639\u0631 \u0627\u0644\u0633\u0627\u0639\u0629\u060c \u0639\u0631\u0648\u0636 \u0623\u0633\u0639\u0627\u0631 \u0627\u0644\u0645\u0634\u0627\u0631\u064a\u0639\u060c \u0627\u0644\u0641\u0648\u0627\u062a\u064a\u0631\u060c \u0647\u0627\u0645\u0634 \u0627\u0644\u0631\u0628\u062d\u060c \u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643\u0627\u062a \u0627\u0644\u0634\u0647\u0631\u064a\u0629\u060c \u0648\u062a\u062c\u0646\u064a\u0628 \u0627\u0644\u0636\u0631\u0627\u0626\u0628. \u0628\u062f\u0648\u0646 \u062a\u0633\u062c\u064a\u0644.',
 'zh': '\u4e3a\u81ea\u7531\u804c\u4e1a\u8005\u63d0\u4f9b\u7684\u514d\u8d39\u3001\u79c1\u5bc6\u8ba1\u7b97\u5668\uff1a\u65f6\u85aa\u3001\u9879\u76ee\u62a5\u4ef7\u3001\u53d1\u7968\u3001\u52a0\u4ef7\u7387\u3001\u5305\u6708\u8d39\u548c\u7a0e\u52a1\u9884\u7559\u3002\u65e0\u9700\u6ce8\u518c\u3002',
 'id': 'Kalkulator gratis dan privat untuk freelancer: tarif per jam, penawaran proyek, invoice, markup, retainer, dan alokasi pajak. Tanpa daftar.',
}
def icon_svg(name, size=22):
    return ('<svg viewBox="0 0 24 24" width="%d" height="%d" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % (size, size, ICONS.get(name, ICONS['file'])))
TODAY = datetime.date.today().isoformat()
TODAY = datetime.date.today().isoformat()
SEL = ('.tab,.cur>span,h1,h2,.head p,.l,.hint,.mini,dt,.lbl,.note,summary,'
       '.about p,details p,.btn,.suf,option,footer p,.howto li')

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
        out.append('<link rel="alternate" hreflang="%s" href="%s/%s/%s/">' % (hl, BASE, code, url_slug(tool)))
    out.append('<link rel="alternate" hreflang="x-default" href="%s/en/%s/">' % (BASE, url_slug(tool)))
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


# Stage 4 item 15: up to 3 related tools for the "Related tools" block on every page --
# same category first, then fill from the rest of the registry so every page gets exactly 3.
def related_tools(slug, n=3):
    this = next(t for t in REG if t['slug'] == slug)
    same_cat = [t for t in REG if t['slug'] != slug and t['cat'] == this['cat']]
    rest = [t for t in REG if t['slug'] != slug and t['cat'] != this['cat']]
    return (same_cat + rest)[:n]


def related_tools_html(lang, slug):
    e = lambda x: html.escape(x, quote=True)
    cards = ''.join(hub_card(lang, t) for t in related_tools(slug))
    return ('<div class="about sheet"><h2>%s</h2><div class="hub-grid">%s</div></div>'
            % (e(tr('Related tools', lang)), cards))


# Stage 4 items 13/14/16: hourly-rate -> quote -> invoice -> late-fee handoffs, carried through
# localStorage by assets/connect.js (see that file). Maps a tool's internal slug to the button
# id connect.js listens for, the English button text (translated via tr()) and the target tool.
CONNECT_NEXT = {
 'hourly-rate': ('connect-to-quote', 'Use this rate in a quote →', 'quote'),
 'quote': ('connect-to-invoice', 'Turn this into an invoice →', 'invoice'),
 'invoice': ('connect-to-latefee', 'Track this invoice for late payment →', 'late-fee'),
}


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
<div class="howto sheet"><h2>{q(T['howto_h'])}</h2><ol><li>{q(T['howto1'])}</li><li>{q(T['howto2'])}</li><li>{q(T['howto3'])}</li></ol></div>
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
        a['href'] = '../%s/' % url_slug(t)
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

    if tool in CONNECT_NEXT:
        btn_id, btn_text_en, next_tool = CONNECT_NEXT[tool]
        btn_html = ('<div class="cta-row"><a id="%s" class="btn" href="%s">%s</a></div>'
                    % (btn_id, html.escape('../%s/' % url_slug(next_tool), quote=True),
                       html.escape(tr(btn_text_en, lang), quote=True)))
        about = sec.find(class_='about')
        if about is not None:
            about.insert_before(BeautifulSoup(btn_html, 'html.parser').div)
    sec.append(BeautifulSoup(related_tools_html(lang, tool), 'html.parser').div)

    ft = copy.copy(footer); translate(ft, mp)
    langs_nav = BeautifulSoup('<nav class="langs" aria-label="Languages"></nav>', 'html.parser').nav
    for code, nm, h, _ in LANGS:
        a = BeautifulSoup('<a></a>', 'html.parser').a
        a['href'] = '../../%s/%s/' % (code, url_slug(tool))
        a['hreflang'] = h
        a['lang'] = code
        if code == lang:
            a['aria-current'] = 'true'
        a.string = nm
        langs_nav.append(a)
    ft.insert(0, langs_nav)
    ft.append(BeautifulSoup('<p><a href="/privacy/">%s</a> &middot; <a href="mailto:%s">%s</a></p>' % (UI[lang]['privacy'], CONTACT_EMAIL, CONTACT_LABEL[lang]), 'html.parser'))

    if tool not in PLUGINS:
        title = tr(TITLES[tool], lang)
        faq = []
        for d in sec.find_all('details'):
            q = d.find('summary'); a = d.find('p')
            if q and a:
                faq.append({'@type': 'Question', 'name': q.get_text().strip(),
                            'acceptedAnswer': {'@type': 'Answer', 'text': a.get_text().strip()}})
    url = '%s/%s/%s/' % (BASE, lang, url_slug(tool))
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
    if tool in CONNECT_NEXT:
        scripts += '\n<script src="../../assets/connect.js?v=%s" defer></script>' % VER['connect.js']
    _r = next(t for t in REG if t['slug'] == tool)
    kicker = ('<div class="kicker"><span class="ico">%s</span><span class="cat">%s</span></div>'
              % (icon_svg(_r['icon']), html.escape(CATS[_r['cat']][lang])))
    e = lambda x: html.escape(x, quote=True)
    quote_label_attr = ' data-quote-label="%s"' % e(tool_name(lang, 'quote')) if tool == 'quote' else ''
    ld_json = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
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
<link rel="preload" href="/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css?v={VER['fonts.css']}">
<link rel="stylesheet" href="../../assets/app.css?v={VER['app.css']}">
<script type="application/ld+json">{ld_json}</script>
</head>
<body data-tool="{tool}"{quote_label_attr}>
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


def hub_card(lang, t):
    e = lambda x: html.escape(x, quote=True)
    slug = t['slug']
    return ('<a class="hub-card" href="/%s/%s/">'
            '<span class="hc-top"><span class="hc-ico">%s</span><span class="hc-cat">%s</span></span>'
            '<h3>%s</h3><p>%s</p></a>'
            % (lang, url_slug(slug), icon_svg(t['icon'], 20), e(CATS[t['cat']][lang]),
               e(tool_name(lang, slug)), e(tool_desc(lang, slug))))


def build_tax_page(lang, country):
    """One of the four fixed-country tax pages, sharing #tool-tax's markup/JS with the other
    three countries filtered out via data-c, plus its own H1, intro, FAQs and Sources box."""
    e = lambda x: html.escape(x, quote=True)
    mp = MAPS[lang]
    name, hl, locale = next((n, h, l) for c, n, h, l in LANGS if c == lang)
    dirn = 'rtl' if lang == 'ar' else 'ltr'
    slug = TAX_SLUG[country]
    TP = TAX_PAGE[country] if lang == 'en' else TAX_I18N[country][lang]
    src = TAX_SOURCES[country]

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
        a['href'] = '../%s/' % url_slug(t)
        if t == 'tax':
            a['aria-current'] = 'page'
        a.string = tool_name(lang, t)
        nav.append(a)

    sec = copy.copy(sections['tax'])
    for attr in ('hidden', 'role', 'aria-labelledby'):
        if sec.has_attr(attr):
            del sec[attr]
    translate(sec, mp)

    # fix the country: drop every data-c block that isn't global or this country's, and hide
    # the country picker itself (kept in the DOM, with one option, so setax() still works)
    for el in sec.select('[data-c]'):
        if country not in el['data-c'].split(' '):
            el.decompose()
    country_field = sec.find('select', id='s-country')
    if country_field is not None:
        for opt_el in list(country_field.find_all('option')):
            opt_el.decompose()
        keep = BeautifulSoup('<option value="%s" selected>%s</option>' % (country, e(src['country'])), 'html.parser')
        country_field.append(keep)
        wrap = country_field.find_parent('label', class_='field')
        (wrap or country_field)['hidden'] = ''

    head = sec.find(class_='head')
    head.find('h1').string = TP['title']
    head.find('p').string = TP['intro']

    about = sec.find(class_='about')
    if about is not None:
        about.clear()
        about.append(BeautifulSoup('<h2>%s</h2>' % e(TP['faq_h2']), 'html.parser'))
        faq_ld = []
        for q, a_txt in TP['faqs']:
            d = BeautifulSoup('<details><summary>%s</summary><p>%s</p></details>' % (e(q), e(a_txt)), 'html.parser')
            about.append(d)
            faq_ld.append({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a_txt}})
        tui = TAX_UI[lang]
        src_links = ''.join('<li><a href="%s" rel="noopener">%s</a></li>' % (e(s['url']), e(s['name'])) for s in src['sources'])
        checked = src['last_checked']
        rates_note = tui['rates'] % {'y': e(src['tax_year']), 'm': checked}
        sources_box = BeautifulSoup(
            '<div class="sheet" id="tax-sources"><h2>%s</h2><ul>%s</ul>'
            '<p class="note">%s</p></div>'
            % (e(tui['sources']), src_links, rates_note), 'html.parser').div
        other = [c for c in ('us', 'uk', 'ca', 'au') if c != country]
        other_tp = lambda c: TAX_PAGE[c] if lang == 'en' else TAX_I18N[c][lang]
        related = ''.join('<li><a href="../%s/">%s</a></li>' % (TAX_SLUG[c], e(other_tp(c)['title'].split(' (')[0])) for c in other)
        related_box = BeautifulSoup('<nav class="sheet" aria-label="Other tax pages"><h2>%s</h2><ul>%s</ul></nav>' % (e(tui['other']), related), 'html.parser').nav
        sec.append(sources_box)
        sec.append(related_box)
    else:
        faq_ld = []
    sec.append(BeautifulSoup(related_tools_html(lang, 'tax'), 'html.parser').div)

    sh = copy.copy(share); translate(sh, mp)
    fb = copy.copy(fallback)
    ft = copy.copy(footer); translate(ft, mp)
    langs_nav = BeautifulSoup('<nav class="langs" aria-label="Languages"></nav>', 'html.parser').nav
    for code, nm, h, _ in LANGS:
        a = BeautifulSoup('<a></a>', 'html.parser').a
        a['href'] = '../../%s/%s/' % (code, slug)
        a['hreflang'] = h
        a['lang'] = code
        if code == lang:
            a['aria-current'] = 'true'
        a.string = nm
        langs_nav.append(a)
    ft.insert(0, langs_nav)
    ft.append(BeautifulSoup('<p><a href="/privacy/">%s</a> &middot; <a href="mailto:%s">%s</a></p>' % (UI[lang]['privacy'], CONTACT_EMAIL, CONTACT_LABEL[lang]), 'html.parser'))

    title = TP['title'] + ' | RateLark'
    description = TP['desc']
    url = '%s/%s/%s/' % (BASE, lang, slug)
    ld = [{'@context': 'https://schema.org', '@type': 'WebApplication', 'name': TP['title'],
           'url': url, 'inLanguage': hl, 'applicationCategory': 'BusinessApplication',
           'operatingSystem': 'Any', 'description': description,
           'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}}]
    if faq_ld:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': faq_ld})

    scripts = ('<script src="../../assets/i18n.js?v={0}"></script>\n'
               '<script src="../../assets/app.js?v={1}"></script>').format(VER['i18n.js'], VER['app.js'])
    kicker = ('<div class="kicker"><span class="ico">%s</span><span class="cat">%s</span></div>'
              % (icon_svg('landmark'), html.escape(CATS['tax'][lang])))
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s/%s/%s/">' % (h, BASE, c, slug) for c, _, h, _ in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s/en/%s/">' % (BASE, slug)
    ld_json = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    page = f'''<!doctype html>
<html lang="{lang}" dir="{dirn}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
{alts}
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
<link rel="preload" href="/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css?v={VER['fonts.css']}">
<link rel="stylesheet" href="../../assets/app.css?v={VER['app.css']}">
<script type="application/ld+json">{ld_json}</script>
</head>
<body data-tool="tax">
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


# Stage 5: three how-to articles, English only for now (per the brief: "Translate later only
# if the English versions get traffic"). Worked examples use the exact same formulas as the
# live calculators (hourly(), quote() and invData() in hourkit.html) -- see the commit message
# for the Python that produced these numbers, so they can be checked against the tool directly.
ARTICLES = {
 'how-to-calculate-freelance-hourly-rate': dict(
   title='How to Calculate Your Freelance Hourly Rate',
   desc='A step-by-step method for working out the hourly rate you need as a freelancer, with a worked example and a free calculator.',
   related='hourly-rate',
   body='''
<div class="about sheet">
<h2>Start from what you want to take home, not what sounds competitive</h2>
<p>Picking a rate by asking what other freelancers charge, or what sounds "reasonable," skips the one number that actually matters: what you need to earn to cover your life, your tax bill and your business costs. Working backwards from that number gives you a rate that is a floor, not a guess &mdash; the point below which you are losing money, even if the job looks busy.</p>
</div>
<div class="about sheet">
<h2>The four numbers you need</h2>
<p><b>Take-home pay.</b> What you want left over per year after tax, for yourself &mdash; not your revenue target.</p>
<p><b>Tax rate.</b> Your effective rate, not your top bracket: total tax paid divided by total income. If you are not sure, 25&ndash;30% is a common starting estimate in many countries, but check your own numbers with the <a href="../us-freelance-tax-calculator/">tax calculator</a> or an accountant.</p>
<p><b>Business expenses.</b> Software, equipment, insurance, coworking space, professional fees &mdash; the costs of running the business, separate from your own pay.</p>
<p><b>Billable hours per year.</b> Not the hours you work. The hours you can actually invoice.</p>
</div>
<div class="about sheet">
<h2>Why billable hours are lower than hours worked</h2>
<p>A 40-hour week does not mean 40 billable hours. Admin, invoicing, replying to email, pitching for the next job, and gaps between contracts all take time you cannot bill for. Most freelancers plan around 20 to 30 billable hours a week rather than 40 &mdash; the exact number depends on how much of your own admin and sales work you do, and how steady your pipeline is.</p>
<p>This is the lever that moves your rate the most. Lower your billable hours in the calculation and the rate climbs fast, because the same annual costs are being spread across fewer hours.</p>
</div>
<div class="about sheet">
<h2>The formula</h2>
<p>Gross your take-home pay up for tax, add your business expenses, then divide by the hours you can actually bill in a year:</p>
<p><code>rate = (take-home &divide; (1 &minus; tax rate) + expenses) &divide; billable hours per year</code></p>
<p>Billable hours per year is <code>(52 &minus; weeks off) &times; billable hours per week</code>.</p>
</div>
<div class="sheet">
<h2>Worked example</h2>
<p>A freelancer wants $70,000 take-home pay, has $8,000 a year in business expenses, expects a 25% effective tax rate, takes 4 weeks off, and can bill 25 hours a week.</p>
<dl class="stats">
<div><dt>Billable hours per year</dt><dd>(52 &minus; 4) &times; 25 = 1,200 hrs</dd></div>
<div><dt>Grossed-up for tax</dt><dd>$70,000 &divide; (1 &minus; 0.25) = $93,333.33</dd></div>
<div><dt>Plus expenses</dt><dd>$93,333.33 + $8,000 = $101,333.33</dd></div>
<div><dt>Minimum hourly rate</dt><dd>$101,333.33 &divide; 1,200 = <b>$84.44/hr</b></dd></div>
<div><dt>Day rate (8 billable hours)</dt><dd>$675.56</dd></div>
</dl>
<p class="note">Run your own numbers in the <a href="../freelance-hourly-rate-calculator/">hourly rate calculator</a> &mdash; it does this same calculation instantly and includes an estimated tax breakdown.</p>
</div>
<div class="about sheet">
<h2>Common mistakes</h2>
<p><b>Using 40 hours a week.</b> Almost nobody bills 40 hours a week consistently; the rate comes out too low and you fall short of your take-home target.</p>
<p><b>Forgetting to gross up for tax.</b> Dividing your take-home target straight by hours, with no tax adjustment, understates the rate you actually need.</p>
<p><b>Leaving out expenses.</b> Software, insurance and equipment are real costs of doing business and belong in the calculation, not absorbed silently out of your take-home pay.</p>
<p><b>Treating it as the rate to quote.</b> This is a floor. Quote above it to leave room for discounts, slow months and clients who pay late &mdash; see <a href="../how-to-price-freelance-projects/">how to price a project</a> for the next step.</p>
</div>
'''),
 'how-to-price-freelance-projects': dict(
   title='How to Price a Freelance Project (With a Buffer and Deposit)',
   desc='How to turn an hourly rate into a fixed-price project quote, with a buffer for surprises and a worked example.',
   related='quote',
   body='''
<div class="about sheet">
<h2>An hourly rate is not a project quote</h2>
<p>Once you know your <a href="../how-to-calculate-freelance-hourly-rate/">minimum hourly rate</a>, pricing a fixed-scope project takes a few more steps: estimating the hours honestly, protecting yourself against the work running long, and deciding how much to ask for upfront.</p>
</div>
<div class="about sheet">
<h2>Estimate the hours honestly</h2>
<p>Break the project into the actual tasks &mdash; discovery calls, drafts, revisions, testing, handoff &mdash; and add up realistic hours for each, rather than guessing a round total. Include the calls and the revision rounds; they are easy to forget and rarely small.</p>
</div>
<div class="about sheet">
<h2>Add a buffer for surprises</h2>
<p>Projects rarely run exactly to estimate. A buffer of 10 to 20% of the labour cost is a common starting point &mdash; set it higher when the scope is vague, the client is new, or the project depends on things outside your control (their content, their feedback turnaround, third-party approvals).</p>
</div>
<div class="about sheet">
<h2>Pass through hard costs separately</h2>
<p>Stock assets, subcontractors, licences, travel &mdash; costs that are not your labour should be listed separately from the buffer, so the client can see exactly what they are paying for.</p>
</div>
<div class="about sheet">
<h2>Decide on a deposit</h2>
<p>A deposit of 30 to 50% before work starts reduces your exposure if the client disappears or the project stalls, and it filters out people who were never serious. It is standard practice, not an imposition.</p>
</div>
<div class="about sheet">
<h2>The formula</h2>
<p><code>labour = hours &times; hourly rate</code></p>
<p><code>total = labour + (labour &times; buffer%) + pass-through costs &minus; discount</code></p>
</div>
<div class="sheet">
<h2>Worked example</h2>
<p>30 estimated hours at $85/hr, $200 in pass-through costs, a 15% buffer, no discount, and a 30% deposit.</p>
<dl class="stats">
<div><dt>Labour</dt><dd>30 &times; $85 = $2,550.00</dd></div>
<div><dt>Buffer (15% of labour)</dt><dd>$382.50</dd></div>
<div><dt>Plus pass-through costs</dt><dd>$2,550 + $382.50 + $200 = <b>$3,132.50 quote</b></dd></div>
<div><dt>Deposit to ask upfront (30%)</dt><dd>$939.75</dd></div>
<div><dt>You earn per hour, on plan</dt><dd>($3,132.50 &minus; $200) &divide; 30 = $97.75/hr</dd></div>
<div><dt>You earn per hour, if it runs 25% over</dt><dd>($3,132.50 &minus; $200) &divide; 37.5 = $78.20/hr</dd></div>
</dl>
<p class="note">Try your own numbers in the <a href="../project-quote-calculator/">project quote calculator</a> &mdash; it shows both of those per-hour figures live as you adjust the buffer and discount.</p>
</div>
<div class="about sheet">
<h2>Watch what a discount really costs you</h2>
<p>A discount comes straight out of your labour and buffer, not out of the pass-through costs. Watch the "on plan" hourly figure as you raise a discount &mdash; it drops faster than the headline percentage suggests, because it is being taken off a total that already includes your buffer.</p>
<p>Once the invoice is out, the next step is getting paid on time &mdash; see the <a href="../freelance-invoice-guide/">invoice guide</a>.</p>
</div>
'''),
 'freelance-invoice-guide': dict(
   title='Freelance Invoice Guide: What to Include and How to Get Paid Faster',
   desc='What a freelance invoice needs, how to number and word it, and a worked example with tax added.',
   related='invoice',
   body='''
<div class="about sheet">
<h2>What every invoice needs</h2>
<p>A unique invoice number, your details and the client's, the issue date and the due date, an itemised list of charges, the total owed, and how to pay you. Clear terms stated up front make it easier to chase a late payment later &mdash; there is no ambiguity to argue about.</p>
</div>
<div class="about sheet">
<h2>Invoice numbering</h2>
<p>A simple sequential number (0001, 0002&hellip;) is enough for most freelancers. Whatever system you pick, keep it consistent and never reuse a number &mdash; it matters for your own records and, in most countries, for tax purposes.</p>
</div>
<div class="about sheet">
<h2>Payment terms</h2>
<p>"Due on receipt" gets paid fastest but can feel aggressive with a new client. Net 7 or Net 14 balances speed with normal business practice; Net 30 is the most common default but ties up your cash the longest. Net 60 mostly benefits the client, not you &mdash; avoid it unless you have no leverage to negotiate.</p>
</div>
<div class="about sheet">
<h2>Tax on invoices</h2>
<p>If you are required to charge tax, VAT or GST, add it as its own line, name it correctly for your jurisdiction, and include your tax registration number if you have one. Rules vary by country and by what you sell &mdash; check your own obligations rather than assuming a rate.</p>
</div>
<div class="sheet">
<h2>Worked example</h2>
<p>Two line items &mdash; a $1,200 flat-fee design project, and 5 hours of consulting at $90/hr &mdash; with 8% tax added.</p>
<dl class="stats">
<div><dt>Website design</dt><dd>1 &times; $1,200.00 = $1,200.00</dd></div>
<div><dt>Consulting (5 hrs &times; $90)</dt><dd>$450.00</dd></div>
<div><dt>Subtotal</dt><dd>$1,650.00</dd></div>
<div><dt>Tax (8%)</dt><dd>$132.00</dd></div>
<div><dt>Total due</dt><dd><b>$1,782.00</b></dd></div>
</dl>
<p class="note">Build this exact invoice in the <a href="../invoice-generator/">invoice generator</a> and print or save it as a PDF &mdash; nothing you type leaves your browser.</p>
</div>
<div class="about sheet">
<h2>Getting paid on time</h2>
<p>State your terms on the invoice itself, send it the same day the work is delivered, and follow up promptly once it is overdue rather than waiting. If a payment does go late, the <a href="../late-payment-fee-calculator/">late payment fee calculator</a> works out interest and a flat fee you can add to the balance &mdash; check your own contract and local rules before charging one.</p>
</div>
'''),
}


def build_article(slug):
    e = lambda x: html.escape(x, quote=True)
    A = ARTICLES[slug]
    lang, hl, locale = 'en', 'en', 'en_US'
    mp = MAPS['en']

    hdr = copy.copy(header)
    hdr.find('a', class_='brand')['href'] = '/'
    _brand = hdr.find('a', class_='brand')
    for _n in list(_brand.contents):
        if isinstance(_n, str):
            _n.extract()
    _brand.append(BeautifulSoup('<span class="wm">Rate<span class="lk">Lark</span></span>', 'html.parser'))
    opt = hdr.find('select', id='lang').find('option', value=lang)
    opt['selected'] = 'selected'
    ui = UI[lang]
    kb = BeautifulSoup('<button type="button" class="kbtn" data-palette aria-label="%s"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg><span class="kt">%s</span><kbd>Ctrl K</kbd></button>' % (ui['search'], ui['search']), 'html.parser')
    hdr.find('div', class_='pick').insert(0, kb)
    cur = hdr.find('select', id='cur')
    if cur is not None and cur.find_parent('label') is not None:
        cur.find_parent('label').decompose()

    ft = copy.copy(footer); translate(ft, mp)
    ft.append(BeautifulSoup('<p><a href="/privacy/">%s</a> &middot; <a href="mailto:%s">%s</a></p>' % (UI[lang]['privacy'], CONTACT_EMAIL, CONTACT_LABEL[lang]), 'html.parser'))

    body_sec = BeautifulSoup(A['body'], 'html.parser')
    related = BeautifulSoup(related_tools_html(lang, A['related']), 'html.parser').div

    title = A['title'] + ' | RateLark'
    description = A['desc']
    url = '%s/en/%s/' % (BASE, slug)
    faq_ld = []
    ld = [{'@context': 'https://schema.org', '@type': 'Article', 'headline': A['title'],
           'url': url, 'inLanguage': hl, 'description': description}]

    ld_json = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    page = f'''<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="RateLark">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
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
<link rel="preload" href="/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css?v={VER['fonts.css']}">
<link rel="stylesheet" href="../../assets/app.css?v={VER['app.css']}">
<script type="application/ld+json">{ld_json}</script>
</head>
<body data-tool="">
<div class="tfx" aria-hidden="true"><i class="arc l"></i><i class="arc r"></i></div>
{hdr}
<main id="main">
<div class="head">
<h1>{e(A['title'])}</h1>
<p>{e(A['desc'])}</p>
</div>
{body_sec}
{related}
</main>
{ft}
<script src="../../assets/palette.js?v={VER['palette.js']}" defer></script>
</body>
</html>
'''
    return page


def build_hub(lang):
    """Per-language hub page at /{lang}/: an H1, the tagline, and a card for every tool."""
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
    cur = hdr.find('select', id='cur')
    if cur is not None and cur.find_parent('label') is not None:
        cur.find_parent('label').decompose()   # no currency picker on the hub
    ui = UI[lang]
    kb = BeautifulSoup('<button type="button" class="kbtn" data-palette aria-label="%s"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg><span class="kt">%s</span><kbd>Ctrl K</kbd></button>' % (ui['search'], ui['search']), 'html.parser')
    hdr.find('div', class_='pick').insert(0, kb)

    ft = copy.copy(footer); translate(ft, mp)
    langs_nav = BeautifulSoup('<nav class="langs" aria-label="Languages"></nav>', 'html.parser').nav
    for code, nm, h, _ in LANGS:
        a = BeautifulSoup('<a></a>', 'html.parser').a
        a['href'] = '/%s/' % code
        a['hreflang'] = h
        a['lang'] = code
        if code == lang:
            a['aria-current'] = 'true'
        a.string = nm
        langs_nav.append(a)
    ft.insert(0, langs_nav)
    ft.append(BeautifulSoup('<p><a href="/privacy/">%s</a> &middot; <a href="mailto:%s">%s</a></p>' % (UI[lang]['privacy'], CONTACT_EMAIL, CONTACT_LABEL[lang]), 'html.parser'))

    e = lambda x: html.escape(x, quote=True)
    title = 'RateLark: %s' % HUB_H1[lang]
    description = HUB_DESC[lang]
    url = '%s/%s/' % (BASE, lang)
    cards = ''.join(hub_card(lang, t) for t in REG)
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s/%s/">' % (h, BASE, c) for c, _, h, _ in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s/en/">' % BASE
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title.split(' | ')[0],
          'url': url, 'inLanguage': hl, 'description': description}
    ld_json = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    page = f'''<!doctype html>
<html lang="{lang}" dir="{dirn}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
{alts}
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
<link rel="preload" href="/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css?v={VER['fonts.css']}">
<link rel="stylesheet" href="/assets/app.css?v={VER['app.css']}">
<script type="application/ld+json">{ld_json}</script>
</head>
<body data-tool="">
<div class="tfx" aria-hidden="true"><i class="arc l"></i><i class="arc r"></i></div>
{hdr}
<main id="main">
<div class="head">
<h1>{e(HUB_H1[lang])}</h1>
<p>{e(tr('Freelance pricing, quote, invoice and tax tools in one place.', lang))}</p>
</div>
<h2 class="sr-only">{e(UI[lang]['all'])}</h2>
<div class="hub-grid">{cards}</div>
</main>
{ft}
<script src="/assets/palette.js?v={VER['palette.js']}" defer></script>
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
.hub-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;margin-top:1.4rem}
.hub-card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1rem;text-decoration:none;color:inherit}
.hub-card:hover,.hub-card:focus-visible{border-color:var(--edge)}
.hub-card .hc-top{display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem}
.hub-card .hc-ico{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;background:var(--bg);color:var(--ink)}
.hub-card .hc-cat{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.hub-card h3{margin:0;font:700 1.05rem var(--display);color:var(--ink)}
.hub-card p{margin:.35rem 0 0;color:var(--muted);font-size:.88rem;line-height:1.4}
a.btn{text-decoration:none;display:inline-block}
.cta-row{margin:0 0 1.25rem}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
'''
PAL_CSS = open(os.path.join(HERE, 'palette.css'), encoding='utf-8').read()
PAL_JS = open(os.path.join(HERE, 'palette.js'), encoding='utf-8').read()
HERO_CSS = open(os.path.join(HERE, 'hero.css'), encoding='utf-8').read()
HERO_JS = open(os.path.join(HERE, 'hero.js'), encoding='utf-8').read()
PLAIN_CSS = ('html{background:#03050a}body{font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;max-width:36rem;margin:3rem auto;padding:0 1rem;color:#F2F5FA;background:radial-gradient(ellipse 90vw 40vh at 50% -12vh,rgba(79,124,255,.45),transparent 70%),#03050a;min-height:100vh}\n'
             'a{color:#FFD84D}li{margin:.4rem 0}h1{font-size:1.9rem;margin:0 0 .5rem}h2{font-size:1.15rem;margin:1.6rem 0 .3rem}p{color:#C3CCDD}\n')
PLUGIN_CSS = ''.join(open(os.path.join(HERE, 'tools', t, 'tool.css'), encoding='utf-8').read() for t in PLUGINS)
SHELL_JS = open(os.path.join(HERE, 'shell.js'), encoding='utf-8').read()
CONNECT_JS = open(os.path.join(HERE, 'connect.js'), encoding='utf-8').read()
LZ_JS = open(os.path.join(HERE, 'tools', 'ppp-pricing-calculator', 'lz-string.min.js'), encoding='utf-8').read()
_css = css + extra_css + bgart.css() + PAL_CSS + PLUGIN_CSS
# self-hosted subset of the two always-loaded families (Bricolage Grotesque 600/700,
# Instrument Sans 400/500/600), latin + latin-ext only -- matches what the site actually
# uses. Avoids the external fonts.googleapis.com -> fonts.gstatic.com render-blocking
# chain on the critical path. hi/ar still lazy-load Noto Sans Devanagari/Arabic from
# Google Fonts on demand (see FONTS in hourkit.html) -- that's not on the critical path.
FONT_CSS = """@font-face{font-family:'Bricolage Grotesque';font-style:normal;font-weight:600;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Bricolage Grotesque';font-style:normal;font-weight:600;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:'Bricolage Grotesque';font-style:normal;font-weight:700;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Bricolage Grotesque';font-style:normal;font-weight:700;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:'Instrument Sans';font-style:normal;font-weight:400;font-display:swap;src:url(/assets/fonts/instrument-sans-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Instrument Sans';font-style:normal;font-weight:400;font-display:swap;src:url(/assets/fonts/instrument-sans-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:'Instrument Sans';font-style:normal;font-weight:500;font-display:swap;src:url(/assets/fonts/instrument-sans-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Instrument Sans';font-style:normal;font-weight:500;font-display:swap;src:url(/assets/fonts/instrument-sans-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
@font-face{font-family:'Instrument Sans';font-style:normal;font-weight:600;font-display:swap;src:url(/assets/fonts/instrument-sans-latin.woff2) format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Instrument Sans';font-style:normal;font-weight:600;font-display:swap;src:url(/assets/fonts/instrument-sans-latin-ext.woff2) format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
"""
VER = {n: hashlib.sha1(t.encode()).hexdigest()[:8] for n, t in
       (('app.css', _css), ('i18n.js', i18n_js), ('app.js', main_js), ('palette.js', PAL_JS), ('shell.js', SHELL_JS), ('connect.js', CONNECT_JS), ('lz-string.min.js', LZ_JS), ('fonts.css', FONT_CSS),
        ('palette.css', PAL_CSS), ('hero.css', HERO_CSS), ('hero.js', HERO_JS), ('plain.css', PLAIN_CSS))}
for _t in PLUGINS:
    for _f in ('engine', 'ui'):
        VER['%s:%s' % (_f, _t)] = hashlib.sha1(open(os.path.join(HERE, 'tools', _t, _f + '.js'), 'rb').read()).hexdigest()[:8]
write('assets/app.css', _css)
write('assets/i18n.js', i18n_js)
write('assets/app.js', main_js)
write('assets/palette.js', PAL_JS)
write('assets/palette.css', PAL_CSS)
write('assets/shell.js', SHELL_JS)
write('assets/connect.js', CONNECT_JS)
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
                   'cat': CATS[t['cat']][code], 'url': '/%s/%s/' % (code, url_slug(t['slug']))})
    write('assets/tools-%s.json' % code, json.dumps({'ui': UI[code], 'tools': tl,
          'langs': [{'code': c, 'name': n} for c, n, _, _ in LANGS]}, ensure_ascii=False))

count = 0
for code, *_ in LANGS:
    for tool in TOOLS:
        if tool == 'tax':
            continue   # Stage 3: replaced by four fixed-country pages, below
        write('%s/%s/index.html' % (code, url_slug(tool)), build_page(code, tool))
        count += 1
    for country in TAX_SLUG:
        write('%s/%s/index.html' % (code, TAX_SLUG[country]), build_tax_page(code, country))
        count += 1
    write('%s/index.html' % code, build_hub(code))
    count += 1

# Stage 5: the three how-to articles, English only (see ARTICLES above)
for slug in ARTICLES:
    write('en/%s/index.html' % slug, build_article(slug))
    count += 1

# sitemap with hreflang alternates
urls = ['<url><loc>%s/</loc><lastmod>%s</lastmod></url>' % (BASE, TODAY)]
for code, *_ in LANGS:
    hub_alts = ''.join('<xhtml:link rel="alternate" hreflang="%s" href="%s/%s/"/>' % (h, BASE, c) for c, _, h, _ in LANGS)
    hub_alts += '<xhtml:link rel="alternate" hreflang="x-default" href="%s/en/"/>' % BASE
    urls.append('<url><loc>%s/%s/</loc><lastmod>%s</lastmod>%s</url>' % (BASE, code, TODAY, hub_alts))
    for tool in TOOLS:
        if tool == 'tax':
            continue
        slug = url_slug(tool)
        alts = ''.join('<xhtml:link rel="alternate" hreflang="%s" href="%s/%s/%s/"/>' % (h, BASE, c, slug)
                       for c, _, h, _ in LANGS)
        alts += '<xhtml:link rel="alternate" hreflang="x-default" href="%s/en/%s/"/>' % (BASE, slug)
        urls.append('<url><loc>%s/%s/%s/</loc><lastmod>%s</lastmod>%s</url>' % (BASE, code, slug, TODAY, alts))
    for country, slug in TAX_SLUG.items():
        alts = ''.join('<xhtml:link rel="alternate" hreflang="%s" href="%s/%s/%s/"/>' % (h, BASE, c, slug)
                       for c, _, h, _ in LANGS)
        alts += '<xhtml:link rel="alternate" hreflang="x-default" href="%s/en/%s/"/>' % (BASE, slug)
        urls.append('<url><loc>%s/%s/%s/</loc><lastmod>%s</lastmod>%s</url>' % (BASE, code, slug, TODAY, alts))
for slug in ARTICLES:
    urls.append('<url><loc>%s/en/%s/</loc><lastmod>%s</lastmod></url>' % (BASE, slug, TODAY))
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
      + '\n'.join(urls) + '\n</urlset>\n')
write('robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % BASE)

# Stage 2: permanent redirects from every old tool URL to its new keyword slug, for every
# language. Written expanded (one line per language) rather than with Cloudflare Pages'
# :placeholder syntax, since that can't be verified against a live Cloudflare deploy from here;
# expanded rules have no such dependency and match exactly what Data 1 in the brief asks for.
redirect_lines = []
for old_slug, new_slug in URL_SLUG.items():
    for code, *_ in LANGS:
        redirect_lines.append('/%s/%s/ /%s/%s/ 301' % (code, old_slug, code, new_slug))
write('_redirects', '\n'.join(redirect_lines) + '\n')
write('.nojekyll', '')

HEAD_COMMON = f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#EDF1F5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E1622" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/plain.css?v={VER['plain.css']}">"""
write('assets/plain.css', PLAIN_CSS)

e = lambda x: html.escape(x, quote=True)
# root page: cinematic dark landing with a 3D lark (assets/hero.*)
TOOL_LABELS = [('hourly-rate', 'Hourly rate'), ('quote', 'Project quote'), ('invoice', 'Invoice'),
               ('markup-margin', 'Markup & margin'), ('retainer', 'Retainer vs hourly'),
               ('late-fee', 'Late fee'), ('tax', 'Tax set-aside')]
chips = ''.join('<li><a data-tool="%s" href="/en/%s/">%s</a></li>' % (url_slug(t), url_slug(t), n) for t, n in TOOL_LABELS)
DESC_EN = {t['slug']: tool_desc('en', t['slug']) for t in REG}
def tile(t):
    slug = t['slug']
    label = dict(TOOL_LABELS).get(slug) or tool_name('en', slug)
    return ('<a class="tile t-%s" data-cat="%s" data-tool="%s" href="/en/%s/">'
            '<span class="tile-top"><span class="ico">%s</span><span class="cat">%s</span></span>'
            '<span class="tile-body"><h3>%s</h3><p>%s</p></span>'
            '<span class="ex"><i>Example</i>%s</span></a>'
            % (t['size'], t['cat'], url_slug(slug), url_slug(slug), icon_svg(t['icon']), CATS[t['cat']]['en'], label, e(DESC_EN[slug]), e(t['sample'])))
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
                        % (url_slug(t['slug']), url_slug(t['slug']), icon_svg(t['icon'], 20), e(tool_name('en', t['slug'])), e(tool_desc('en', t['slug'])))
                        for t in REG if t['cat'] == c)
        cols += '<div class="mc"><h3>%s</h3><ul>%s</ul></div>' % (e(CATS[c]['en']), items)
    return cols
def footer_tools():
    out = ''
    for c in _cats():
        out += '<div class="fc"><h3>%s</h3><ul>%s</ul></div>' % (e(CATS[c]['en']), ''.join(
            '<li><a data-tool="%s" href="/en/%s/">%s</a></li>' % (url_slug(t['slug']), url_slug(t['slug']), e(tool_name('en', t['slug']))) for t in REG if t['cat'] == c))
    return out
cat_order = []
for t in REG:
    if t['cat'] not in cat_order: cat_order.append(t['cat'])
filters = '<button type="button" data-cat="all" aria-pressed="true">All</button>' + ''.join(
    '<button type="button" data-cat="%s" aria-pressed="false">%s</button>' % (c, CATS[c]['en']) for c in cat_order)
langs = ''.join('<a href="/%s/" hreflang="%s" lang="%s">%s</a>' % (c, h, c, n) for c, n, h, _ in LANGS)
write('assets/hero.js', HERO_JS)
write('assets/hero.css', HERO_CSS)
LAYERS = logo.hero_art()
MEGA = mega_html()
FOOTER_TOOLS = footer_tools()
LANGLIS = ''.join('<li><a href="/%s/" hreflang="%s" lang="%s">%s</a></li>' % (c, h, c, n) for c, n, h, _ in LANGS)
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
<link rel="preload" href="/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css?v={VER['fonts.css']}">
<link rel="stylesheet" href="/assets/hero.css?v={VER['hero.css']}">
<link rel="stylesheet" href="/assets/palette.css?v={VER['palette.css']}">
</head>
<body>
<div class="fx" aria-hidden="true"><i class="arc l"></i><i class="arc r"></i></div>
<header class="nav">
  <a class="brand" href="/"><span class="mark" aria-hidden="true"></span><span class="wm">Rate<span class="lk">Lark</span></span></a>
  <ul class="links"><li class="has-menu"><button type="button" class="menu-btn" id="tools-btn" aria-expanded="false" aria-controls="tools-menu">Tools {CHEV}</button><div class="mega" id="tools-menu" role="region" aria-label="All tools" hidden><div class="mega-in">{MEGA}</div><a class="mega-all" data-tool="{url_slug('hourly-rate')}" href="/en/{url_slug('hourly-rate')}/">Open the tool pages &rarr;</a></div></li><li><a href="#why">Why RateLark</a></li><li><a href="#langs">Languages</a></li><li><a href="/privacy/">Privacy</a></li></ul>
  <div class="navr"><button type="button" class="kbtn" data-palette aria-label="Search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"></circle><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path></svg><span class="kt">Search</span><kbd>Ctrl K</kbd></button><a class="pill" data-tool="{url_slug('hourly-rate')}" href="/en/{url_slug('hourly-rate')}/">Try it</a></div>
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
    <div class="cta"><a class="pill light" data-tool="{url_slug('hourly-rate')}" href="/en/{url_slug('hourly-rate')}/">Get started</a><a class="pill solid" data-tool="{url_slug('invoice')}" href="/en/{url_slug('invoice')}/">Make an invoice</a></div>
  </section>
</main>
<section class="why" id="why" aria-labelledby="why-h">
  <h2 id="why-h">Built to be used in a minute</h2>
  <ul>
    <li><span class="wi">{icon_svg('clock', 22)}</span><b>Free, with no sign-up</b><p>Open a tool and the answer is already on screen. No account, no email, no card.</p></li>
    <li><span class="wi">{icon_svg('receipt', 22)}</span><b>Private by design</b><p>Every calculation runs in your browser. What you type is never uploaded.</p></li>
    <li><span class="wi">{icon_svg('globe', 22)}</span><b>Made for the world</b><p>Nine languages, 19 currencies and tax rules for the US, UK, Canada and Australia.</p></li>
  </ul>
  <div class="why-cta"><a class="pill light" data-tool="{url_slug('hourly-rate')}" href="/en/{url_slug('hourly-rate')}/">Get started</a><button type="button" class="pill" data-palette>Search every tool <kbd>Ctrl K</kbd></button></div>
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
<script type="module" src="/assets/hero.js?v={VER['hero.js']}"></script>
<script src="/assets/palette.js?v={VER['palette.js']}" defer></script>
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
<p>Most fonts are hosted on RateLark and never touch a third party. If you switch to Hindi or Arabic, the page loads that language's font from Google Fonts, so Google receives your IP address and browser details at that point. The site is served by a hosting provider, which may keep standard server logs (IP address, page requested, time).</p>
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
    src = os.path.join(STATIC, f)
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(OUT, 'assets', f), dirs_exist_ok=True)
    else:
        shutil.copy(src, os.path.join(OUT, f))

write('assets/fonts.css', FONT_CSS)

# security + caching headers (Cloudflare Pages and Netlify both read _headers)
write('_headers', """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
/assets/*
  Cache-Control: public, max-age=31536000, immutable
""")
print('built %d pages for %s into %s' % (count, BASE, OUT))
