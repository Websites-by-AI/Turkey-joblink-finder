"""Self-contained HTML report (no external CSS/JS/fonts: renders in a sandboxed viewer)."""

from __future__ import annotations

import html
import json
import os
import sqlite3
from datetime import datetime, timezone

ROW_SQL = """
SELECT c.cid, c.pseudonym, c.headline, c.city AS ccity, c.languages, c.skills AS cskills,
       m.title, m.company, m.city, m.remote, m.score, m.components, m.matched_skills,
       m.gaps, m.url, m.source
FROM matches m JOIN candidates c ON c.cid = m.cid
ORDER BY c.cid, m.score DESC
"""

CSS = """
:root{--bg:#0f1115;--card:#171a21;--ink:#e8eaf0;--mut:#9aa3b2;--ok:#31c48d;--warn:#f0b429;--bad:#f4536c}
*{box-sizing:border-box}
body{margin:0;padding:28px;background:var(--bg);color:var(--ink);
 font:15px/1.6 system-ui,-apple-system,"Segoe UI",Tahoma,sans-serif}
h1{font-size:22px;margin:0 0 4px} .sub{color:var(--mut);margin:0 0 22px;font-size:13px}
.card{background:var(--card);border:1px solid #232834;border-radius:14px;padding:16px 18px;margin:0 0 18px}
.cand{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;border-bottom:1px solid #232834;padding-bottom:10px;margin-bottom:12px}
.cand b{font-size:17px} .tag{background:#222a38;border-radius:999px;padding:2px 10px;font-size:12px;color:#cbd5e1}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:right;padding:9px 8px;border-bottom:1px solid #1f2430;vertical-align:top}
th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
td.l,th.l{text-align:left}
.score{font-variant-numeric:tabular-nums;font-weight:700;font-size:16px}
.s-hi{color:var(--ok)} .s-md{color:var(--warn)} .s-lo{color:var(--bad)}
.gaps{margin:6px 0 0;padding:0;list-style:none;font-size:12.5px;color:var(--mut);text-align:right}
.gaps li{margin:2px 0} .gaps b{color:var(--bad)}
a{color:#7fb3ff;text-decoration:none} a:hover{text-decoration:underline}
.pill{font-size:11px;border:1px solid #2c3444;border-radius:6px;padding:1px 6px;margin-left:4px;color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:18px}
.kpi{background:var(--card);border:1px solid #232834;border-radius:12px;padding:12px 14px}
.kpi .n{font-size:22px;font-weight:700} .kpi .k{color:var(--mut);font-size:12px}
.note{color:var(--mut);font-size:12px;margin-top:14px;text-align:right}
"""


def _load_explanations(path: str | None) -> dict:
    if not path or not os.path.exists(path):
        return {}
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}


def render(store_path: str, out_path: str, *, title: str = "JobLink — TR ⇄ IR dispatch report",
           explanations: str | None = None) -> dict:
    db = sqlite3.connect(store_path)
    db.row_factory = sqlite3.Row
    rows = list(db.execute(ROW_SQL))
    why = _load_explanations(explanations or os.path.join(os.path.dirname(store_path), "explanations.json"))
    stats = {"matches": len(rows), "candidates": len({r["cid"] for r in rows})}
    by_cand: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        by_cand.setdefault(r["cid"], []).append(r)

    body: list[str] = []
    for cid, items in by_cand.items():
        head = items[0]
        skills = ", ".join(s.get("name", "") for s in json.loads(head["cskills"] or "[]"))[:220]
        langs = " / ".join(f'{l.get("code","?")}·{l.get("level",0)}' for l in json.loads(head["languages"] or "[]"))
        body.append(f"""<section class="card"><div class="cand">
<b>{html.escape(head['pseudonym'] or cid)}</b><span class="tag">{html.escape(head['headline'] or '')}</span>
<span class="tag">{html.escape(head['ccity'] or 'IR')}</span><span class="tag">langs: {html.escape(langs)}</span>
<div style="flex:1 1 100%;color:#9aa3b2;font-size:12.5px">skills: {html.escape(skills)}</div></div>""")
        tr = []
        for r in items:
            sc = r["score"] or 0
            cls = "s-hi" if sc >= 55 else "s-md" if sc >= 35 else "s-lo"
            comp = json.loads(r["components"] or "{}")
            gaps = json.loads(r["gaps"] or "[]")
            g = "".join(f'<li><b>{html.escape(gx.get("item",""))}</b> — {html.escape(gx.get("advice",""))}</li>'
                        for gx in gaps[:3])
            note = why.get(f"{r['cid']}::{r['url']}", "")
            note_html = (f'<div style="margin-top:6px;color:#cbd5e1;font-size:12.5px;white-space:pre-wrap">'
                         f'{html.escape(note)}</div>') if note else ""
            tr.append(f"""<tr>
<td class="l"><a href="{html.escape(r['url'])}" target="_blank" rel="noopener">{html.escape(r['title'] or '')}</a><br>
<span class="pill">{html.escape(r['source'])}</span><span class="pill">{html.escape(r['company'] or '-')}</span>
<span class="pill">{html.escape(r['city'] or '-')}</span><span class="pill">{'remote' if r['remote'] else 'onsite'}</span>{note_html}</td>
<td class="score {cls}">{sc:.0f}</td>
<td style="color:#9aa3b2;font-size:12px">skill {comp.get('skill',0):.2f}<br>sem {comp.get('semantic',0):.2f}<br>
lang {comp.get('language',0):.2f}<br>loc {comp.get('location',0):.2f}</td>
<td style="text-align:right"><ul class="gaps">{g or '<li>—</li>'}</ul></td></tr>""")
        body.append("<table><tr><th class='l'>آگهی / Job</th><th>امتیاز</th><th>اجزا</th><th>فاصله‌ها</th></tr>"
                    + "".join(tr) + "</table></section>")

    doc = f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>
<style>{CSS}</style></head><body>
<h1>{html.escape(title)}</h1>
<p class="sub">تولید شده در {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} ·
موتور مچینگ hybrid (BM25 + skill lexicon fa/tr/en) · داده‌های کارجو: نمونه مصنوعی با رضایت ساختگی</p>
<div class="grid">
<div class="kpi"><div class="n">{stats['candidates']}</div><div class="k">کارجو</div></div>
<div class="kpi"><div class="n">{stats['matches']}</div><div class="k">مچ ذخیره‌شده</div></div>
<div class="kpi"><div class="n">{len({r['url'] for r in rows})}</div><div class="k">آگهی منحصربه‌فرد</div></div>
</div>
{''.join(body)}
<p class="note">این خروجی صرفاً برای دمو است. هیچ داده‌ی شخصی واقعی از سایت‌ها برداشته نشده؛
سمت کارجو باید opt-in باشد (بخش ۴ نقشه را بخوانید).</p>
</body></html>"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return stats
