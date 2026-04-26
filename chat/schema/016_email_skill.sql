-- Email skill (mobius-skills/email) — Phase 2 persistence
-- Tables: email_messages, email_audit, email_suppressions
-- DB: CHAT_RAG_DATABASE_URL (mobius_chat). Idempotent via IF NOT EXISTS.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS email_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key TEXT UNIQUE NOT NULL,
  actor TEXT NOT NULL,
  org TEXT,
  run_id TEXT,
  step_id TEXT,
  mode TEXT NOT NULL,
  intent TEXT,
  to_addrs TEXT[] NOT NULL,
  cc_addrs TEXT[] DEFAULT '{}',
  bcc_addrs TEXT[] DEFAULT '{}',
  subject TEXT NOT NULL,
  body_text TEXT NOT NULL,
  body_html TEXT,
  status TEXT NOT NULL,
  confirm_mode TEXT NOT NULL DEFAULT 'auto',
  confirmed_at TIMESTAMPTZ,
  confirmed_by TEXT,
  provider TEXT NOT NULL DEFAULT 'gmail',
  provider_message_id TEXT,
  provider_thread_id TEXT,
  error TEXT,
  attempts INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_email_messages_status ON email_messages(status, created_at);
CREATE INDEX IF NOT EXISTS ix_email_messages_actor ON email_messages(actor, created_at);
CREATE INDEX IF NOT EXISTS ix_email_messages_run ON email_messages(run_id) WHERE run_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS email_audit (
  id BIGSERIAL PRIMARY KEY,
  message_id UUID REFERENCES email_messages(id) ON DELETE CASCADE,
  actor TEXT,
  action TEXT NOT NULL,
  payload JSONB,
  ts TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_email_audit_msg ON email_audit(message_id, ts);

CREATE TABLE IF NOT EXISTS email_suppressions (
  email TEXT PRIMARY KEY,
  reason TEXT NOT NULL,
  added_by TEXT,
  ts TIMESTAMPTZ DEFAULT NOW()
);
