#!/usr/bin/env node
// Modération CLI des signalements Utiq Tracker (lecture seule depuis l'hôte, via SSH).
//   node admin/moderate.mjs [list]            -> liste les pending, tri count décroissant
//   node admin/moderate.mjs approve <domain>  -> sort le domaine du pending (à ajouter dans data/source.json)
//   node admin/moderate.mjs reject  <domain>  -> rejette le domaine
// approve/reject archivent l'entrée dans resolved-reports.json. Verrou partagé avec le service.

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { withLock, readJsonArray, atomicWrite, paths } from '../report/store.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIR = process.env.REPORTS_DIR || path.join(__dirname, '..', 'reports');

const [, , cmd = 'list', arg] = process.argv;

async function list() {
  const { pending } = paths(DIR);
  const rows = await readJsonArray(pending);
  rows.sort((a, b) => (b.count - a.count) || (a.domain < b.domain ? -1 : 1));
  if (!rows.length) { console.log('Aucun signalement en attente.'); return; }
  console.log(`${rows.length} signalement(s) en attente (tri count décroissant):\n`);
  for (const e of rows) {
    const seen = `${(e.first_seen || '').slice(0, 10)}→${(e.last_seen || '').slice(0, 10)}`;
    console.log(`  ${String(e.count).padStart(3)}  ${e.domain.padEnd(40)} ${(e.detected_by || '').padEnd(12)} ${seen}${e.notified ? '  ✓notifié' : ''}`);
  }
}

async function resolve(decision, domain) {
  if (!domain) { console.error(`usage: moderate ${decision} <domain>`); process.exitCode = 1; return; }
  domain = domain.toLowerCase();
  const { pending, resolved } = paths(DIR);
  await withLock(DIR, async () => {
    const rows = await readJsonArray(pending);
    const idx = rows.findIndex((e) => e.domain === domain);
    if (idx < 0) throw new Error(`introuvable dans les pending: ${domain}`);
    const [entry] = rows.splice(idx, 1);
    entry.status = decision === 'approve' ? 'approved' : 'rejected';
    entry.resolved_at = new Date().toISOString();
    const archive = await readJsonArray(resolved);
    archive.push(entry);
    await atomicWrite(resolved, archive);
    await atomicWrite(pending, rows);
    console.log(`${domain} → ${entry.status}.`);
    if (decision === 'approve') {
      console.log("  → Ajoute-le maintenant dans data/source.json (avec name/url/description), puis rebuild pour publication dans sites.json.");
    }
  });
}

try {
  if (cmd === 'list') await list();
  else if (cmd === 'approve' || cmd === 'reject') await resolve(cmd, arg);
  else { console.log('usage: moderate [list] | approve <domain> | reject <domain>'); process.exitCode = 1; }
} catch (e) {
  console.error('erreur:', e.message);
  process.exitCode = 1;
}
