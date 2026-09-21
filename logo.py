"""RateLark logo: three golden feather blades (stacked fan, tips at the left, tails curling down at the right).
Coordinates are in a 1254 x 1254 design space traced from the brand reference. Used for logo.svg, favicon,
share image and the homepage hero (each blade is its own layer so the hero can tilt in 3D)."""
VB = '195 115 920 895'          # x y w h of the mark inside the design space
VBW, VBH = 920, 895

# each blade: tip, top edge (tip -> tail), tail, lower edge (tail -> tip)
BLADES = [
  dict(top=[(215,140.4),(250,188.4),(330,233.4),(430,267.4),(560,303.4),(700,334.5),(850,373),(960,430.6),(1030,485.6),(1070,558.6),(1090,655.6),(1095,755.6),(1088,840.6)],
       low=[(1088,840.6),(1072,792.6),(1042,716.6),(985,644.6),(900,593.6),(800,554.3),(700,524.5),(600,495.2),(500,477.4),(400,457.4),(322,425.4),(300,355.4),(265,275.4),(235,205.4),(215,140.4)]),
  dict(top=[(326,440),(400,478),(500,508),(620,542),(760,588),(880,635),(970,703),(1030,782),(1056,868),(1046,935)],
       low=[(1046,935),(1018,882),(968,828),(896,797),(800,772),(700,752),(600,728),(510,690),(430,620),(370,530),(326,440)]),
  dict(top=[(548,746),(612,773),(700,795),(790,817),(880,843),(950,882),(996,942),(1008,990)],
       low=[(1008,990),(978,942),(928,904),(862,883),(772,875),(692,863),(624,836),(574,789),(548,746)]),
]

def _catmull(pts, t=0.5):
    """open Catmull-Rom spline through pts -> list of cubic segments"""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        c1 = (p1[0] + (p2[0]-p0[0]) * t / 3 * 2 * 0.5 * 1.0, p1[1] + (p2[1]-p0[1]) * t / 3 * 2 * 0.5 * 1.0)
        c2 = (p2[0] - (p3[0]-p1[0]) * t / 3 * 2 * 0.5 * 1.0, p2[1] - (p3[1]-p1[1]) * t / 3 * 2 * 0.5 * 1.0)
        out.append((c1, c2, p2))
    return out

def blade_path(i):
    b = BLADES[i]
    f = lambda v: '%.1f' % v
    d = 'M%s %s' % (f(b['top'][0][0]), f(b['top'][0][1]))
    for c1, c2, p in _catmull(b['top']) + _catmull(b['low']):
        d += 'C%s %s %s %s %s %s' % (f(c1[0]), f(c1[1]), f(c2[0]), f(c2[1]), f(p[0]), f(p[1]))
    return d + 'Z'

DEFS = ('<defs>'
 '<linearGradient id="g1" gradientUnits="userSpaceOnUse" x1="260" y1="780" x2="1090" y2="260"><stop offset="0" stop-color="#EE9200"/><stop offset=".22" stop-color="#FFB800"/><stop offset=".48" stop-color="#FFE45C"/><stop offset=".6" stop-color="#FFF6BC"/><stop offset=".75" stop-color="#FFD21F"/><stop offset="1" stop-color="#FFC200"/></linearGradient>'
 '<linearGradient id="g2" gradientUnits="userSpaceOnUse" x1="320" y1="920" x2="1060" y2="580"><stop offset="0" stop-color="#EA8C00"/><stop offset=".25" stop-color="#FFB400"/><stop offset=".5" stop-color="#FFDD4A"/><stop offset=".62" stop-color="#FFF0A0"/><stop offset=".78" stop-color="#FFCB1A"/><stop offset="1" stop-color="#FFB800"/></linearGradient>'
 '<linearGradient id="g3" gradientUnits="userSpaceOnUse" x1="540" y1="980" x2="1010" y2="770"><stop offset="0" stop-color="#E68600"/><stop offset=".3" stop-color="#FFAE00"/><stop offset=".55" stop-color="#FFD940"/><stop offset=".68" stop-color="#FFEE96"/><stop offset=".85" stop-color="#FFC814"/><stop offset="1" stop-color="#FFB000"/></linearGradient>'
 '<linearGradient id="lt" gradientUnits="userSpaceOnUse" x1="260" y1="200" x2="1090" y2="640"><stop offset="0" stop-color="#FFE23B"/><stop offset=".5" stop-color="#FFF04D"/><stop offset="1" stop-color="#FFF98A"/></linearGradient>'
 '<linearGradient id="rim" gradientUnits="userSpaceOnUse" x1="215" y1="135" x2="1095" y2="700"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/><stop offset=".6" stop-color="#FFF7A8" stop-opacity=".9"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".95"/></linearGradient>'
 '<linearGradient id="sk" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#FFD24A" stop-opacity=".95"/><stop offset="1" stop-color="#FFB000" stop-opacity="0"/></linearGradient>'
 '<linearGradient id="fl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFB000" stop-opacity="0"/><stop offset=".5" stop-color="#FFE38A" stop-opacity="1"/><stop offset="1" stop-color="#FFB000" stop-opacity="0"/></linearGradient>'
 '<filter id="blur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="26"/></filter>'
 '<filter id="blur2" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="9"/></filter>'
 '</defs>')

# light "glass" facet on each blade: everything above the crease line is the brighter yellow
CREASE = [
  "M180 130 L1140 130 L1140 470 L560 470 Z",           # blade 1: light upper part (drawn clipped to the blade)
  "M300 400 L1100 400 L1100 690 L520 690 Z",
  "M520 640 L1030 640 L1030 830 L520 830 Z",
]
CREASE_LINES = [((330, 250), (1095, 640)), ((330, 445), (1060, 780)), ((560, 690), (1010, 900))]

def blade(i, uid=''):
    d = blade_path(i)
    (x1, y1), (x2, y2) = CREASE_LINES[i]
    cid = f'bc{i}{uid}'
    # polygon on the upper-left side of the crease line, clipped to the blade
    far = (x1 - 200 * (y2 - y1) / 100, y1 + 200 * (x2 - x1) / 100 * 0)  # unused helper values
    poly = f'M{x1-400} {y1-400*(y2-y1)/(x2-x1)-900} L{x2+400} {y2+400*(y2-y1)/(x2-x1)-900} L{x2+400} {y2+400*(y2-y1)/(x2-x1)} L{x1-400} {y1-400*(y2-y1)/(x2-x1)} Z'
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<path d="{d}" fill="url(#g{i+1})"/>'
            f'<g clip-path="url(#{cid})"><path d="{poly}" fill="url(#lt)" opacity=".92"/></g>'
            f'<path d="{d}" fill="none" stroke="url(#rim)" stroke-width="5" stroke-linejoin="round"/>')

def glow(vb=VB):
    return ''.join(f'<path d="{blade_path(i)}" fill="#FFAA00" filter="url(#blur)" opacity=".75"/>' for i in range(3))

STREAKS = [((236,180),(118,124),5),((262,246),(84,204),4),((330,393),(150,352),4),((470,560),(230,500),3),((430,610),(70,528),3),((560,706),(310,640),4),((640,832),(400,790),3)]
def streaks():
    o = ''
    for (x1, y1), (x2, y2), w in STREAKS:
        o += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="url(#sk)" stroke-width="{w}" stroke-linecap="round" gradientTransform="rotate(0)"/>'
    o += ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFE9A0"/>' for x, y, r in ((165,375,5),(255,392,3.5),(485,690,4)))
    return o

def floorlight():
    return ('<ellipse cx="740" cy="998" rx="380" ry="22" fill="#FFB000" opacity=".45" filter="url(#blur2)"/>'
            '<rect x="380" y="994" width="720" height="5" rx="2.5" fill="url(#fl)"/>')

ART_VB = '40 90 1180 960'
def art():
    """the full brand artwork: glow, light streaks, blades, floor light (for the hero and the share image)"""
    return f'<svg viewBox="{ART_VB}" xmlns="http://www.w3.org/2000/svg">{DEFS}{glow()}{streaks()}{body()}{floorlight()}</svg>'

def body():
    return ''.join(blade(i) for i in range(3))

def mark(vb=VB):
    return f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">{DEFS}{body()}</svg>'

def sweep_layer(vb=None):
    vb = vb or ART_VB
    clip = ''.join(f'<path d="{blade_path(i)}"/>' for i in range(3))
    return (f'<svg class="ly lysweep" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><clipPath id="allb">{clip}</clipPath>'
            '<linearGradient id="swp" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFCD8" stop-opacity=".9"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient></defs>'
            '<g clip-path="url(#allb)"><g class="sw"><rect x="-420" y="0" width="300" height="1300" fill="url(#swp)" transform="skewX(-22)"/></g></g></svg>')

def layer(i, vb=None):
    vb = vb or ART_VB
    if i == 'bg':
        return f'<svg class="ly lybg" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{DEFS}{glow()}{streaks()}{floorlight()}</svg>'
    return f'<svg class="ly ly{i}" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{DEFS}{blade(i, "L")}</svg>'

def icon():
    s = 40 / VBW
    return (f'<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">{DEFS}<rect width="64" height="64" rx="15" fill="#0a1226"/>'
            f'<rect x=".75" y=".75" width="62.5" height="62.5" rx="14.3" fill="none" stroke="#FFD84D" stroke-opacity=".4" stroke-width="1.5"/>'
            f'<g transform="translate({12 - 195*s:.3f} {(64 - VBH*s)/2 - 115*s:.3f}) scale({s:.5f})">{body()}</g></svg>')

if __name__ == '__main__':
    open('static/logo.svg', 'w').write(mark() + '\n')
    open('static/favicon.svg', 'w').write(icon() + '\n')
    print('logo.svg + favicon.svg written')


def hero_art():
    """Single SVG for the homepage hero: one set of gradient ids, no blur filters, three blade groups the page can animate."""
    clip = ''.join(f'<path d="{blade_path(i)}"/>' for i in range(3))
    extra = ('<defs><clipPath id="allb">' + clip + '</clipPath>'
             '<linearGradient id="swp" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFF" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#FFFBD0" stop-opacity=".95"/><stop offset="1" stop-color="#FFF" stop-opacity="0"/></linearGradient></defs>')
    floor = ('<ellipse cx="740" cy="998" rx="330" ry="12" fill="#FFB000" opacity=".22"/>'
             '<rect x="380" y="994" width="720" height="5" rx="2.5" fill="url(#fl)"/>')
    blades = ''.join(f'<g class="pl pl{i}"><g class="bl bl{i}">{blade(i, "H")}</g></g>' for i in (2, 1, 0))
    sweep = ('<g clip-path="url(#allb)"><g class="sw"><rect x="-420" y="0" width="300" height="1300" fill="url(#swp)" '
             'transform="skewX(-22)"/></g></g>')
    return (f'<svg class="art" viewBox="{ART_VB}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">'
            f'{DEFS}{extra}<g class="fx">{streaks()}{floor}</g>{blades}{sweep}</svg>')
