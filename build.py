#!/usr/bin/env python3
"""BoltSpec static site generator. Zero dependencies (Python 3.9+).
   python build.py  ->  ./dist   (≈360 pages + sitemap + robots + IndexNow key)"""
import json, math, shutil, html, datetime, urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
CFG = json.loads((ROOT / "config.json").read_text())
DIST = ROOT / "dist"
BASE = CFG["base_url"].rstrip("/")
SITE = CFG["site_name"]
TODAY = datetime.date.today().isoformat()

# ───────────────────────── DATA ─────────────────────────
# (d mm, pitch mm, coarse?)  ISO 261/262, within ISO 898-1 scope (M1.6–M39)
METRIC = [(1.6,.35,1),(2,.4,1),(2.5,.45,1),(3,.5,1),(4,.7,1),(5,.8,1),(6,1,1),(8,1.25,1),(10,1.5,1),
          (12,1.75,1),(14,2,1),(16,2,1),(18,2.5,1),(20,2.5,1),(22,2.5,1),(24,3,1),(27,3,1),(30,3.5,1),
          (33,3.5,1),(36,4,1),(39,4,1),
          (8,1,0),(10,1.25,0),(10,1,0),(12,1.5,0),(12,1.25,0),(14,1.5,0),(16,1.5,0),(18,1.5,0),
          (20,1.5,0),(22,1.5,0),(24,2,0),(27,2,0),(30,2,0),(33,2,0),(36,3,0)]
# class: (proof MPa d<=16, proof MPa d>16, tensile MPa, max d, note)
CLASSES = {"4.6":(225,225,400,39,"low-carbon steel"),
           "5.8":(380,380,520,39,"low/medium-carbon steel"),
           "8.8":(580,600,800,39,"quenched & tempered medium-carbon steel"),
           "10.9":(830,830,1040,39,"quenched & tempered alloy steel"),
           "12.9":(970,970,1220,39,"quenched & tempered alloy steel"),
           "A2-70":(450,450,700,24,"austenitic stainless steel (304), 0.2% proof stress used"),
           "A4-80":(600,600,800,24,"austenitic stainless steel (316), 0.2% proof stress used")}
# ISO 273 clearance holes (close, medium, coarse), hex across flats ISO 4014/4017, socket key ISO 4762
M_EXTRA = {1.6:(1.7,1.8,2,3.2,1.5),2:(2.2,2.4,2.6,4,1.5),2.5:(2.7,2.9,3.1,5,2),3:(3.2,3.4,3.6,5.5,2.5),
           4:(4.3,4.5,4.8,7,3),5:(5.3,5.5,5.8,8,4),6:(6.4,6.6,7,10,5),8:(8.4,9,10,13,6),
           10:(10.5,11,12,16,8),12:(13,13.5,14.5,18,10),14:(15,15.5,16.5,21,12),16:(17,17.5,18.5,24,14),
           18:(19,20,21,27,14),20:(21,22,24,30,17),22:(23,24,26,34,17),24:(25,26,28,36,19),
           27:(28,30,32,41,19),30:(31,33,35,46,22),33:(34,36,38,50,24),36:(37,39,42,55,27),
           39:(40,42,45,60,None)}
# Unified inch: (label, d in, tpi, series, tap drill, drill dia in, close clr, free clr, hex wrench)
INCH = [("#4-40",.112,40,"UNC","#43",.0890,"#32","#30",None),("#6-32",.138,32,"UNC","#36",.1065,"#27","#25",None),
        ("#8-32",.164,32,"UNC","#29",.1360,"#18","#16",None),("#10-24",.190,24,"UNC","#25",.1495,"#9","#7",None),
        ("#10-32",.190,32,"UNF","#21",.1590,"#9","#7",None),
        ("1/4-20",.25,20,"UNC","#7",.2010,"F","H","7/16"),("1/4-28",.25,28,"UNF","#3",.2130,"F","H","7/16"),
        ("5/16-18",.3125,18,"UNC","F",.2570,"P","Q","1/2"),("5/16-24",.3125,24,"UNF","I",.2720,"P","Q","1/2"),
        ("3/8-16",.375,16,"UNC","5/16",.3125,"W","X","9/16"),("3/8-24",.375,24,"UNF","Q",.3320,"W","X","9/16"),
        ("7/16-14",.4375,14,"UNC","U",.3680,"29/64","15/32","5/8"),("7/16-20",.4375,20,"UNF","25/64",.3906,"29/64","15/32","5/8"),
        ("1/2-13",.5,13,"UNC","27/64",.4219,"33/64","17/32","3/4"),("1/2-20",.5,20,"UNF","29/64",.4531,"33/64","17/32","3/4"),
        ("9/16-12",.5625,12,"UNC","31/64",.4844,"37/64","19/32","13/16"),("9/16-18",.5625,18,"UNF","33/64",.5156,"37/64","19/32","13/16"),
        ("5/8-11",.625,11,"UNC","17/32",.5312,"41/64","21/32","15/16"),("5/8-18",.625,18,"UNF","37/64",.5781,"41/64","21/32","15/16"),
        ("3/4-10",.75,10,"UNC","21/32",.6562,"49/64","25/32","1-1/8"),("3/4-16",.75,16,"UNF","11/16",.6875,"49/64","25/32","1-1/8"),
        ("7/8-9",.875,9,"UNC","49/64",.7656,"57/64","29/32","1-5/16"),("7/8-14",.875,14,"UNF","13/16",.8125,"57/64","29/32","1-5/16"),
        ("1-8",1.0,8,"UNC","7/8",.8750,"1-1/64","1-1/32","1-1/2"),("1-12",1.0,12,"UNF","59/64",.9219,"1-1/64","1-1/32","1-1/2")]
# SAE J429 proof strength psi: grade -> [(max d, psi)]
GRADES = {"2":[(.75,55000),(1.5,33000)],"5":[(1.0,85000),(1.5,74000)],"8":[(1.5,120000)]}
K_DRY, K_LUBE, PRELOAD = 0.20, 0.15, 0.75

# ───────────────────────── ENGINEERING ─────────────────────────
def m_area(d,p): return math.pi/4*(d-0.9382*p)**2                  # mm², ISO 898-1
def in_area(d,n): return 0.7854*(d-0.9743/n)**2                    # in², ASME B1.1
def m_calc(d,p,cls):
    sp = CLASSES[cls][0] if d<=16 else CLASSES[cls][1]
    A = m_area(d,p); F = PRELOAD*sp*A                              # N
    return dict(A=A, sp=sp, F=F, dry=K_DRY*d/1000*F, lube=K_LUBE*d/1000*F)   # N·m
def in_calc(d,n,g):
    sp = next(s for mx,s in GRADES[g] if d<=mx)
    A = in_area(d,n); F = PRELOAD*sp*A                             # lbf
    return dict(A=A, sp=sp, F=F, dry=K_DRY*d*F/12, lube=K_LUBE*d*F/12)       # lb·ft
def sig(x,n=3):
    if x==0: return "0"
    r = round(x, n-1-int(math.floor(math.log10(abs(x)))))
    return f"{r:,.0f}" if r>=100 else f"{r:g}"
def g(x): return f"{x:g}"
def mname(d,p): return f"M{g(d)} x {g(p)}"
def mslug(d,p): return f"m{g(d)}x{g(p)}"
def islug(lbl): return lbl.replace("#","no").replace("/","-")

# ───────────────────────── TEMPLATING ─────────────────────────
PAGES = []   # (url path, lastmod)
GV = f'<meta name="google-site-verification" content="{CFG["google_verification"]}">' if CFG.get("google_verification") else ""
def amazon(q, text):
    u = "https://www.amazon.com/s?k=" + urllib.parse.quote_plus(q)
    if CFG["amazon_tag"]: u += "&tag=" + CFG["amazon_tag"]
    return f'<a href="{u}" rel="sponsored nofollow noopener" target="_blank">{html.escape(text)}</a>'
def wrench_pick(nm):
    if nm<5: return "torque screwdriver","torque screwdriver"
    if nm<25: return "1/4 inch drive torque wrench","1/4″ drive torque wrench"
    if nm<100: return "3/8 inch drive torque wrench","3/8″ drive torque wrench"
    if nm<340: return "1/2 inch drive torque wrench","1/2″ drive torque wrench"
    return "3/4 inch drive torque wrench","3/4″ drive torque wrench"
def ad():
    c = CFG["adsense_client"]
    return (f'<ins class="adsbygoogle" style="display:block" data-ad-client="{c}" data-ad-format="auto" '
            f'data-full-width-responsive="true"></ins><script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>') if c else ""
def table(head, rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>"+"".join(f"<td>{c}</td>" for c in r)+"</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'
def faq(qa):
    ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qa]}
    body = "".join(f"<h3>{html.escape(q)}</h3><p>{html.escape(a)}</p>" for q,a in qa)
    return f'<h2>FAQ</h2>{body}<script type="application/ld+json">{json.dumps(ld)}</script>'
DISCLAIMER = ('<p class="warn"><b>Reference values only.</b> Calculated from standard formulas with assumed friction '
              '(K) and 75% of proof load. Real joints vary with coating, lubricant, washers and thread condition. '
              'For safety-critical joints always use the equipment manufacturer’s specified torque.</p>')
LOGO = '<svg viewBox="0 0 32 32"><path d="M16 2l12.1 7v14L16 30 3.9 23V9z" fill="#f26a1b"/><circle cx="16" cy="16" r="6" fill="#0e1420"/></svg>'
SRCH = '<div class="srch"><input type="search" placeholder="Search a thread – M10, 1/4-20…" aria-label="Search threads" autocomplete="off"><div class="res"></div></div>'
SEARCH = []
def bolt_svg(dia, pitch, wrench):
    th = "".join(f'<line x1="{x}" y1="52" x2="{x-7}" y2="98"/>' for x in range(150,292,9))
    return f"""<svg viewBox="0 0 340 170" fill="none" stroke="currentColor" stroke-width="1.6" font-family="Inter,sans-serif" font-size="12">
<rect x="42" y="30" width="52" height="90" rx="3" fill="currentColor" fill-opacity=".08"/><line x1="42" y1="52" x2="94" y2="52"/><line x1="42" y1="98" x2="94" y2="98"/>
<path d="M94 52h192l8 8v30l-8 8H94z" fill="currentColor" fill-opacity=".04"/><g stroke-width="1">{th}</g>
<g stroke="#f26a1b" stroke-width="1.2"><line x1="24" y1="30" x2="24" y2="120"/><line x1="18" y1="30" x2="36" y2="30"/><line x1="18" y1="120" x2="36" y2="120"/>
<line x1="312" y1="52" x2="312" y2="98"/><line x1="300" y1="52" x2="318" y2="52"/><line x1="300" y1="98" x2="318" y2="98"/>
<line x1="177" y1="40" x2="186" y2="40"/><line x1="177" y1="36" x2="177" y2="48"/><line x1="186" y1="36" x2="186" y2="48"/></g>
<g fill="currentColor" stroke="none" font-weight="600"><text x="24" y="140" text-anchor="middle">{wrench}</text><text x="24" y="154" text-anchor="middle" font-size="10" font-weight="400">wrench</text>
<text x="312" y="118" text-anchor="middle">{dia}</text><text x="181" y="28" text-anchor="middle">{pitch}</text></g></svg>"""
def tile(lab, val, unit, alt="", cls=""):
    return f'<div class="tile {cls}"><span class="lab">{lab}</span><span class="val">{val}<small>{unit}</small></span><span class="alt">{alt}</span></div>'
def page(path, title, desc, body, crumbs=()):
    home = path.strip("/") == ""
    path = path.strip("/"); url = f"/{path}/" if path else "/"
    out = DIST / path / "index.html"; out.parent.mkdir(parents=True, exist_ok=True)
    c = CFG["adsense_client"]
    adjs = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={c}" crossorigin="anonymous"></script>' if c else ""
    bc = ' › '.join([f'<a href="/">{SITE}</a>'] + [f'<a href="{u}">{t}</a>' for t,u in crumbs])
    SEARCH.append([title.split(" | ")[0].split(":")[0], url])
    out.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0e1420">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE}{url}">{GV}<link rel="icon" href="/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">{adjs}</head><body>
<header><div class="hin"><a class="logo" href="/">{LOGO}<span>Bolt<i>Spec</i></span></a><nav><a href="/metric-bolt-torque/">Metric torque</a>
<a href="/inch-bolt-torque/">Inch torque</a><a href="/tap-drill/">Tap drill</a><a href="/calculator/">Calculator</a></nav>
{"" if home else SRCH}</div></header>
<main>{"" if home else f'<p class="bc">{bc}</p>'}{body}</main>
<footer><div class="fin">{DISCLAIMER}<p>As an Amazon Associate this site earns from qualifying purchases.
<a href="/about/">About &amp; method</a> · <a href="/privacy/">Privacy</a> · Updated {TODAY}</p></div></footer>
<script src="/site.js" defer></script></body></html>""", encoding="utf-8")
    PAGES.append(url)

CALC_JS = """<script>
function bc(){const q=id=>parseFloat(document.getElementById(id).value)||0;
const d=q('c_d'),A=q('c_a'),sp=q('c_sp'),k=q('c_k'),pct=q('c_pct')/100,inch=document.getElementById('c_u').value=='in';
const F=pct*sp*A;let o;
if(inch){const t=k*d*F;o=`<b>${(t/12).toFixed(1)} lb·ft</b> (${t.toFixed(0)} lb·in, ${(t*0.113).toFixed(1)} N·m) — preload ${F.toFixed(0)} lbf`}
else{const t=k*d/1000*F;o=`<b>${t.toFixed(1)} N·m</b> (${(t*0.7376).toFixed(1)} lb·ft, ${(t*8.851).toFixed(0)} lb·in) — preload ${(F/1000).toFixed(2)} kN`}
document.getElementById('c_out').innerHTML=o}
document.addEventListener('input',bc);document.addEventListener('DOMContentLoaded',bc);</script>"""
def calc_widget(d,A,sp,unit):
    u = ("mm","mm²","MPa") if unit=="mm" else ("in","in²","psi")
    return f"""<div class="calc"><h2>Adjust for your joint</h2><input type="hidden" id="c_u" value="{unit}">
<div class="cg"><label>Diameter ({u[0]})<input id="c_d" value="{g(d)}"></label><label>Stress area ({u[1]})<input id="c_a" value="{A:.4g}"></label>
<label>Proof strength ({u[2]})<input id="c_sp" value="{g(sp)}"></label>
<label>K (nut factor)<input id="c_k" value="0.20" step="0.01" type="number"></label>
<label>% of proof load<input id="c_pct" value="75" type="number"></label></div>
<p id="c_out" class="out"></p><p class="small">Typical K: 0.20 dry zinc/plain · 0.15 oiled · 0.12 moly paste · 0.10 PTFE.</p></div>{CALC_JS}"""

# ───────────────────────── PAGE BUILDERS ─────────────────────────
def build_metric():
    hub_rows = []
    for d,p,coarse in METRIC:
        name, slug = mname(d,p), mslug(d,p)
        cls_ok = [c for c in CLASSES if d<=CLASSES[c][3]]
        cells = [f'<a href="/tap-drill/{slug}/">{name}</a>' + ("" if coarse else " <small>fine</small>")]
        for c in CLASSES:
            cells.append(f'<a href="/metric-bolt-torque/{slug}-class-{c.lower()}/">{sig(m_calc(d,p,c)["dry"])}</a>' if c in cls_ok else "–")
        hub_rows.append(cells)
        for c in cls_ok:
            r = m_calc(d,p,c); ex = M_EXTRA[d]; nm = r["dry"]
            q,label = wrench_pick(nm)
            title = f"{name} Class {c} Bolt Torque: {sig(nm)} N·m ({sig(nm*0.7376)} lb·ft) | {SITE}"
            desc = (f"Tightening torque for {name} class {c} bolts: {sig(nm)} N·m dry, {sig(r['lube'])} N·m lubricated. "
                    f"Preload, stress area, tap drill, clearance hole and wrench size.")
            body = f"""<h1>{name} class {c} bolt torque</h1>
<div class="hero"><div class="tiles">{tile("Dry · K 0.20",sig(nm),"N·m",f"{sig(nm*0.7376)} lb·ft · {sig(nm*8.851)} lb·in","pri")}
{tile("Lubricated · K 0.15",sig(r['lube']),"N·m",f"{sig(r['lube']*0.7376)} lb·ft · {sig(r['lube']*8.851)} lb·in")}
{tile("Clamp force at 75% proof",sig(r['F']/1000),"kN",f"{sig(r['F']*0.2248)} lbf","wide")}</div>
<div class="fig">{bolt_svg(f"Ø{g(d)} mm",f"P {g(p)}",f"{g(ex[3])} mm")}</div></div>
<p class="lead">A {name} {"coarse" if coarse else "fine"}-thread bolt in property class {c} ({CLASSES[c][4]}) has a tensile stress area of
{sig(r['A'])} mm² and a proof strength of {r['sp']} MPa. Tightened to 75% of proof load it carries a clamp force of
about {sig(r['F']/1000)} kN.</p>
{table(["Condition","K","N·m","lb·ft","lb·in"],[
 ["Dry (plain / zinc)","0.20",sig(nm),sig(nm*0.7376),sig(nm*8.851)],
 ["Lubricated (oiled)","0.15",sig(r['lube']),sig(r['lube']*0.7376),sig(r['lube']*8.851)]])}
{ad()}
<h2>{name} specifications</h2>
{table(["Property","Value"],[
 ["Nominal diameter",f"{g(d)} mm"],["Thread pitch",f"{g(p)} mm ({'coarse' if coarse else 'fine'})"],
 ["Tensile stress area",f"{sig(r['A'])} mm²"],["Proof strength (class {})".format(c),f"{r['sp']} MPa"],
 ["Minimum tensile strength",f"{CLASSES[c][2]} MPa"],["Preload at 75% proof",f"{sig(r['F']/1000)} kN ({sig(r['F']*0.2248)} lbf)"],
 ["Tap drill",f'<a href="/tap-drill/{slug}/">{g(round(d-p,1))} mm</a>'],
 ["Clearance hole (close / medium / coarse)",f"{g(ex[0])} / {g(ex[1])} / {g(ex[2])} mm"],
 ["Hex head wrench size",f"{g(ex[3])} mm"],["Socket-head hex key",f"{g(ex[4])} mm" if ex[4] else "–"]])}
<p class="aff">🔧 Right tool for {sig(nm)} N·m: {amazon(q,"compare "+label+"es")} ·
{amazon(f"{name.replace(' ','')} class {c} bolts", f"{name} class {c} bolts")}</p>
{calc_widget(d,r['A'],r['sp'],"mm")}
<h2>How this is calculated</h2>
<p>Stress area A<sub>s</sub> = π/4 · (d − 0.9382·P)² = {sig(r['A'])} mm². Preload F = 0.75 · S<sub>p</sub> · A<sub>s</sub> =
{sig(r['F']/1000)} kN. Torque T = K · d · F = {K_DRY} × {g(d)} mm × {sig(r['F']/1000)} kN = {sig(nm)} N·m.</p>
{"<p class='warn'>Stainless fasteners gall easily and friction varies widely. Use anti-seize and verify torque by test.</p>" if c.startswith("A") else ""}
{faq([(f"What is the torque for an {name} {c} bolt?", f"About {sig(nm)} N·m ({sig(nm*0.7376)} lb·ft) dry and {sig(r['lube'])} N·m lubricated, at 75% of proof load."),
      (f"What size wrench fits an {name.split(' ')[0]} bolt?", f"A standard ISO hex head {name.split(' ')[0]} bolt takes a {g(ex[3])} mm wrench."),
      (f"What tap drill is used for {name}?", f"{g(round(d-p,1))} mm.")])}
<h2>Other classes for {name}</h2><p class="links">{" ".join(f'<a href="/metric-bolt-torque/{slug}-class-{o.lower()}/">{o}</a>' for o in cls_ok if o!=c)}</p>
<h2>Other sizes in class {c}</h2><p class="links">{" ".join(f'<a href="/metric-bolt-torque/{mslug(a,b)}-class-{c.lower()}/">{mname(a,b)}</a>' for a,b,_ in METRIC if a<=CLASSES[c][3] and (a,b)!=(d,p))}</p>"""
            page(f"metric-bolt-torque/{slug}-class-{c.lower()}", title, desc, body, [("Metric bolt torque","/metric-bolt-torque/")])
    page("metric-bolt-torque", f"Metric Bolt Torque Chart (N·m) – M1.6 to M39, Class 4.6–12.9 | {SITE}",
         "Metric bolt torque chart for coarse and fine threads, property classes 4.6, 5.8, 8.8, 10.9, 12.9 and stainless A2-70/A4-80.",
         f"<h1>Metric bolt torque chart</h1><p class='lead'>Dry torque in N·m (K = 0.20, 75% of proof load). Click any value for lubricated torque, preload, and full specs.</p>{ad()}"
         + table(["Thread"]+list(CLASSES), hub_rows, "chart"))

def build_inch():
    rows = []
    for lbl,d,n,ser,tap,_,cc,cf,wr in INCH:
        if d<.25: continue
        slug = islug(lbl); cells=[f'<a href="/tap-drill/{slug}/">{lbl}</a> <small>{ser}</small>']
        for gr in GRADES:
            r = in_calc(d,n,gr); t=r["dry"]; nm=t*1.3558
            q,label = wrench_pick(nm)
            cells.append(f'<a href="/inch-bolt-torque/{slug}-grade-{gr}/">{sig(t)}</a>')
            title = f"{lbl} Grade {gr} Bolt Torque: {sig(t)} lb·ft ({sig(nm)} N·m) | {SITE}"
            desc = f"Torque spec for {lbl} {ser} SAE grade {gr} bolts: {sig(t)} lb·ft dry, {sig(r['lube'])} lb·ft lubricated. Clamp load, tap drill and wrench size."
            body = f"""<h1>{lbl} grade {gr} bolt torque</h1>
<div class="hero"><div class="tiles">{tile("Dry · K 0.20",sig(t),"lb·ft",f"{sig(t*12)} lb·in · {sig(nm)} N·m","pri")}
{tile("Lubricated · K 0.15",sig(r['lube']),"lb·ft",f"{sig(r['lube']*12)} lb·in · {sig(r['lube']*1.3558)} N·m")}
{tile("Clamp force at 75% proof",sig(r['F']),"lbf",f"{sig(r['F']*4.448/1000)} kN","wide")}</div>
<div class="fig">{bolt_svg(f"Ø{d:g} in",f"{n} TPI",f"{wr} in")}</div></div>
<p class="lead">A {lbl} {ser} bolt in SAE J429 grade {gr} has a tensile stress area of {r['A']:.4f} in² and a proof strength of
{r['sp']:,} psi. At 75% of proof load the clamp force is about {sig(r['F'])} lbf.</p>
{table(["Condition","K","lb·ft","lb·in","N·m"],[
 ["Dry (plain / zinc)","0.20",sig(t),sig(t*12),sig(nm)],
 ["Lubricated (oiled)","0.15",sig(r['lube']),sig(r['lube']*12),sig(r['lube']*1.3558)]])}
{ad()}
<h2>{lbl} specifications</h2>
{table(["Property","Value"],[["Major diameter",f'{d:.4f} in ({d*25.4:.2f} mm)'],["Threads per inch",f"{n} ({ser})"],
 ["Tensile stress area",f"{r['A']:.4f} in²"],[f"Proof strength (grade {gr})",f"{r['sp']:,} psi"],
 ["Clamp load at 75% proof",f"{sig(r['F'])} lbf ({sig(r['F']*4.448/1000)} kN)"],
 ["Tap drill",f'<a href="/tap-drill/{slug}/">{tap}</a>'],["Clearance drill (close / free)",f"{cc} / {cf}"],
 ["Hex head wrench size",f"{wr} in"]])}
<p class="aff">🔧 Right tool for {sig(t)} lb·ft: {amazon(q,"compare "+label+"es")} · {amazon(f"{lbl} grade {gr} bolts",f"{lbl} grade {gr} bolts")}</p>
{calc_widget(d,r['A'],r['sp'],"in")}
<h2>How this is calculated</h2><p>A<sub>s</sub> = 0.7854 · (D − 0.9743/n)² = {r['A']:.4f} in². F = 0.75 · S<sub>p</sub> · A<sub>s</sub> = {sig(r['F'])} lbf.
T = K · D · F = {K_DRY} × {d:g} in × {sig(r['F'])} lbf = {sig(t*12)} lb·in = {sig(t)} lb·ft.</p>
{faq([(f"How tight should a {lbl} grade {gr} bolt be?", f"About {sig(t)} lb·ft dry or {sig(r['lube'])} lb·ft lubricated, which gives roughly {sig(r['F'])} lbf of clamp load."),
      (f"What wrench fits a {lbl} bolt?", f"A standard hex cap screw of this size takes a {wr} inch wrench."),
      (f"What is the tap drill for {lbl}?", f"A {tap} drill.")])}
<h2>Other grades</h2><p class="links">{" ".join(f'<a href="/inch-bolt-torque/{slug}-grade-{o}/">Grade {o}</a>' for o in GRADES if o!=gr)}</p>
<h2>Other sizes in grade {gr}</h2><p class="links">{" ".join(f'<a href="/inch-bolt-torque/{islug(x[0])}-grade-{gr}/">{x[0]}</a>' for x in INCH if x[1]>=.25 and x[0]!=lbl)}</p>"""
            page(f"inch-bolt-torque/{slug}-grade-{gr}", title, desc, body, [("Inch bolt torque","/inch-bolt-torque/")])
        rows.append(cells)
    page("inch-bolt-torque", f"Inch Bolt Torque Chart (lb·ft) – SAE Grade 2, 5, 8, UNC & UNF | {SITE}",
         "SAE bolt torque chart in lb·ft for UNC and UNF threads from 1/4 to 1 inch, grades 2, 5 and 8.",
         f"<h1>Inch (SAE) bolt torque chart</h1><p class='lead'>Dry torque in lb·ft (K = 0.20, 75% of proof load). Click a value for details.</p>{ad()}"
         + table(["Thread","Grade 2","Grade 5","Grade 8"], rows, "chart"))

def build_tap():
    mrows, irows = [], []
    for d,p,coarse in METRIC:
        name, slug, ex, drill = mname(d,p), mslug(d,p), M_EXTRA[d], round(d-p,1)
        pct = (d-drill)/(1.0825*p)*100
        mrows.append([f'<a href="/tap-drill/{slug}/">{name}</a>', f"{g(drill)} mm", f"{g(ex[1])} mm"])
        body = f"""<h1>{name} tap drill size</h1><div class="hero"><div class="tiles">{tile("Tap drill",g(drill),"mm",f"{drill/25.4:.4f} in · ≈{pct:.0f}% thread","pri")}
{tile("Clearance hole",g(ex[1]),"mm","medium fit, ISO 273")}</div>
<div class="fig">{bolt_svg(f"Ø{g(d)} mm",f"P {g(p)}",f"{g(ex[3])} mm")}</div></div>
<p class="lead">For an {name} {"coarse" if coarse else "fine"} thread, drill {g(drill)} mm before tapping (nominal diameter minus pitch).
For a through-hole that the bolt passes through, use a {g(ex[1])} mm clearance drill.</p>
{table(["Hole","Drill"],[["Tap drill (cutting tap)",f"{g(drill)} mm"],["Clearance – close fit",f"{g(ex[0])} mm"],
 ["Clearance – medium fit",f"{g(ex[1])} mm"],["Clearance – coarse fit",f"{g(ex[2])} mm"]])}
{ad()}<p class="aff">🔧 {amazon(f"{name.replace(' ','')} tap", f"{name} taps")} · {amazon(f"{g(drill)}mm drill bit", f"{g(drill)} mm drill bits")} · {amazon("metric tap and die set","metric tap &amp; die sets")}</p>
{faq([(f"What drill bit do I use for an {name} tap?", f"A {g(drill)} mm drill, giving about {pct:.0f}% thread engagement."),
      (f"What is the clearance hole for {name.split(' ')[0]}?", f"{g(ex[0])} mm close, {g(ex[1])} mm medium or {g(ex[2])} mm coarse fit (ISO 273).")])}
<h2>{name} torque by class</h2><p class="links">{" ".join(f'<a href="/metric-bolt-torque/{slug}-class-{c.lower()}/">Class {c}</a>' for c in CLASSES if d<=CLASSES[c][3])}</p>"""
        page(f"tap-drill/{slug}", f"{name} Tap Drill Size: {g(drill)} mm + Clearance Hole | {SITE}",
             f"Tap drill size for {name}: {g(drill)} mm. Clearance holes {g(ex[0])}/{g(ex[1])}/{g(ex[2])} mm.", body, [("Tap drill chart","/tap-drill/")])
    for lbl,d,n,ser,tap,dd,cc,cf,wr in INCH:
        slug = islug(lbl); pct = (d-dd)*n/1.299*100
        irows.append([f'<a href="/tap-drill/{slug}/">{lbl}</a> <small>{ser}</small>', f"{tap} ({dd:.4f} in)", f"{cc} / {cf}"])
        tq = f'<h2>{lbl} torque by grade</h2><p class="links">' + " ".join(f'<a href="/inch-bolt-torque/{slug}-grade-{o}/">Grade {o}</a>' for o in GRADES) + "</p>" if d>=.25 else ""
        body = f"""<h1>{lbl} tap drill size</h1><div class="hero"><div class="tiles">{tile("Tap drill",tap,"",f"{dd:.4f} in · {dd*25.4:.2f} mm · ≈{pct:.0f}% thread","pri")}
{tile("Clearance drill",cc,"",f"close fit · {cf} free fit")}</div>
<div class="fig">{bolt_svg(f"Ø{d:g} in",f"{n} TPI",f"{wr} in" if wr else "–")}</div></div>
<p class="lead">For a {lbl} {ser} thread, drill with a {tap} bit before tapping. For a bolt to pass through, use a {cc} (close fit) or {cf} (free fit) clearance drill.</p>
{table(["Hole","Drill"],[["Tap drill",f"{tap} ({dd:.4f} in)"],["Clearance – close fit",cc],["Clearance – free fit",cf]])}
{ad()}<p class="aff">🔧 {amazon(f"{lbl} tap", f"{lbl} taps")} · {amazon("tap and die set SAE","SAE tap &amp; die sets")} · {amazon("number letter fractional drill bit set","115-piece drill sets")}</p>
{faq([(f"What size drill bit for a {lbl} tap?", f"A {tap} drill ({dd:.4f} in), giving about {pct:.0f}% thread.")])}{tq}"""
        page(f"tap-drill/{slug}", f"{lbl} Tap Drill Size: {tap} Drill + Clearance Hole | {SITE}",
             f"Tap drill size for {lbl} {ser}: {tap} ({dd:.4f} in). Clearance drills {cc} / {cf}.", body, [("Tap drill chart","/tap-drill/")])
    page("tap-drill", f"Tap Drill Chart – Metric & Inch (UNC/UNF) | {SITE}", "Tap drill and clearance hole chart for metric and unified inch threads.",
         f"<h1>Tap drill chart</h1>{ad()}<h2>Metric</h2>" + table(["Thread","Tap drill","Clearance (medium)"], mrows, "chart")
         + "<h2>Inch (UNC / UNF)</h2>" + table(["Thread","Tap drill","Clearance (close / free)"], irows, "chart"))

def build_static():
    page("calculator", f"Bolt Torque Calculator (Metric & Inch) | {SITE}", "Free bolt torque calculator: T = K·d·F with adjustable nut factor and preload.",
         "<h1>Bolt torque calculator</h1><p>Enter your thread data (defaults: M10 x 1.5 class 8.8). Pick a thread from the charts to pre-fill.</p>"
         + calc_widget(10, m_area(10,1.5), 580, "mm"))
    page("", f"{SITE} – Bolt Torque Charts, Tap Drill Sizes & Calculator",
         "Fast reference for bolt tightening torque, tap drill and clearance hole sizes. Metric and inch.",
         f"""<section class="home"><h1>Bolt torque &amp; tap drill sizes, <i>instantly.</i></h1>
<p>362 fastener spec pages. Every number is calculated from the ISO, ASME and SAE formulas, with the working shown.</p>
{SRCH}<div class="chips"><a href="/metric-bolt-torque/m8x1.25-class-8.8/">M8 8.8</a><a href="/metric-bolt-torque/m10x1.5-class-10.9/">M10 10.9</a>
<a href="/metric-bolt-torque/m12x1.75-class-8.8/">M12 8.8</a><a href="/inch-bolt-torque/1-4-20-grade-5/">1/4-20 Gr 5</a><a href="/inch-bolt-torque/1-2-13-grade-8/">1/2-13 Gr 8</a>
<a href="/tap-drill/m6x1/">M6 tap drill</a><a href="/tap-drill/1-4-20/">1/4-20 tap drill</a></div></section>
<div class="cards"><a href="/metric-bolt-torque/"><em>🔩</em><b>Metric bolt torque</b><span>M1.6–M39 · class 4.6–12.9 · stainless</span></a>
<a href="/inch-bolt-torque/"><em>📏</em><b>Inch bolt torque</b><span>1/4–1″ · UNC/UNF · grade 2/5/8</span></a>
<a href="/tap-drill/"><em>🌀</em><b>Tap drill chart</b><span>Metric &amp; inch, with clearance holes</span></a>
<a href="/calculator/"><em>🧮</em><b>Torque calculator</b><span>Custom K factor and preload</span></a></div>{ad()}""")
    page("about", f"About & Method | {SITE}", "How BoltSpec values are calculated and their limits.",
         f"""<h1>About &amp; method</h1><p>{SITE} is an independent quick-reference for fastener data.</p>
<ul><li>Metric stress area: A<sub>s</sub> = π/4·(d − 0.9382P)² (ISO 898-1). Inch: A<sub>s</sub> = 0.7854·(D − 0.9743/n)² (ASME B1.1).</li>
<li>Proof strengths: ISO 898-1 property classes; ISO 3506 stainless (0.2% proof); SAE J429 grades.</li>
<li>Preload = 75% of proof load. Torque T = K·d·F, K = 0.20 dry, 0.15 lubricated.</li>
<li>Clearance holes: ISO 273. Tap drills: nominal − pitch (metric); standard chart drills (inch).</li></ul>{DISCLAIMER}
<p>Contact: {CFG['contact_email']}</p><p>Affiliate disclosure: some links go to Amazon; as an Amazon Associate we earn from qualifying purchases at no cost to you.</p>""")
    page("privacy", f"Privacy Policy | {SITE}", "Privacy policy.",
         f"""<h1>Privacy policy</h1><p>{SITE} does not require accounts and does not collect personal data directly.</p>
<p>Third-party vendors, including Google, use cookies to serve ads based on a user’s prior visits to this and other websites.
Google’s use of advertising cookies enables it and its partners to serve ads based on those visits. You can opt out of personalised
advertising at <a href="https://www.google.com/settings/ads">Google Ads Settings</a> or <a href="https://www.aboutads.info">aboutads.info</a>.</p>
<p>Links to Amazon are affiliate links; Amazon may set cookies when you follow them. Our host may keep standard server logs.</p>
<p>Contact: {CFG['contact_email']}</p>""")

CSS = """:root{--bg:#f3f4f6;--card:#fff;--ink:#0f172a;--mut:#5b6677;--line:#e2e6ec;--steel:#0e1420;--acc:#f26a1b;--acc2:#0b63ce;--tile:#0e1420;--tilefg:#fff;--soft:#f7f8fa}
@media(prefers-color-scheme:dark){:root{--bg:#0a0d12;--card:#121821;--ink:#e8edf4;--mut:#93a0b4;--line:#232c3a;--steel:#070a0f;--acc2:#6aa9ff;--tile:#1a2331;--soft:#0e141c}}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{font:16px/1.6 Inter,system-ui,-apple-system,Segoe UI,sans-serif;margin:0;color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased}
.num,td,.val,.out,input{font-variant-numeric:tabular-nums}a{color:var(--acc2);text-underline-offset:3px}
header{background:var(--steel);position:sticky;top:0;z-index:9;border-bottom:3px solid var(--acc)}
.hin{max-width:1040px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;gap:10px 22px;align-items:center}
.logo{display:flex;align-items:center;gap:9px;color:#fff;font-weight:800;font-size:20px;letter-spacing:-.02em;text-decoration:none}.logo svg{width:26px;height:26px}.logo i{color:var(--acc);font-style:normal}
nav{display:flex;gap:4px;flex-wrap:wrap}nav a{color:#c8d1de;text-decoration:none;font-size:14.5px;font-weight:500;padding:6px 11px;border-radius:7px}nav a:hover{background:#1c2636;color:#fff}
.srch{margin-left:auto;position:relative;flex:1 1 200px;max-width:300px}.srch input{width:100%;background:#1a2331;border:1px solid #2b3648;color:#fff;border-radius:8px;padding:8px 12px;font-size:14.5px;outline:0}
.srch input:focus{border-color:var(--acc)}.srch input::placeholder{color:#8795aa}
.res{position:absolute;left:0;right:0;top:calc(100% + 6px);background:var(--card);border:1px solid var(--line);border-radius:10px;box-shadow:0 12px 30px rgba(0,0,0,.25);overflow:hidden;display:none}
.res a{display:block;padding:9px 12px;color:var(--ink);text-decoration:none;font-size:14.5px;border-bottom:1px solid var(--line)}.res a:hover,.res a.on{background:var(--soft);color:var(--acc)}
main{max-width:1040px;margin:0 auto;padding:18px 20px 40px;min-height:70vh}
.bc{font-size:13px;color:var(--mut);margin:0 0 6px}.bc a{color:var(--mut)}
h1{font-size:clamp(26px,4.2vw,38px);line-height:1.15;letter-spacing:-.025em;margin:.1em 0 .5em;font-weight:800}
h2{font-size:20px;letter-spacing:-.01em;margin:2em 0 .6em;font-weight:700;display:flex;align-items:center;gap:10px}h2:before{content:"";width:6px;height:20px;background:var(--acc);border-radius:2px}
h3{font-size:16px;margin:1.2em 0 0}p{margin:.6em 0}
.hero{display:grid;grid-template-columns:1.25fr 1fr;gap:16px;margin:8px 0 18px}@media(max-width:760px){.hero{grid-template-columns:1fr}}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:12px}.tile{background:var(--tile);color:var(--tilefg);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;position:relative;overflow:hidden}
.tile:after{content:"";position:absolute;right:-18px;top:-18px;width:70px;height:70px;border:10px solid rgba(255,255,255,.05);border-radius:50%}
.tile.pri{background:linear-gradient(135deg,#f26a1b,#d94f06)}.tile.wide{grid-column:1/-1;flex-direction:row;align-items:baseline;gap:14px;flex-wrap:wrap;padding:12px 18px}
.lab{font-size:12px;text-transform:uppercase;letter-spacing:.09em;opacity:.8;font-weight:600}.val{font-size:clamp(30px,5vw,42px);font-weight:800;letter-spacing:-.03em;line-height:1.15}.val small{font-size:.48em;font-weight:700;margin-left:6px;letter-spacing:0}
.wide .val{font-size:24px}.wide .val small{font-size:.62em}@media(max-width:600px){nav{flex-wrap:nowrap;overflow-x:auto;width:100%;scrollbar-width:none}nav a{white-space:nowrap;padding:6px 9px}.srch{max-width:none;flex-basis:100%}.tile{padding:14px}}.alt{font-size:14px;opacity:.85}
.fig{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;display:flex;align-items:center;justify-content:center;color:var(--ink);
background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:22px 22px;background-position:-1px -1px}
.fig svg{width:100%;max-width:380px;height:auto}
.lead{color:var(--mut);font-size:16.5px;max-width:70ch}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line)}tr:last-child td{border-bottom:0}
th{background:var(--soft);font-size:12.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);font-weight:700}tbody tr:hover td{background:var(--soft)}
td:first-child{color:var(--mut)}td+td{font-weight:600}
.chart td,.chart th{text-align:right;white-space:nowrap}.chart td:first-child,.chart th:first-child{text-align:left;position:sticky;left:0;background:var(--card);font-weight:700;border-right:1px solid var(--line)}
.chart th:first-child{background:var(--soft)}.chart td:first-child a{color:var(--ink);text-decoration:none}.chart td a{text-decoration:none}.chart td a:hover{text-decoration:underline}
.chart tbody tr:nth-child(even) td{background:var(--soft)}.chart small{font-weight:500}
.warn{background:#fff6e5;border:1px solid #f3d7a0;color:#5c4308;border-radius:10px;padding:10px 14px;font-size:14px}@media(prefers-color-scheme:dark){.warn{background:#2a2110;border-color:#5a4516;color:#f1d9a3}}
.aff{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:10px;padding:12px 14px;margin:16px 0}.aff a{font-weight:600}
.links{display:flex;flex-wrap:wrap;gap:7px}.links a{padding:5px 11px;border:1px solid var(--line);background:var(--card);border-radius:999px;text-decoration:none;font-size:13.5px;color:var(--ink);font-weight:500}.links a:hover{border-color:var(--acc);color:var(--acc)}
.calc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:4px 18px 14px;margin-top:22px}.calc h2{margin-top:.8em}
.cg{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}.calc label{font-size:12.5px;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.calc input{display:block;width:100%;margin-top:5px;padding:9px 10px;font-size:16px;border:1px solid var(--line);border-radius:8px;background:var(--soft);color:var(--ink);font-weight:600}.calc input:focus{outline:2px solid var(--acc);border-color:transparent}
.out{font-size:19px;background:var(--soft);border-radius:10px;padding:12px 14px;margin:14px 0 6px}.out b{color:var(--acc);font-size:1.25em}.small,small{font-size:12.5px;color:var(--mut)}
.home{background:var(--steel);color:#fff;border-radius:18px;padding:clamp(24px,5vw,52px);margin:6px 0 20px;position:relative;overflow:hidden;
background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:28px 28px}
.home h1{font-size:clamp(30px,5.5vw,52px);max-width:16ch;margin-bottom:.3em}.home h1 i{color:var(--acc);font-style:normal}.home p{color:#b9c4d4;max-width:52ch;font-size:17px}
.home .srch{margin:22px 0 0;max-width:520px}.home .srch input{padding:14px 16px;font-size:17px;border-radius:12px;background:#fff;color:#0f172a;border:0}.home .srch input::placeholder{color:#6b7686}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.chips a{color:#dbe3ee;border:1px solid #2f3b4f;border-radius:999px;padding:5px 12px;font-size:13.5px;text-decoration:none}.chips a:hover{border-color:var(--acc);color:#fff}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.cards a{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;text-decoration:none;color:var(--ink);transition:.15s;display:block}
.cards a:hover{transform:translateY(-3px);border-color:var(--acc);box-shadow:0 10px 24px rgba(0,0,0,.08)}.cards b{display:block;font-size:17px;margin:10px 0 2px}.cards span{color:var(--mut);font-size:14px}.cards em{font-style:normal;font-size:26px}
footer{background:var(--steel);color:#93a0b4;font-size:13px}.fin{max-width:1040px;margin:0 auto;padding:22px 20px}footer a{color:#c8d1de}footer .warn{background:transparent;border-color:#2b3648;color:#93a0b4}
ul{padding-left:20px}li{margin:.35em 0}"""

SITE_JS = """(function(){var data=null;function load(cb){if(data)return cb();fetch('/search.json').then(function(r){return r.json()}).then(function(j){data=j;cb()})}
function norm(s){return s.toLowerCase().replace(/[^a-z0-9./#]/g,'')}
document.querySelectorAll('.srch').forEach(function(box){var inp=box.querySelector('input'),res=box.querySelector('.res'),sel=-1;
function show(){var q=norm(inp.value);if(!q){res.style.display='none';return}
var hits=data.filter(function(d){return d[2].indexOf(q)>=0}).slice(0,8);sel=-1;
res.innerHTML=hits.map(function(h){return '<a href="'+h[1]+'">'+h[0]+'</a>'}).join('')||'<a>No match – try “M10” or “1/4-20”</a>';res.style.display='block'}
inp.addEventListener('focus',function(){load(function(){})});inp.addEventListener('input',function(){load(show)});
inp.addEventListener('keydown',function(e){var a=res.querySelectorAll('a[href]');if(e.key=='ArrowDown'||e.key=='ArrowUp'){e.preventDefault();sel=(sel+(e.key=='ArrowDown'?1:-1)+a.length)%a.length;a.forEach(function(x,i){x.classList.toggle('on',i==sel)})}
else if(e.key=='Enter'&&a.length){location.href=(a[sel<0?0:sel]).href}});
document.addEventListener('click',function(e){if(!box.contains(e.target))res.style.display='none'})})})();"""

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST/"style.css").write_text(CSS); (DIST/"site.js").write_text(SITE_JS)
    (DIST/"favicon.svg").write_text(LOGO.replace("<svg ",'<svg xmlns="http://www.w3.org/2000/svg" '))
    build_static(); build_metric(); build_inch(); build_tap()
    sm = "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in PAGES)
    (DIST/"sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    norm = lambda t: "".join(ch for ch in t.lower() if ch.isalnum() or ch in "./#")
    (DIST/"search.json").write_text(json.dumps([[t,u,norm(t)] for t,u in SEARCH if u.count("/")>2], ensure_ascii=False))
    (DIST/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    (DIST/"urls.txt").write_text("\n".join(BASE+u for u in PAGES))
    (DIST/"404.html").write_text(f'<!doctype html><meta charset="utf-8"><title>Not found</title><link rel="stylesheet" href="/style.css"><main><h1>Page not found</h1><p><a href="/">Back to {SITE}</a></p></main>')
    if CFG["indexnow_key"]: (DIST/f'{CFG["indexnow_key"]}.txt').write_text(CFG["indexnow_key"])
    if CFG["adsense_client"]: (DIST/"ads.txt").write_text(f'google.com, {CFG["adsense_client"].replace("ca-","")}, DIRECT, f08c47fec0942fa0\n')
    print(f"Built {len(PAGES)} pages -> {DIST}")
if __name__ == "__main__": main()
