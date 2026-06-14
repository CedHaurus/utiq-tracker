// Endpoint de signalement Utiq Tracker — POST /api/v1/report
// Node natif, zéro dépendance. Tourne en conteneur durci (read-only, cap_drop ALL).
// Reçoit les signalements de l'extension, déduplique, persiste hors racine web.

import http from 'node:http';
import { promises as fs } from 'node:fs';
import {
  withLock, readJsonArray, atomicWrite, paths,
  normalizeDomain, validateDomain,
} from './store.mjs';

const PORT = parseInt(process.env.PORT || '8090', 10);
const DATA_DIR = process.env.REPORTS_DIR || '/data';
const SITES_PATH = process.env.SITES_PATH || '/app/public/api/v1/sites.json';
const MAX_BODY = parseInt(process.env.MAX_BODY || '1024', 10);          // 1 Kio
const RL_MAX = parseInt(process.env.RL_MAX || '10', 10);               // req/IP/fenêtre
const RL_WINDOW_MS = parseInt(process.env.RL_WINDOW_MS || `${60 * 60 * 1000}`, 10);
const NOTIFY_WEBHOOK = process.env.NOTIFY_WEBHOOK || '';
const NOTIFY_KIND = (process.env.NOTIFY_KIND || 'discord').toLowerCase();
const NOTIFY_THRESHOLD = parseInt(process.env.NOTIFY_THRESHOLD || '2', 10);
const NOTIFY_MENTION = process.env.NOTIFY_MENTION || ''; // user ID Discord à ping (optionnel)

const DETECTED_BY_RE = /^[a-z0-9_]{1,32}$/;
const VERSION_RE = /^\d{1,3}(\.\d{1,3}){1,3}$/;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

function send(res, code, obj) {
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    ...CORS,
  });
  res.end(JSON.stringify(obj));
}

// --- Cache des domaines déjà connus (sites.json), rafraîchi sur mtime ---
let knownSet = new Set();
let knownMtime = -1;
async function refreshKnown() {
  try {
    const st = await fs.stat(SITES_PATH);
    if (st.mtimeMs === knownMtime) return;
    const data = JSON.parse(await fs.readFile(SITES_PATH, 'utf8'));
    const s = new Set();
    for (const site of data.sites || []) {
      if (site && typeof site.domain === 'string') s.add(site.domain.toLowerCase());
    }
    knownSet = s;
    knownMtime = st.mtimeMs;
    console.log(`[known] ${s.size} domaines connus chargés`);
  } catch (e) {
    console.error('[known] échec rafraîchissement:', e.message); // garde l'ancien set
  }
}

// --- Rate limiting en mémoire (fenêtre glissante), l'IP n'est jamais persistée ---
const hits = new Map();
function rateLimited(ip) {
  const now = Date.now();
  const arr = (hits.get(ip) || []).filter((t) => now - t < RL_WINDOW_MS);
  if (arr.length >= RL_MAX) { hits.set(ip, arr); return true; }
  arr.push(now);
  hits.set(ip, arr);
  return false;
}
setInterval(() => {
  const now = Date.now();
  for (const [ip, arr] of hits) {
    const keep = arr.filter((t) => now - t < RL_WINDOW_MS);
    if (keep.length) hits.set(ip, keep); else hits.delete(ip);
  }
}, 10 * 60 * 1000).unref();

function clientIp(req) {
  const xri = req.headers['x-real-ip'];
  if (typeof xri === 'string' && xri.length > 0 && xri.length < 64) return xri.trim();
  const xff = req.headers['x-forwarded-for'];
  if (typeof xff === 'string' && xff.length > 0) return xff.split(',')[0].trim();
  return req.socket.remoteAddress || 'unknown';
}

// --- Notification (générique webhook), déclenchée une seule fois par domaine ---
async function notify(entry) {
  if (!NOTIFY_WEBHOOK) {
    console.log(`[notify] (webhook non configuré) ${entry.domain} a atteint count=${entry.count}`);
    return;
  }
  try {
    const line = `Domaine: ${entry.domain} · count=${entry.count} · détecté par ${entry.detected_by} (ext ${entry.extension_version})`;
    let payload;
    if (NOTIFY_KIND === 'telegram') {
      payload = { text: `🚨 Utiq Tracker — signalement confirmé\n${line}` };
    } else { // discord / générique
      const ping = NOTIFY_MENTION ? `<@${NOTIFY_MENTION}> ` : '';
      payload = { content: `${ping}🚨 **Utiq Tracker** — signalement confirmé\n${line}` };
      if (NOTIFY_MENTION) payload.allowed_mentions = { users: [NOTIFY_MENTION] };
    }
    const r = await fetch(NOTIFY_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000),
    });
    if (!r.ok) console.error(`[notify] webhook HTTP ${r.status} pour ${entry.domain}`);
    else console.log(`[notify] envoyé pour ${entry.domain} (count=${entry.count})`);
  } catch (e) {
    console.error('[notify] échec:', e.message);
  }
}

async function handleReport(req, res) {
  // Lecture du corps avec plafond strict.
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) return send(res, 413, { status: 'invalid', error: 'body too large' });
    chunks.push(chunk);
  }

  let data;
  try { data = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { return send(res, 400, { status: 'invalid', error: 'bad json' }); }
  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    return send(res, 400, { status: 'invalid', error: 'bad payload' });
  }

  const domain = normalizeDomain(data.domain);
  if (!validateDomain(domain)) return send(res, 422, { status: 'invalid' });

  let detectedBy = typeof data.detected_by === 'string' ? data.detected_by.toLowerCase() : '';
  if (!DETECTED_BY_RE.test(detectedBy)) detectedBy = 'unknown';
  let version = typeof data.extension_version === 'string' ? data.extension_version : '';
  if (!VERSION_RE.test(version)) version = 'unknown';

  await refreshKnown();
  if (knownSet.has(domain)) return send(res, 200, { status: 'known' });

  const result = await withLock(DATA_DIR, async () => {
    const { pending } = paths(DATA_DIR);
    const list = await readJsonArray(pending);
    const now = new Date().toISOString();
    let entry = list.find((e) => e.domain === domain);
    let status;
    let confirmed = null;
    if (entry) {
      entry.count = (entry.count || 1) + 1;
      entry.last_seen = now;
      if (detectedBy !== 'unknown') entry.detected_by = detectedBy;
      if (version !== 'unknown') entry.extension_version = version;
      status = 'pending';
      if (entry.count >= NOTIFY_THRESHOLD && !entry.notified) {
        entry.notified = true;
        confirmed = { ...entry };
      }
    } else {
      entry = {
        domain, detected_by: detectedBy, extension_version: version,
        first_seen: now, last_seen: now, count: 1, status: 'pending', notified: false,
      };
      list.push(entry);
      status = 'ok';
    }
    await atomicWrite(pending, list);
    return { status, confirmed };
  });

  if (result.confirmed) notify(result.confirmed); // fire-and-forget
  return send(res, 200, { status: result.status });
}

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  // Sonde de santé interne (pas de rate limit, pas d'effet de bord).
  if (url === '/healthz') return send(res, 200, { status: 'ok' });

  if (url !== '/api/v1/report') return send(res, 404, { status: 'invalid', error: 'not found' });

  if (req.method === 'OPTIONS') { res.writeHead(204, CORS); return res.end(); }
  if (req.method !== 'POST') {
    res.writeHead(405, { Allow: 'POST, OPTIONS', ...CORS });
    return res.end(JSON.stringify({ status: 'invalid', error: 'method not allowed' }));
  }

  const ct = (req.headers['content-type'] || '').split(';')[0].trim().toLowerCase();
  if (ct !== 'application/json') return send(res, 415, { status: 'invalid', error: 'content-type' });

  if (rateLimited(clientIp(req))) return send(res, 429, { status: 'invalid', error: 'rate limited' });

  handleReport(req, res).catch((e) => {
    console.error('[handler]', e);
    if (!res.headersSent) send(res, 500, { status: 'invalid', error: 'server error' });
  });
});

server.listen(PORT, () => {
  console.log(`utiq report endpoint :${PORT} (rate ${RL_MAX}/${RL_WINDOW_MS}ms, seuil notif ${NOTIFY_THRESHOLD})`);
  refreshKnown();
});
