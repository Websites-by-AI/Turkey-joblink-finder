---
title: JobLink — ایران ⇄ ترکیه مچینگ
emoji: 🤝
sdk: gradio
sdk_version: "5.42.0"
app_file: app.py
python_version: "3.11"
license: mit
tags: [jobs, matching, persian, turkish, nlp]
short_description: CV بچسبان، ۵ آگهی واقعی ترکیه با دلیل و فاصله‌ها ببین
---

# JobLink demo space

What lives here (PLAN-FA.md §7): this Space is **not** the crawler. It is
(a) the public matching demo for job seekers, (b) optionally the embedding service.

```bash
# local
pip install -r requirements.txt && python app.py
# deploy: create a Space (docker not needed, gradio sdk), upload this folder + ../joblink
```

Layout expectation on the Space:

```
/README.md   (this file)
/app.py
/requirements.txt
/joblink/    (copy of the python package; `cp -r ../joblink .`)
/jobs.json   (a recent ingest export so the demo works with zero DB)
```

Free CPU zero is fine: 18–5k jobs JSON + BM25 is milliseconds. Only `HF_TOKEN`
(set as a Space secret) turns on multilingual embeddings, and the code falls back
silently if it is missing or rate-limited.
