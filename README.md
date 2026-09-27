# JobLink — TR job offers ⇄ IR job seekers (Uber-style dispatch)

Two pieces in one repo:

1. **`PLAN-FA.md`** — the strategy/architecture/scraping plan **in Persian** (Snapp/Uber-style
   marketplace model, the 10×10 site matrix with *measured* HTTP results, the anti-bot tier
   ladder, hosting on Cloudflare + Hugging Face, the blue-collar specifics, and the legal line
   we do not cross). Decisions recorded there: **vertical = blue collar + migration**,
   **audience = Iran-resident seekers**, **hosts = CF Workers/D1/Browser Run + HF Spaces**.
2. **`joblink/`** — a working Python core that ingests Turkish job boards, normalises
   Farsi/Turkish/English text, matches opt-in Iranian candidates, and writes an HTML dispatch
   report. Plus `worker/` (Cloudflare) and `spaces/` (Hugging Face) deploy shells.

## Quickstart

```bash
cd joblink
python3 -m pip install -r requirements.txt
cp .env.example .env              # optional: Cloudflare / proxy / HF keys
python3 -m joblink.cli sites      # registry + feasibility of every source
python3 -m joblink.cli check --source eleman_net --parse --no-cache
python3 -m joblink.cli ingest --source eleman_net --source cvyolla
python3 -m joblink.cli seed --file examples/candidates.json
python3 -m joblink.cli match --top 6
python3 -m joblink.cli report --out data/report.html
python3 -m joblink.cli ai-check   # what the HF router accepts/rejects for your token
python3 -m pytest -q              # 39 tests
```

`python -m joblink.cli demo` runs ingest → seed → match → report in one shot.

## What was actually verified (2026-09-13, EU datacenter IP, no browser)

| probe | result |
|---|---|
| `isinolsun.com/` | 200; `/is-ilani/*` details reset — **so parse `__NEXT_DATA__` instead**: 36 full ad objects incl. `salaryValue`, geo and employer-verification flag |
| `careerjet.com.tr/*` | identical 10,953-byte page with a reCAPTCHA `data-sitekey` on every path — dead end, do not solve captchas |
| `eleman.net/is-ilanlari/{istanbul,ankara,izmir,bursa,kocaeli,antalya,uretim,guvenlik,temizlik,imalat}` | HTTP 200, static, **JobPosting JSON-LD** on detail pages → 45 live jobs ingested (max_details budget per run) |
| `cvyolla.com/sitemaps/ilanlar.xml` | 271 published ad URLs → 6 live jobs (employer + city parsed) |
| `cvyolla.com/sitemaps/ilanlar.xml` | HTTP 200, **271 ad URLs** published by the site → 6 live jobs ingested (company + city parsed) |
| `secretcv.com` | 200 but cards are JS-hydrated; robots disallows `?p=`/`?k=` search |
| `kariyer.net` | 403 on every path — needs a browser tier |
| `yenibiris.com` | 403, `cf-mitigated: challenge` |
| `tr.indeed.com`, `jooble.org` | 403 |
| `linkedin.com/jobs-guest/...` | 200 + 30 cards, **but** `robots.txt` disallows it → our gate blocked it on purpose |
| `*.ir` boards (jobinja, jobvision, divar, estekhdam…) | TCP timeout from foreign DC IPs; reachable via a rendering proxy |

## AI layer (measured, not assumed)

`python -m joblink.cli ai-check` probes the account and prints an actionable verdict. Current facts we
verified against the live API: `api-inference.huggingface.co` is gone (no HTTP response) so the code
uses `router.huggingface.co`; a fine-grained token without the **Inference Providers** scope
authenticates (`/api/whoami-v2` → 200) but returns `403 ... does not have sufficient permissions to
call Inference Providers` for both embeddings and chat; free accounts get **$0.10/month** of provider
credit (PRO $9 = $2). `intfloat/multilingual-e5-large` is served (hf-inference + deepinfra) while
`...-e5-base` has **no** provider — do not "downgrade" to it. `examples/hf_probe.py` measures whether
embedding churn is worth those tokens before you turn it on.

LLM output is used for *explanations and CV tailoring only*, never for ranking (that stays auditable),
and `llm.redact()` strips IR/TR phone numbers, e-mails and national ids before a prompt is built —
asserted by `test_pii_never_leaves_the_process`.

## Design rules baked into the code

* **robots gate, fail-closed** — `joblink/robots.py`; a blocked source stays blocked (LinkedIn proved it).
* **tier ladder** `direct → flaresolverr → browser(CF Browser Run) → proxy → reader` — `joblink/httpfetch.py`.
* **sitemap-first discovery**, because a published `<urlset>` is a contract the site offers you.
* **fraud/quality triage before matching** (`quality.py`): pay-to-apply ads and phone-only listings
  are rejected outright; missing/below-minimum salary is flagged. On the live sample, 42 of 51 ads
  stated no salary — salary transparency is a product feature, not a nicety.
* **refusal over guessing**: `MIN_SEND_SCORE` + occupation-family gate means a welder never sees a
  cleaning ad, and a CNC operator with no matching supply gets an empty list.
* **per-source budget + throttle + jitter + circuit breaker + disk cache** — no runaway crawler.
* **no PII harvesting**: the candidate side exists only through `intake.candidate_from_cv(..., consent_token=)`.
  Storing a person's CV without a consent token raises `ConsentError` and is rejected by the DB layer.
* **currency/PII hygiene**: contacts stored only as sha256; `purge_consent_revoked()` implements erasure.

## Layout

```
joblink/
  config.py      10 TR + 10 IR sources, tiers, budgets, measured notes
  httpfetch.py   tier ladder, robots gate, cache, throttle, breaker
  adapters/      jsonld_board (works on 4+ TR sites), kariyer, iskur, linkedin_guest, iran_board
  normalize.py   fa/tr/en folding, skill lexicon, salary parser (TL / TOMAN / RIAL / USD), city, seniority
  matcher.py     BM25 + skills + gates + optional HF embeddings -> score + explainable gaps
  intake.py      opt-in CV parsing (the legal replacement for "scraping seekers")
  store.py       SQLite DDL (D1-compatible), runs log, consent purge
  report.py      self-contained RTL HTML report
worker/          Cloudflare Worker: cron -> /ingest -> D1 (wrangler.toml included)
bot/feed/monitor: telegram consent intake (rehearsable offline), employer feed (TL/USD/Toman +
                 salary-transparency filter), source-health alerts
spaces/          Hugging Face Space: Gradio matching demo
```
