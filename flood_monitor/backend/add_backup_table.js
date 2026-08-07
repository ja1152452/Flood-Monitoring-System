import pg from 'pg';
import dotenv from 'dotenv';
dotenv.config();

const { Pool } = pg;
const pool = new Pool({
  host:     process.env.DB_HOST,
  port:     parseInt(process.env.DB_PORT),
  database: process.env.DB_NAME,
  user:     process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

async function addBackupRequestsTable() {
  const client = await pool.connect();
  console.log('Connected to database.');
  console.log('Adding backup_requests table...');
  
  try {
    await client.query('BEGIN');

    await client.query(`
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
    `);
    console.log('  ✓ backup_requests table created');

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_backup_requests_active ON backup_requests (status, created_at DESC) WHERE status = 'ACTIVE';
      CREATE INDEX IF NOT EXISTS idx_backup_requests_requester ON backup_requests (requester_id);
      CREATE INDEX IF NOT EXISTS idx_backup_requests_target_role ON backup_requests (target_role, status);
    `);
    console.log('  ✓ Indexes created');

    await client.query('COMMIT');
    console.log('\n✅ Migration complete! Backup requests feature is now ready.');

  } catch (err) {
    await client.query('ROLLBACK');
    console.error('❌ Migration failed:', err.message);
    console.error(err);
  } finally {
    client.release();
    await pool.end();
  }
}

addBackupRequestsTable();
