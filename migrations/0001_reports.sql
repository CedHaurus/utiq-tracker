CREATE TABLE IF NOT EXISTS reports (
  domain TEXT PRIMARY KEY,
  detected_by TEXT NOT NULL DEFAULT 'unknown',
  extension_version TEXT NOT NULL DEFAULT 'unknown',
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'pending',
  notified INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS reports_notified_idx ON reports(notified, count);
