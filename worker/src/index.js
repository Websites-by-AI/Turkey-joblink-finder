// JobLink edge worker — cron ingest + API over D1.
//
// Role split (see PLAN-FA.md §7):
//   * THIS worker  : schedule, cheap static fetches, JSON-LD extraction, D1 writes, read API.
//   * the python pkg : complex sources (Cloudflare challenges, .ir egress, embeddings, matching tuning).
//
// Deploy (needs your Cloudflare account):
//   cd worker && npm i -g wrangler && wrangler create d1 --name joblink
//   wrangler d1 execute joblink --file=./schema.sql --remote
//   wrangler secret put PYTHON_HOOK_TOKEN        # optional, protects /hook
//   wrangler deploy
//
// NOTE: not executed here (no CF account in this sandbox). It is a starting point, verify with
// `wrangler dev` + `curl localhost:8787/cron` before trusting it.

const SOURCES = [
  {
    key: "eleman_net", name: "Eleman.net", country: "TR",
    list: "https://www.eleman.net/is-ilanlari",
    detail: /https:\/\/www\.eleman\.net\/is-ilani\/[^\s"']+/g,
    maxDetails: 14, ttlSeconds: 6 * 3600,
  },
  {
    key: "cvyolla", name: "CV Yolla", country: "TR",
    list: "https://www.cvyolla.com/sitemaps/ilanlar.xml",
    detail: /https:\/\/www\.cvyolla\.com\/\d+-[^\s"<>]*-is-ilani/g,
    maxDetails: 14, ttlSeconds: 6 * 3600,
  },
];

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/126.0.0.0 Safari/537.36";

// ---------------------------------------------------------------- helpers --
const sha1 = async (s) => {
  const b = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("").slice(0, 20);
};

const stripTags = (s) =>
  s
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();

// Minimal schema.org JobPosting reader. Deliberately no CSS selectors: markup changes, JSON-LD doesn't.
function findJobPostings(html) {
  const out = [];
  for (const m of html.matchAll(/<script[^>]*application\/ld\+json[^>]*>([\s\S]*?)<\/script>/gi)) {
    let data;
    try {
      data = JSON.parse(m[1].trim());
    } catch {
      continue;
    }
    const stack = [data];
    while (stack.length) {
      const cur = stack.pop();
      if (Array.isArray(cur)) stack.push(...cur);
      else if (cur && typeof cur === "object") {
        if (cur["@graph"]) stack.push(cur["@graph"]);
        if (String(cur["@type"] || "").toLowerCase() === "jobposting") out.push(cur);
      }
    }
  }
  return out;
}

const lexicon = {
  python: /python|پایتون/i,
  javascript: /javascript|typescript|جاوا\s*اسکریپت/i,
  react: /react|next\.?js|ریاکت/i,
  nodejs: /node(\.js)?|express/i,
  sql: /\bsql\b|mysql|postgres|مای\s*اسکیو/i,
  excel: /excel|اکسل/i,
  docker: /docker/i,
  kubernetes: /kubernetes|k8s/i,
  aws: /\baws\b|azure|gcp/i,
  accounting: /muhasebe|حسابداری|accounting/i,
  sales: /satış|sales|فروش|بازاریابی/i,
  security_guard: /güvenlik görevlisi|نگهبان/i,
  warehouse: /depo|warehouse|انبار/i,
  customer_service: /müşteri|پشتیبان|call center|çağrı/i,
  cnc: /\bcnc\b|تراش|cnc/i,
  welding: /kaynak|برقکاری|welding/i,
  forklift: /forklift|لیفتراک/i,
  teaching: /öğretmen|مدرس|teacher/i,
  translation: /tercüme|ترجمه|translation/i,
};

const extractSkills = (text) =>
  Object.entries(lexicon)
    .filter(([, re]) => re.test(text))
    .map(([k]) => k)
    .slice(0, 25);

const parseSalary = (text) => {
  const m = String(text).match(/(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})\s*(?:-\s*(\d{1,3}(?:[.\s]\d{3})+|\d{4,9})\s*)?tl\b/i);
  if (!m) return {};
  const num = (x) => (x ? Number(x.replace(/[.\s]/g, "")) : null);
  const lo = num(m[1]);
  const hi = num(m[2]);
  if (!lo || lo < 5000 || lo > 1_500_000) return {};   // implausible monthly gross -> unknown
  return { salary_min: lo, salary_max: hi && hi !== lo ? hi : null, currency: "TRY" };
};

const detectRemote = (t) => (/uzaktan|remote|дистан|دورکاری/i.test(t) ? 1 : /ofis|onsite|yerinde/i.test(t) ? 0 : null);
const detectCity = (t) => {
  const m = String(t).match(
    /(istanbul|ankara|izmir|bursa|antalya|adana|kocaeli|konya|mersin|gaziantap|denizli|eskisehir|samsun)/i
  );
  return m ? m[1][0].toUpperCase() + m[1].slice(1).toLowerCase() : null;
};

async function getHtml(url, env, force = false) {
  const key = "html:" + url;
  if (!force) {
    const hit = await env.CACHE.get(key, "json");
    if (hit) return hit;
  }
  const res = await fetch(url, {
    headers: {
      "user-agent": UA,
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "accept-language": "tr-TR,tr;q=0.9,en;q=0.6",
      "upgrade-insecure-requests": "1",
    },
    cf: { cacheTtl: 300, cacheKey: url }, // CF edge cache, cheap politeness
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  const text = await res.text();
  const box = { url, status: res.status, text, ts: Date.now() };
  await env.CACHE.put(key, JSON.stringify(box), { expirationTtl: 6 * 3600 });
  return box;
}

// Use Cloudflare Browser Run for JS-heavy / challenge-protected boards, straight from the worker.
// Docs: Browser Rendering bindings -> `env.BROWSER.newPage()`. Requires `browser_rendering = true` in wrangler.toml.
async function getHtmlViaBrowser(url, env) {
  if (!env.BROWSER) return null;
  try {
    const page = await env.BROWSER.newPage();
    await page.goto(url, { waitUntil: "networkidle0", timeout: 25000 });
    const text = await page.content();
    await page.close();
    return { url, status: 200, text, ts: Date.now() };
  } catch {
    return null;
  }
}

async function ingestSource(src, env, force = false) {
  let box;
  try {
    box = await getHtml(src.list, env, force);
  } catch (e) {
    box = await getHtmlViaBrowser(src.list, env);
    if (!box) return { source: src.key, error: String(e.message || e) };
  }
  const urls = [...new Set(box.text.match(src.detail) || [])].slice(0, src.maxDetails);
  const rows = [];
  for (const u of urls) {
    let d;
    try {
      d = await getHtml(u, env, force);
    } catch {
      d = await getHtmlViaBrowser(u, env);
    }
    if (!d) continue;
    const [jp] = findJobPostings(d.text);
    const body = stripTags(d.text);
    const title = jp?.title || body.split(/[-–]/)[0]?.trim().slice(0, 120) || u.split("/").pop();
    const blob = `${title} ${jp?.description || ""} ${body.slice(0, 4000)}`;
    const sal = parseSalary(jp?.baseSalary ? JSON.stringify(jp.baseSalary) + " " + blob : blob);
    rows.push({
      uid: await sha1(src.key + "|" + u),
      source: src.key,
      country: src.country,
      title: String(title).slice(0, 200),
      company: jp?.hiringOrganization
        ? typeof jp.hiringOrganization === "string"
          ? jp.hiringOrganization
          : (Array.isArray(jp.hiringOrganization) ? jp.hiringOrganization[0] : jp.hiringOrganization).name ?? null
        : null,
      city: detectCity(blob),
      url: u,
      description: String(jp?.description ? stripTags(jp.description) : body.slice(0, 4000)).slice(0, 6000),
      skills: extractSkills(blob),
      posted_at: jp?.datePosted ? String(jp.datePosted).slice(0, 10) : null,
      remote: detectRemote(blob),
      salary_min: sal.salary_min ?? null,
      salary_max: sal.salary_max ?? null,
      currency: sal.currency ?? null,
    });
    await scheduler.wait(1500); // politeness: ~1.5s between detail pages
  }
  if (rows.length) await writeJobs(env, rows);
  return { source: src.key, jobs: rows.length, discovered: urls.length };
}

async function writeJobs(env, rows) {
  const now = new Date().toISOString();
  for (const r of rows) {
    await env.DB.prepare(
      `INSERT INTO jobs (uid,source,country,title,company,city,url,description,skills,posted_at,
                         remote,salary_min,salary_max,currency,scraped_at,last_seen_at,status,search_text)
       VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?15,'open',?16)
       ON CONFLICT(uid) DO UPDATE SET title=excluded.title, description=excluded.description,
         salary_min=excluded.salary_min, salary_max=excluded.salary_max, skills=excluded.skills,
         last_seen_at=excluded.last_seen_at, status='open'`
    )
      .bind(
        r.uid, r.source, r.country, r.title, r.company, r.city, r.url, r.description,
        JSON.stringify(r.skills), r.posted_at, r.remote, r.salary_min, r.salary_max, r.currency,
        now, `${r.title} ${r.description}`.slice(0, 8000)
      )
      .run();
  }
  await env.DB.prepare(`INSERT INTO runs (ts,source,kind,items) VALUES (?1,'worker','jobs',?2)`)
    .bind(now, rows.length)
    .run();
}

// ------------------------------------------------------------------- router --
export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      Promise.all(SOURCES.map((s) => ingestSource(s, env).then((r) => console.log(JSON.stringify(r)))))
    );
  },

  async fetch(req, env) {
    const url = new URL(req.url);
    const json = (o, status = 200) =>
      new Response(JSON.stringify(o, null, 2), {
        status,
        headers: { "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*" },
      });

    if (url.pathname === "/health") return json({ ok: true, ts: new Date().toISOString() });

    if (url.pathname === "/cron") {
      const out = [];
      for (const s of SOURCES) out.push(await ingestSource(s, env, url.searchParams.get("force") === "1"));
      return json({ ran: out });
    }

    if (url.pathname === "/jobs") {
      const q = url.searchParams.get("q") || "";
      const limit = Math.min(100, Number(url.searchParams.get("limit") || 30));
      const where = q
        ? `WHERE status='open' AND (search_text LIKE ?1 OR title LIKE ?1 OR skills LIKE ?1)`
        : `WHERE status='open'`;
      const stmt = env.DB.prepare(
        `SELECT uid,source,title,company,city,remote,salary_min,salary_max,currency,url,skills,posted_at
         FROM jobs ${where} ORDER BY last_seen_at DESC LIMIT ${limit}`
      );
      const { results } = await (q ? stmt.bind(`%${q}%`) : stmt).all();
      return json({ count: results.length, jobs: results });
    }

    if (url.pathname === "/stats") {
      const jobs = await env.DB.prepare(`SELECT source, COUNT(*) n FROM jobs WHERE status='open' GROUP BY source`).all();
      const cand = await env.DB.prepare(`SELECT COUNT(*) n FROM candidates`).first();
      return json({ jobs: jobs.results, candidates: cand?.meta?.count ?? cand?.n ?? null });
    }

    // /hook lets the python crawler (Fly/HF/your VPS) push parsed jobs into the same D1.
    if (url.pathname === "/hook") {
      const token = req.headers.get("x-hook-token");
      if (env.HOOK_TOKEN && token !== env.HOOK_TOKEN) return json({ error: "unauthorized" }, 401);
      const body = await req.json();
      const rows = Array.isArray(body) ? body : body.jobs || [];
      await writeJobs(
        env,
        rows.map((r) => ({
          uid: r.uid, source: r.source, country: r.country || "TR", title: r.title,
          company: r.company ?? null, city: r.city ?? null, url: r.url,
          description: (r.description || "").slice(0, 6000), skills: r.skills || [],
          posted_at: r.posted_at ?? null, remote: r.remote == null ? null : r.remote ? 1 : 0,
          salary_min: r.salary_min ?? null, salary_max: r.salary_max ?? null, currency: r.currency ?? null,
        }))
      );
      return json({ accepted: rows.length });
    }

    return json({ error: "not found", routes: ["/health", "/cron", "/jobs", "/stats", "/hook"] }, 404);
  },
};
