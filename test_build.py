#!/usr/bin/env python3
"""Sanity tests: formulas vs. published reference values + link integrity. Run: python test_build.py"""
import re, build
from pathlib import Path
def close(a,b,tol=0.01): assert abs(a-b)/b<tol, (a,b)
# ISO 898-1 nominal stress areas (mm²)
for d,p,ref in [(6,1,20.1),(8,1.25,36.6),(10,1.5,58.0),(12,1.75,84.3),(16,2,157),(20,2.5,245),(24,3,353)]: close(build.m_area(d,p),ref)
# ASME B1.1 stress areas (in²)
for d,n,ref in [(.25,20,.0318),(.375,16,.0775),(.5,13,.1419),(.75,10,.334),(1,8,.606)]: close(build.in_area(d,n),ref)
close(build.m_calc(10,1.5,"8.8")["dry"],50.5,.02)      # ~50 N·m in common charts
close(build.in_calc(.5,13,"5")["dry"],75.4,.02)        # ~75 lb·ft in common charts
build.main()
dist=Path(build.DIST); pages=list(dist.rglob("index.html")); assert len(pages)>300, len(pages)
bad=set()
for f in pages:
    for href in re.findall(r'href="(/[^"]*)"', f.read_text()):
        t=dist/href.strip("/")
        if not (t.is_file() or (t/"index.html").is_file()): bad.add(href)
assert not bad, sorted(bad)[:10]
assert len(set(build.PAGES))==len(build.PAGES)
print(f"OK: {len(pages)} pages, all internal links resolve")
