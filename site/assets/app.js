
(function(){
"use strict";
const NIL={value:'',textContent:'',innerHTML:'',hidden:false,dataset:{},style:{},options:[],children:[],offsetHeight:0,addEventListener(){},focus(){},select(){},setAttribute(){},getAttribute(){return null},appendChild(){},closest(){return null},querySelector(){return NIL},querySelectorAll(){return []},scrollIntoView(){},classList:{add(){},remove(){}}};
const $=(s,r=document)=>r.querySelector(s)||NIL, $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const store={
  get(k,d){try{const v=localStorage.getItem('fr:'+k);return v===null?d:JSON.parse(v)}catch(e){return d}},
  set(k,v){try{localStorage.setItem('fr:'+k,JSON.stringify(v))}catch(e){}}
};
let LOC, NLOC, lang='en', MAP=Object.create(null);
const LOCS={en:undefined,es:'es',pt:'pt-BR',fr:'fr',de:'de',hi:'hi-IN',ar:'ar-u-nu-latn',zh:'zh-CN',id:'id'};
const t=(k,v)=>{let r=MAP[k];if(r===undefined)r=k;return v?r.replace(/\{(\w+)\}/g,(m,x)=>v[x]!==undefined?v[x]:m):r};
const guessCountry=()=>{try{const r=((navigator.language||'').split('-')[1]||'').toUpperCase();return {GB:'uk',CA:'ca',AU:'au'}[r]||'us'}catch(e){return 'us'}};
const guessLang=()=>{const l=((navigator.language||'en').slice(0,2)).toLowerCase();return Object.prototype.hasOwnProperty.call(LOCS,l)?l:'en'};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const REGION_CUR={US:'USD',GB:'GBP',CA:'CAD',AU:'AUD',NZ:'NZD',SG:'SGD',CH:'CHF',IN:'INR',PK:'PKR',BD:'BDT',PH:'PHP',BR:'BRL',MX:'MXN',ZA:'ZAR',NG:'NGN',KE:'KES',AE:'AED',SA:'SAR',DE:'EUR',FR:'EUR',ES:'EUR',IT:'EUR',NL:'EUR',IE:'EUR',PT:'EUR',AT:'EUR',BE:'EUR',FI:'EUR'};
const guessCur=()=>{try{const r=((navigator.language||'').split('-')[1]||'').toUpperCase();return REGION_CUR[r]||'USD'}catch(e){return 'USD'}};
let cur=store.get('cur',guessCur());
const money=(n,d=2,c)=>{
  if(!isFinite(n))return '—';
  try{return new Intl.NumberFormat(NLOC,{style:'currency',currency:c||cur,minimumFractionDigits:d,maximumFractionDigits:d}).format(n)}
  catch(e){return n.toFixed(d)}
};
const sym=(c)=>{
  try{return new Intl.NumberFormat(NLOC,{style:'currency',currency:c||cur,currencyDisplay:'narrowSymbol'}).formatToParts(0).find(p=>p.type==='currency').value}
  catch(e){return cur}
};
const pct=n=>isFinite(n)?(Math.round(n*10)/10).toLocaleString(NLOC,{maximumFractionDigits:1})+'%':'—';
const val=id=>{const v=parseFloat($('#'+id).value);return isFinite(v)?v:0};
const setT=(id,t)=>{$('#'+id).textContent=t};
const isoDate=d=>new Date(d.getTime()-d.getTimezoneOffset()*6e4).toISOString().slice(0,10);
const parseD=s=>{const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(s||'');return m?new Date(+m[1],+m[2]-1,+m[3]):null};
const fmtD=d=>d?d.toLocaleDateString(LOC,{year:'numeric',month:'short',day:'numeric'}):'—';

/* ---------- tabs ---------- */
const TOOLS=['hourly-rate','quote','invoice','markup-margin','retainer','late-fee','tax'];
const TITLES={
  'hourly-rate':'Freelance Hourly Rate Calculator (with Tax and Time Off) | RateLark',
  'quote':'Freelance Project Quote Calculator | RateLark',
  'invoice':'Free Invoice Generator (PDF, No Sign-Up) | RateLark',
  'markup-margin':'Markup and Margin Calculator | RateLark',
  'retainer':'Retainer vs Hourly Billing Calculator | RateLark',
  'late-fee':'Late Payment Fee and Interest Calculator | RateLark',
  'tax':'Freelance tax set-aside estimate | RateLark'
};
const PAGE=(document.body&&document.body.dataset.tool)||'';
let current=PAGE||'hourly-rate';
function show(id){
  if(id==='us-tax')id='tax';
  if(!TOOLS.includes(id))id='hourly-rate';
  current=id;
  TOOLS.forEach(t=>{
    $('#tool-'+t).hidden=(t!==id);
    const b=$('#tab-'+t);
    b.setAttribute('aria-selected',t===id?'true':'false');
    b.tabIndex=t===id?0:-1;
  });
  document.documentElement.dataset.tool=id;
  document.title=t(TITLES[id]);
  try{history.replaceState(null,'','#'+id)}catch(e){try{location.hash=id}catch(_){}}
  const b=$('#tab-'+id); if(b&&b.scrollIntoView){try{b.scrollIntoView({block:'nearest',inline:'center'})}catch(e){}}
}
if(!PAGE)$$('.tab').forEach(b=>b.addEventListener('click',()=>{show(b.dataset.tool);window.scrollTo(0,0)}));
if(!PAGE)$('.tabs').addEventListener('keydown',e=>{
  if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;
  const i=TOOLS.indexOf(current), n=(i+(e.key==='ArrowRight'?1:-1)+TOOLS.length)%TOOLS.length;
  show(TOOLS[n]); $('#tab-'+TOOLS[n]).focus();
});
if(!PAGE)window.addEventListener('hashchange',()=>show(location.hash.slice(1)));

/* ---------- calculators ---------- */
function hourly(){
  const T=val('h-income'),E=val('h-exp');
  const tr=Math.min(Math.max(val('h-tax'),0),90)/100;
  const off=Math.min(Math.max(val('h-off'),0),52), hpw=val('h-hours');
  const hours=(52-off)*hpw, profit=T/(1-tr), rev=profit+E;
  const rate=hours>0?rev/hours:NaN;
  setT('h-rate',money(rate));
  setT('h-day',money(rate*8));
  setT('h-month',money(rev/12,0));
  setT('h-year',money(rev,0));
  setT('h-hrs',hours>0?t('{n} hrs',{n:hours.toLocaleString(NLOC,{maximumFractionDigits:0})}):'—');
  setT('h-taxamt',money(profit-T,0));
}
function markup(){
  const c=val('m-cost'), mode=$('#m-mode').value, v=val('m-val');
  let price=NaN, note='';
  if(mode==='markup')price=c*(1+v/100);
  else if(mode==='margin'){ if(v<100)price=c/(1-v/100); else note=t('Margin must be below 100%.'); }
  else price=v;
  const profit=price-c, mu=c>0?profit/c*100:NaN, mg=price>0?profit/price*100:NaN;
  setT('m-price',money(price)); setT('m-profit',money(profit)); setT('m-mu',pct(mu)); setT('m-mg',pct(mg));
  if(!note&&isFinite(mu)&&isFinite(mg))note=t('A {mu} markup is a {mg} margin. Markup is measured against cost, margin against price.',{mu:pct(mu),mg:pct(mg)});
  setT('m-note',note);
  $('#m-pre').hidden=(mode!=='price'); $('#m-suf').hidden=(mode==='price');
}
function late(){
  const a=val('l-amt'), due=parseD($('#l-due').value), asof=parseD($('#l-asof').value), rate=val('l-rate'), flat=val('l-flat');
  let days=0; if(due&&asof)days=Math.round((asof-due)/864e5);
  const over=days>0, daily=a*rate/100/365, interest=over?daily*days:0, f=over?flat:0;
  setT('l-total',money(a+interest+f));
  setT('l-days',over?(days===1?t('1 day'):t('{n} days',{n:days})):t('Not overdue'));
  setT('l-orig',money(a)); setT('l-int',money(interest)); setT('l-flat-out',money(f)); setT('l-daily',money(daily));
  setT('l-note',over?'':t('Interest and fees start after the due date.'));
}

function quote(){
  const h=val('q-hours'), r=val('q-rate'), x=val('q-exp'), b=val('q-buf')/100;
  const d=Math.min(Math.max(val('q-disc'),0),100)/100, dp=Math.min(Math.max(val('q-dep'),0),100)/100;
  const labour=h*r, buf=labour*b, sub=labour+buf+x, disc=sub*d, total=sub-disc;
  setT('q-total',money(total)); setT('q-labour',money(labour)); setT('q-bufamt',money(buf));
  setT('q-expout',money(x)); setT('q-discamt',disc>0?'−'+money(disc):money(0)); setT('q-depamt',money(total*dp));
  setT('q-eff',h>0?t('{amount}/hr',{amount:money((total-x)/h)}):'—');
  setT('q-over',h>0?t('{amount}/hr',{amount:money((total-x)/(h*1.25))}):'—');
}
const idl=n=>n==='Tax'?t('Tax ID'):t('{name} no.',{name:t(n)});
const sgn=n=>isFinite(n)?(n>=0?'+':'−')+money(Math.abs(n)):'—';
function retainer(){
  const f=val('r-fee'), h=val('r-hours'), r=val('r-rate');
  const hourly=h*r, diff=f-hourly;
  setT('r-lbl',diff>=0?t('Retainer earns you more, per month, by'):t('Hourly would earn you more, per month, by'));
  setT('r-diff',money(Math.abs(diff)));
  setT('r-eff',h>0?t('{amount}/hr',{amount:money(f/h)}):'—');
  setT('r-hourly',money(hourly));
  setT('r-be',r>0?t('{n} hrs',{n:(f/r).toLocaleString(NLOC,{maximumFractionDigits:1})}):'—');
  setT('r-under',sgn(f-h*0.7*r));
  setT('r-over',sgn(f-h*1.5*r));
}
const TCUR={us:'USD',uk:'GBP',ca:'CAD',au:'AUD'};
function bands(x,br){let tax=0,prev=0;for(const b of br){if(x>prev)tax+=(Math.min(x,b[0])-prev)*b[1];prev=b[0]}return tax}
function setax(){
  const c=$('#s-country').value, cc=TCUR[c]||'USD';
  const m=n=>money(n,0,cc);
  const p=Math.max(val('s-profit'),0);
  $$('#tool-tax [data-c]').forEach(el=>{el.hidden=el.dataset.c.split(' ').indexOf(c)<0});
  const S=sym(cc); $$('#tool-tax .tsym').forEach(el=>{el.textContent=S});
  let total=0;
  if(c==='us'){
    const it=Math.min(Math.max(val('s-itax'),0),60)/100, base=Math.max(val('s-base'),0);
    const ne=p*0.9235; let ss=0, med=0;
    if(ne>=400){ss=Math.min(ne,base)*0.124;med=ne*0.029}
    const se=ss+med, half=se/2, inc=Math.max(p-half,0)*it; total=se+inc;
    setT('s-se',m(se)); setT('s-ss',m(ss)); setT('s-med',m(med)); setT('s-half',m(half)); setT('s-inc',m(inc));
  }else if(c==='uk'){
    const pa=Math.max(0,12570-Math.max(0,(p-100000)/2)), ti=Math.max(0,p-pa);
    const inc=Math.min(ti,37700)*0.2+Math.min(Math.max(ti-37700,0),125140-37700)*0.4+Math.max(ti-125140,0)*0.45;
    const ni=Math.max(0,Math.min(p,50270)-12570)*0.06+Math.max(0,p-50270)*0.02;
    total=inc+ni; setT('s-tax',m(inc)); setT('s-ni',m(ni));
  }else if(c==='ca'){
    const pr=Math.min(Math.max(val('s-prov-rate'),0),30)/100;
    const cpp=Math.max(0,Math.min(p,74600)-3500)*0.119+Math.max(0,Math.min(p,85000)-74600)*0.08;
    const ti=Math.max(0,p-cpp/2);
    let bpa=16452; if(ti>181440)bpa=ti>=258482?14829:16452-(16452-14829)*(ti-181440)/(258482-181440);
    const fed=Math.max(0,bands(ti,[[58523,.14],[117045,.205],[181440,.26],[258482,.29],[Infinity,.33]])-bpa*0.14);
    const prov=ti*pr; total=fed+prov+cpp;
    setT('s-fed',m(fed)); setT('s-prov',m(prov)); setT('s-cpp',m(cpp));
  }else{
    const inc=bands(p,[[18200,0],[45000,.15],[135000,.3],[190000,.37],[Infinity,.45]]), med=p*0.02;
    total=inc+med; setT('s-tax',m(inc)); setT('s-medl',m(med));
  }
  setT('s-total',m(total)); setT('s-q',m(total/4)); setT('s-share',p>0?pct(total/p*100):'—');
  const rows=$$('#s-stats > div').filter(r=>!r.hidden);
  rows.forEach((r,i)=>{r.style.borderBottom=(i===rows.length-1)?'0':''});
}

/* ---------- invoice ---------- */
let items=store.get('items',[{d:'Website design',q:1,p:1200},{d:'Revisions (per hour)',q:3,p:80}]);
if(!Array.isArray(items))items=[];
function drawItems(){
  const box=$('#items'); box.innerHTML='';
  items.forEach((it,i)=>{
    const el=document.createElement('div'); el.className='item';
    el.innerHTML=
      '<input class="ctl" data-dyn data-i="'+i+'" data-f="d" aria-label="'+esc(t('Item {n} description',{n:i+1}))+'" placeholder="'+esc(t('Description'))+'" value="'+esc(it.d)+'">'+
      '<div class="row">'+
        '<label><span class="mini" data-dyn>'+esc(t('Qty'))+'</span><input class="ctl" type="number" inputmode="decimal" min="0" step="any" data-i="'+i+'" data-f="q" value="'+esc(it.q)+'"></label>'+
        '<label><span class="mini" data-dyn>'+esc(t('Rate'))+'</span><input class="ctl" type="number" inputmode="decimal" min="0" step="any" data-i="'+i+'" data-f="p" value="'+esc(it.p)+'"></label>'+
        '<button type="button" class="btn alt sm" data-dyn data-rm="'+i+'" aria-label="'+esc(t('Remove item {n}',{n:i+1}))+'">'+esc(t('Remove'))+'</button>'+
      '</div>';
    box.appendChild(el);
  });
}
function invData(){
  const date=parseD($('#i-date').value), terms=$('#i-terms').value, tax=val('i-tax');
  let dueTxt;
  if(terms==='receipt')dueTxt=t('On receipt');
  else dueTxt=date?fmtD(new Date(date.getFullYear(),date.getMonth(),date.getDate()+(+terms))):'—';
  const rows=items.map(it=>{const q=+it.q||0,p=+it.p||0;return{d:it.d||'',q,p,a:q*p}});
  const sub=rows.reduce((s,r)=>s+r.a,0), tx=sub*tax/100;
  return{
    taxName:$('#i-taxname').value, taxId:$('#i-taxid').value.trim(), from:$('#i-from').value.trim(), to:$('#i-to').value.trim(), no:$('#i-no').value.trim()||'—',
    issued:fmtD(date), due:dueTxt, tax, rows, sub, tx, total:sub+tx, notes:$('#i-notes').value.trim()
  };
}
function invoice(){
  const d=invData();
  const ph=x=>'<span class="ph">'+esc(t(x))+'</span>';
  const rows=d.rows.map(r=>'<tr><td>'+(esc(r.d)||ph('Item'))+'</td><td class="n">'+r.q+'</td><td class="n">'+money(r.p)+'</td><td class="n">'+money(r.a)+'</td></tr>').join('');
  $('#doc').innerHTML=
    '<div class="doc-head"><div><div class="doc-title">'+esc(t('Invoice'))+'</div><div>'+esc(t('No.'))+' '+esc(d.no)+'</div></div>'+
    '<div><div>'+esc(t('Issued:'))+' '+esc(d.issued)+'</div><div>'+esc(t('Due:'))+' '+esc(d.due)+'</div></div></div>'+
    '<div class="doc-parties"><div><h2>'+esc(t('From'))+'</h2><p class="pl">'+(d.from?esc(d.from):ph('Your name and address'))+'</p>'+(d.taxId?'<p class="pl" style="margin-top:.3rem">'+esc(idl(d.taxName))+': '+esc(d.taxId)+'</p>':'')+'</div>'+
    '<div><h2>'+esc(t('Bill to'))+'</h2><p class="pl">'+(d.to?esc(d.to):ph('Client name and address'))+'</p></div></div>'+
    '<div class="doc-scroll"><table><thead><tr><th>'+esc(t('Description'))+'</th><th class="n">'+esc(t('Qty'))+'</th><th class="n">'+esc(t('Rate'))+'</th><th class="n">'+esc(t('Amount'))+'</th></tr></thead><tbody>'+rows+'</tbody></table></div>'+
    '<div class="doc-tot"><div><span>'+esc(t('Subtotal'))+'</span><span>'+money(d.sub)+'</span></div>'+
    (d.tax>0?'<div><span>'+esc(t(d.taxName))+' ('+esc(d.tax)+'%)</span><span>'+money(d.tx)+'</span></div>':'')+
    '<div class="grand"><span>'+esc(t('Total due'))+'</span><span>'+money(d.total)+'</span></div></div>'+
    (d.notes?'<div class="doc-notes"><h2>'+esc(t('Notes'))+'</h2><p class="pl">'+esc(d.notes)+'</p></div>':'');
}
function invoiceText(){
  const d=invData();
  const lines=[t('Invoice')+' '+t('No.')+' '+d.no, t('Issued:')+' '+d.issued, t('Due:')+' '+d.due,'',t('From')+':',d.from||'-'];
  if(d.taxId)lines.push(idl(d.taxName)+': '+d.taxId);
  lines.push('',t('Bill to')+':',d.to||'-','',t('Items')+':');
  d.rows.forEach(r=>lines.push('- '+(r.d||t('Item'))+': '+r.q+' x '+money(r.p)+' = '+money(r.a)));
  lines.push('',t('Subtotal')+': '+money(d.sub));
  if(d.tax>0)lines.push(t(d.taxName)+' ('+d.tax+'%): '+money(d.tx));
  lines.push(t('Total due')+': '+money(d.total));
  if(d.notes)lines.push('',t('Notes')+':',d.notes);
  return lines.join('\n');
}

/* ---------- shared ---------- */
function all(){hourly();quote();markup();retainer();late();setax();invoice()}
function syms(){const s=sym();$$('.sym').forEach(el=>{el.textContent=s})}
let tt;
const toast=m=>{const t=$('#toast');t.textContent=m;clearTimeout(tt);tt=setTimeout(()=>{t.textContent=''},5000)};
async function copy(text,msg){
  try{await navigator.clipboard.writeText(text);$('#fallback').hidden=true;toast(msg)}
  catch(e){const f=$('#fallback');f.hidden=false;f.value=text;f.focus();f.select();toast(t('Copy is blocked here. The text is selected below, copy it manually.'))}
}

document.addEventListener('input',e=>{
  const t=e.target;
  if(t.dataset&&t.dataset.f){
    const it=items[+t.dataset.i]; if(!it)return;
    it[t.dataset.f]=t.dataset.f==='d'?t.value:(parseFloat(t.value)||0);
    store.set('items',items);
  }
  if(t.matches&&t.matches('[data-p]'))store.set('f:'+t.id,t.value);
  all();
});
document.addEventListener('click',e=>{
  const rm=e.target.closest&&e.target.closest('[data-rm]');
  if(rm){items.splice(+rm.dataset.rm,1);store.set('items',items);drawItems();invoice();}
});
$('#add-item').addEventListener('click',()=>{
  items.push({d:'',q:1,p:0});store.set('items',items);drawItems();invoice();
  const last=$$('#items .item').pop(); if(last)last.querySelector('input').focus();
});
$('#lang').addEventListener('change',e=>{const l=e.target.value;if(PAGE){store.set('lang',l);location.href='../../'+l+'/'+PAGE+'/'}else applyLang(l)});
$('#cur').addEventListener('change',e=>{cur=e.target.value;store.set('cur',cur);syms();all()});
$('#print').addEventListener('click',()=>{try{window.print()}catch(e){toast(t('Printing is blocked here. Use Copy as text.'))}});
$('#copy-inv').addEventListener('click',()=>copy(invoiceText(),t('Invoice copied as text')));
$('#share').addEventListener('click',async()=>{
  const url=PAGE?location.href.split('#')[0]:location.href.split('#')[0]+'#'+current;
  if(navigator.share){
    try{await navigator.share({title:document.title,url});return}
    catch(e){if(e&&e.name==='AbortError')return}
  }
  copy(url,t('Link copied'));
});

/* ---------- language ---------- */
const SEL='.tab,.cur>span,h1,h2,.head p,.l,.hint,.mini,dt,.lbl,.note,summary,.about p,details p,.btn,.suf,option,footer p,.howto li';
const FONTS={hi:'Noto+Sans+Devanagari:wght@400;600;700',ar:'Noto+Sans+Arabic:wght@400;600;700'};
function loadFont(l){
  if(!FONTS[l]||document.getElementById('f-'+l))return;
  const k=document.createElement('link'); k.id='f-'+l; k.rel='stylesheet';
  k.href='https://fonts.googleapis.com/css2?family='+FONTS[l]+'&display=swap';
  document.head.appendChild(k);
}
function buildMap(l){
  MAP=Object.create(null);
  const a=(window.FR_L||{})[l], en=window.FR_EN||[];
  if(!a)return;
  en.forEach((k,i)=>{if(a[i])MAP[k]=a[i]});
}
function applyLang(l){
  if(!Object.prototype.hasOwnProperty.call(LOCS,l))l='en';
  lang=l; store.set('lang',l); LOC=LOCS[l]; NLOC=(l==='ar'?'en':LOC); buildMap(l);
  loadFont(l);
  if(!PAGE){
    const h=document.documentElement; h.lang=l; h.dir=(l==='ar'?'rtl':'ltr');
    $$(SEL).forEach(el=>{
      if(el.hasAttribute('data-dyn')||el.children.length||el.closest('.doc')||el.closest('#cur')||el.closest('#lang'))return;
      if(el.dataset.en===undefined){const x=el.textContent.trim();if(!x)return;el.dataset.en=x}
      el.textContent=t(el.dataset.en);
    });
    $$('[placeholder]').forEach(el=>{
      if(el.hasAttribute('data-dyn'))return;
      if(el.dataset.enPh===undefined)el.dataset.enPh=el.getAttribute('placeholder');
      el.setAttribute('placeholder',t(el.dataset.enPh));
    });
    document.title=t(TITLES[current]);
  }
  $('#lang').value=l;
  drawItems(); syms(); all();
  window.dispatchEvent(new Event('resize'));
}

/* ---------- init ---------- */
const today=new Date();
$('#i-date').value=isoDate(today);
$('#l-asof').value=isoDate(today);
$('#l-due').value=isoDate(new Date(today.getFullYear(),today.getMonth(),today.getDate()-20));
$$('[data-p]').forEach(el=>{const v=store.get('f:'+el.id,null);if(v!==null)el.value=v});
if(store.get('f:s-country',null)===null)$('#s-country').value=guessCountry();
if(!Array.from($('#cur').options).some(o=>o.value===cur))cur='USD';
$('#cur').value=cur;
if(PAGE){document.documentElement.dataset.tool=PAGE;applyLang(document.documentElement.lang||'en')}
else{applyLang(store.get('lang',guessLang()));show(location.hash.slice(1))}
const setTabsH=()=>document.documentElement.style.setProperty('--tabsh',$('.tabs').offsetHeight+'px');
setTabsH(); window.addEventListener('resize',setTabsH);
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(setTabsH);
})();
