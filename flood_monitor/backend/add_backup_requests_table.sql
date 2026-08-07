-- Add backup_requests table for responder backup functionality

CREATE TABLE IF NOT EXISTS backup_requests (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lat           DOUBLE PRECISION NOT NULL,
  lng           DOUBLE PRECISION NOT NULL,
  message       TEXT,
  target_role   VARCHAR(50),
  status        VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_backup_requests_active ON backup_requests (status, created_at DESC) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_backup_requests_requester ON backup_requests (requester_id);
CREATE INDEX IF NOT EXISTS idx_backup_requests_target_role ON backup_requests (target_role, status);
