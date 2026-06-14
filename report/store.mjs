// Stockage partagé des signalements Utiq Tracker.
// Utilisé par le service HTTP (conteneur) ET par le CLI de modération (hôte).
// Zéro dépendance : verrou par lockfile + écriture atomique (temp + rename).

import { promises as fs } from 'node:fs';
import path from 'node:path';

const FILE_PENDING = 'pending-reports.json';
const FILE_RESOLVED = 'resolved-reports.json';
const FILE_LOCK = 'pending-reports.lock';

export function paths(dir) {
  return {
    pending: path.join(dir, FILE_PENDING),
    resolved: path.join(dir, FILE_RESOLVED),
    lock: path.join(dir, FILE_LOCK),
  };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Verrou inter-process : un seul écrivain à la fois (service + CLI coordonnés).
// Lockfile exclusif (wx). Lock périmé (> staleMs) cassé automatiquement.
export async function withLock(dir, fn, { retries = 200, delay = 25, staleMs = 10000 } = {}) {
  const { lock } = paths(dir);
  let fh = null;
  for (let i = 0; i < retries && !fh; i++) {
    try {
      fh = await fs.open(lock, 'wx');
      await fh.writeFile(`${process.pid}\n`);
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      try {
        const st = await fs.stat(lock);
        if (Date.now() - st.mtimeMs > staleMs) { await fs.rm(lock, { force: true }); continue; }
      } catch { /* lock disparu entre-temps */ }
      await sleep(delay);
    }
  }
  if (!fh) throw new Error('verrou indisponible (pending-reports.lock)');
  try {
    return await fn();
  } finally {
    try { await fh.close(); } catch { /* ignore */ }
    try { await fs.rm(lock, { force: true }); } catch { /* ignore */ }
  }
}

export async function readJsonArray(p) {
  try {
    const data = JSON.parse(await fs.readFile(p, 'utf8'));
    return Array.isArray(data) ? data : [];
  } catch (e) {
    if (e.code === 'ENOENT') return [];
    throw e;
  }
}

// Écriture atomique : fichier temporaire dans le même dossier puis rename().
// Un lecteur externe ne voit jamais un JSON partiel. Permissions 600.
export async function atomicWrite(p, data) {
  const dir = path.dirname(p);
  const tmp = path.join(dir, `.${path.basename(p)}.${process.pid}.${Date.now()}.tmp`);
  const fh = await fs.open(tmp, 'w', 0o600);
  try {
    await fh.writeFile(`${JSON.stringify(data, null, 2)}\n`);
    await fh.sync();
  } finally {
    await fh.close();
  }
  await fs.rename(tmp, p);
}

// --- Validation du domaine (FQDN public plausible, en lowercase) ---

export function normalizeDomain(input) {
  if (typeof input !== 'string') return null;
  let d = input.trim().toLowerCase();
  if (d.endsWith('.')) d = d.slice(0, -1); // tolère un point final (FQDN absolu)
  return d;
}

// Chaque label : 1-63 car., alphanumérique, tiret interne uniquement.
const FQDN_RE = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/;
const TLD_ALPHA_RE = /\.[a-z]{2,}$/;          // doit finir par un TLD alphabétique
const IPV4_RE = /^\d{1,3}(\.\d{1,3}){3}$/;

export function validateDomain(d) {
  if (!d) return false;
  if (d.length < 5 || d.length > 253) return false;
  if (d === 'localhost') return false;
  if (d.endsWith('.local') || d.endsWith('.localhost')) return false;
  if (d.includes(':')) return false;          // IPv6 ou host:port
  if (d.includes('..')) return false;
  if (!d.includes('.')) return false;
  if (IPV4_RE.test(d)) return false;          // adresse IPv4 nue
  if (!TLD_ALPHA_RE.test(d)) return false;    // rejette dernier label numérique
  if (!FQDN_RE.test(d)) return false;
  return true;
}
