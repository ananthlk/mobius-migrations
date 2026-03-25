-- Synced from mobius-chat/db/schema/018_roster_upload_members.sql (Step 3 roster snapshot).

CREATE TABLE IF NOT EXISTS roster_upload_members (
    id BIGSERIAL PRIMARY KEY,
    upload_id TEXT NOT NULL,
    org_id TEXT,
    row_index INT NOT NULL DEFAULT 0,
    npi TEXT NOT NULL,
    display_name TEXT,
    address_line_1 TEXT,
    city TEXT,
    state TEXT,
    zip5 TEXT,
    source_row JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roster_upload_members_upload ON roster_upload_members (upload_id);
CREATE INDEX IF NOT EXISTS idx_roster_upload_members_upload_npi ON roster_upload_members (upload_id, npi);
