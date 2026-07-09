const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

const DETECTED_BY_RE = /^[a-z0-9_]{1,32}$/;
const VERSION_RE = /^\d{1,3}(\.\d{1,3}){1,3}$/;
const FQDN_RE = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/;
const TLD_ALPHA_RE = /\.[a-z]{2,}$/;
const IPV4_RE = /^\d{1,3}(\.\d{1,3}){3}$/;
const hits = new Map();
let knownCache = { expires: 0, set: new Set() };

function json(status, obj) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...CORS },
  });
}

function normalizeDomain(input) {
  if (typeof input !== 'string') return null;
  let d = input.trim().toLowerCase();
  if (d.endsWith('.')) d = d.slice(0, -1);
  return d;
}

function validateDomain(d) {
  if (!d) return false;
  if (d.length < 5 || d.length > 253) return false;
  if (d === 'localhost') return false;
  if (d.endsWith('.local') || d.endsWith('.localhost')) return false;
  if (d.includes(':') || d.includes('..') || !d.includes('.')) return false;
  if (IPV4_RE.test(d)) return false;
  if (!TLD_ALPHA_RE.test(d)) return false;
  return FQDN_RE.test(d);
}

function clientIp(request) {
  return request.headers.get('CF-Connecting-IP') || request.headers.get('X-Real-IP') || 'unknown';
}

function rateLimited(ip, env) {
  const max = parseInt(env.RL_MAX || '10', 10);
  const win = parseInt(env.RL_WINDOW_MS || `${60 * 60 * 1000}`, 10);
  const now = Date.now();
  const arr = (hits.get(ip) || []).filter((t) => now - t < win);
  if (arr.length >= max) { hits.set(ip, arr); return true; }
  arr.push(now);
  hits.set(ip, arr);
  return false;
}

async function knownDomains(env) {
  const now = Date.now();
  if (knownCache.expires > now && knownCache.set.size > 0) return knownCache.set;
  const url = env.SITES_JSON_URL || 'https://utiq-tracker.online/api/v1/sites.json';
  const res = await fetch(url, { headers: { Accept: 'application/json' }, cf: { cacheTtl: 300, cacheEverything: true } });
  if (!res.ok) return knownCache.set;
  const data = await res.json();
  const s = new Set();
  for (const site of data.sites || []) {
    if (site && typeof site.domain === 'string') s.add(site.domain.toLowerCase());
  }
  knownCache = { expires: now + 5 * 60 * 1000, set: s };
  return s;
}

async function notify(env, entry) {
  if (!env.NOTIFY_WEBHOOK) return;
  const kind = (env.NOTIFY_KIND || 'discord').toLowerCase();
  const line = `Domaine: ${entry.domain} · count=${entry.count} · détecté par ${entry.detected_by} (ext ${entry.extension_version})`;
  let payload;
  if (kind === 'telegram') {
    payload = { text: `🚨 Utiq Tracker — signalement confirmé\n${line}` };
  } else {
    const ping = env.NOTIFY_MENTION ? `<@${env.NOTIFY_MENTION}> ` : '';
    payload = { content: `${ping}🚨 **Utiq Tracker** — signalement confirmé\n${line}` };
    if (env.NOTIFY_MENTION) payload.allowed_mentions = { users: [env.NOTIFY_MENTION] };
  }
  await fetch(env.NOTIFY_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

async function handleReport(request, env, ctx) {
  const contentType = (request.headers.get('content-type') || '').split(';')[0].trim().toLowerCase();
  if (contentType !== 'application/json') return json(415, { status: 'invalid', error: 'content-type' });
  const maxBody = parseInt(env.MAX_BODY || '1024', 10);
  const raw = await request.text();
  if (new TextEncoder().encode(raw).length > maxBody) return json(413, { status: 'invalid', error: 'body too large' });
  let data;
  try { data = JSON.parse(raw); } catch { return json(400, { status: 'invalid', error: 'bad json' }); }
  if (typeof data !== 'object' || data === null || Array.isArray(data)) return json(400, { status: 'invalid', error: 'bad payload' });

  const domain = normalizeDomain(data.domain);
  if (!validateDomain(domain)) return json(422, { status: 'invalid' });

  let detectedBy = typeof data.detected_by === 'string' ? data.detected_by.toLowerCase() : '';
  if (!DETECTED_BY_RE.test(detectedBy)) detectedBy = 'unknown';
  let version = typeof data.extension_version === 'string' ? data.extension_version : '';
  if (!VERSION_RE.test(version)) version = 'unknown';

  const known = await knownDomains(env);
  if (known.has(domain)) return json(200, { status: 'known' });

  const now = new Date().toISOString();
  const existing = await env.REPORTS_DB.prepare('SELECT * FROM reports WHERE domain = ?').bind(domain).first();
  const threshold = parseInt(env.NOTIFY_THRESHOLD || '2', 10);
  let status = 'ok';
  let confirmed = null;

  if (existing) {
    const count = Number(existing.count || 1) + 1;
    const nextDetected = detectedBy !== 'unknown' ? detectedBy : existing.detected_by;
    const nextVersion = version !== 'unknown' ? version : existing.extension_version;
    const shouldNotify = count >= threshold && !Number(existing.notified || 0);
    await env.REPORTS_DB.prepare('UPDATE reports SET count=?, last_seen=?, detected_by=?, extension_version=?, notified=? WHERE domain=?')
      .bind(count, now, nextDetected, nextVersion, shouldNotify ? 1 : Number(existing.notified || 0), domain).run();
    status = 'pending';
    if (shouldNotify) confirmed = { domain, count, detected_by: nextDetected, extension_version: nextVersion };
  } else {
    await env.REPORTS_DB.prepare('INSERT INTO reports (domain, detected_by, extension_version, first_seen, last_seen, count, status, notified) VALUES (?, ?, ?, ?, ?, 1, ?, 0)')
      .bind(domain, detectedBy, version, now, now, 'pending').run();
  }

  if (confirmed) ctx.waitUntil(notify(env, confirmed));
  return json(200, { status });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/healthz') return json(200, { status: 'ok' });
    if (url.pathname !== '/api/v1/report') return json(404, { status: 'invalid', error: 'not found' });
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    if (request.method !== 'POST') return new Response(JSON.stringify({ status: 'invalid', error: 'method not allowed' }), { status: 405, headers: { Allow: 'POST, OPTIONS', ...CORS } });
    if (rateLimited(clientIp(request), env)) return json(429, { status: 'invalid', error: 'rate limited' });
    return handleReport(request, env, ctx).catch(() => json(500, { status: 'invalid', error: 'server error' }));
  },
};
