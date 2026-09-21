#!/usr/bin/env python3
"""
Refresh data/ppp.json for the PPP Pricing Localizer.

  price level  = World Bank PPP conversion factor (PA.NUS.PPP) / official exchange rate (PA.NUS.FCRF)
                 (US = 1.0; India is about 0.23 = prices are roughly a quarter of US prices)
  exchange rate = open.er-api.com (free, attribution required), one snapshot per refresh

Run:  python3 scripts/refresh_ppp_data.py      (needs internet; standard library only)
Then rebuild the site with build.py. World Bank data is CC BY 4.0. Re-run every few months.
"""
import datetime, json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', 'ppp.json')

# iso2, iso3, currency, regions (used for the region presets)
COUNTRIES = [
 ('IN','IND','INR','emerging south_asia'), ('BR','BRA','BRL','emerging latam'), ('ID','IDN','IDR','emerging sea'), ('NG','NGA','NGN','emerging africa'),
 ('PK','PAK','PKR','south_asia'), ('BD','BGD','BDT','south_asia'), ('LK','LKA','LKR','south_asia'), ('NP','NPL','NPR','south_asia'),
 ('PH','PHL','PHP','sea'), ('VN','VNM','VND','sea'), ('TH','THA','THB','sea'), ('MY','MYS','MYR','sea'), ('SG','SGP','SGD','sea'),
 ('MX','MEX','MXN','latam'), ('AR','ARG','ARS','latam'), ('CL','CHL','CLP','latam'), ('CO','COL','COP','latam'), ('PE','PER','PEN','latam'), ('UY','URY','UYU','latam'), ('CR','CRI','CRC','latam'), ('DO','DOM','DOP','latam'),
 ('KE','KEN','KES','africa'), ('ZA','ZAF','ZAR','africa'), ('GH','GHA','GHS','africa'), ('TZ','TZA','TZS','africa'), ('UG','UGA','UGX','africa'), ('EG','EGY','EGP','africa mena'), ('MA','MAR','MAD','africa mena'),
 ('GB','GBR','GBP','europe'), ('DE','DEU','EUR','europe'), ('FR','FRA','EUR','europe'), ('ES','ESP','EUR','europe'), ('IT','ITA','EUR','europe'), ('NL','NLD','EUR','europe'),
 ('BE','BEL','EUR','europe'), ('AT','AUT','EUR','europe'), ('IE','IRL','EUR','europe'), ('PT','PRT','EUR','europe'), ('FI','FIN','EUR','europe'), ('GR','GRC','EUR','europe'),
 ('SE','SWE','SEK','europe'), ('NO','NOR','NOK','europe'), ('DK','DNK','DKK','europe'), ('CH','CHE','CHF','europe'), ('PL','POL','PLN','europe'), ('CZ','CZE','CZK','europe'),
 ('HU','HUN','HUF','europe'), ('RO','ROU','RON','europe'), ('UA','UKR','UAH','europe'), ('TR','TUR','TRY','europe mena'),
 ('CA','CAN','CAD','north_america'), ('AU','AUS','AUD','asia_pacific'), ('NZ','NZL','NZD','asia_pacific'), ('JP','JPN','JPY','asia_pacific'), ('KR','KOR','KRW','asia_pacific'),
 ('HK','HKG','HKD','asia_pacific'), ('CN','CHN','CNY','asia_pacific'), ('AE','ARE','AED','mena'), ('SA','SAU','SAR','mena'), ('IL','ISR','ILS','mena'),
]

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)

def wb(indicator):
    d = get('https://api.worldbank.org/v2/country/all/indicator/%s?format=json&date=2019:2027&per_page=5000' % indicator)
    out = {}
    for r in d[1]:
        if r['value'] is not None:
            out.setdefault(r['countryiso3code'], {})[int(r['date'])] = r['value']
    return out, d[0].get('lastupdated')

ppp, upd = wb('PA.NUS.PPP')
fcr, _ = wb('PA.NUS.FCRF')
fx = get('https://open.er-api.com/v6/latest/USD')
assert fx.get('result') == 'success', fx

countries, missing = {}, []
for iso2, iso3, cur, regions in COUNTRIES:
    year = next((y for y in sorted(ppp.get(iso3, {}), reverse=True) if y in fcr.get(iso3, {})), None)
    rate = fx['rates'].get(cur)
    if year is None or not rate:
        missing.append(iso2); continue
    plr = ppp[iso3][year] / fcr[iso3][year]
    countries[iso2] = {'cur': cur, 'plr': round(plr, 4), 'year': year, 'fx': round(rate, 6), 'regions': regions.split()}

out = {
  'version': 1,
  'generated': datetime.date.today().isoformat(),
  'priceLevel': {'source': 'World Bank, PA.NUS.PPP / PA.NUS.FCRF (International Comparison Program)', 'license': 'CC BY 4.0', 'lastUpdated': upd},
  'fx': {'source': 'Exchange Rate API (open.er-api.com)', 'date': fx.get('time_last_update_utc', '')[:16]},
  'countries': countries,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w'), indent=1, sort_keys=True)
print('wrote', len(countries), 'countries; skipped (no data):', missing or 'none')
