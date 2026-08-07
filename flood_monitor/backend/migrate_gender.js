import { query } from './src/config/db.js';

try {
  await query(`ALTER TABLE evacuation_families ADD COLUMN IF NOT EXISTS gender VARCHAR(20)`);
  console.log('✓ Added gender column to evacuation_families');
} catch (e) {
  console.log('Note:', e.message);
}

try {
  await query(`ALTER TABLE evacuation_family_members ADD COLUMN IF NOT EXISTS gender VARCHAR(20)`);
  console.log('✓ Added gender column to evacuation_family_members');
} catch (e) {
  console.log('Note:', e.message);
}

process.exit(0);
