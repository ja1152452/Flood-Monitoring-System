import { query } from './src/config/db.js';

try {
  await query("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'MSWDO'");
  console.log('✓ Added MSWDO to user_role enum');
} catch (e) {
  console.log('Role note:', e.message);
}

try {
  await query(`
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS evacuation_center_id UUID
    REFERENCES evacuation_centers(id) ON DELETE SET NULL
  `);
  console.log('✓ Added evacuation_center_id column to users table');
} catch (e) {
  console.log('Column note:', e.message);
}

process.exit(0);
