import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

async function addMDRRMORole() {
  try {
    console.log('Checking if MDRRMO role exists...');
    
    const { rows } = await pool.query(`
      SELECT enumlabel FROM pg_enum 
      WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')
      ORDER BY enumlabel
    `);
    
    console.log('Current roles:', rows.map(r => r.enumlabel).join(', '));
    
    const hasMDRRMO = rows.some(r => r.enumlabel === 'MDRRMO');
    
    if (hasMDRRMO) {
      console.log('✓ MDRRMO role already exists');
    } else {
      console.log('Adding MDRRMO role...');
      await pool.query(`ALTER TYPE user_role ADD VALUE 'MDRRMO'`);
      console.log('✓ MDRRMO role added successfully');
    }
    
    // Show final list
    const { rows: finalRoles } = await pool.query(`
      SELECT enumlabel FROM pg_enum 
      WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'user_role')
      ORDER BY enumlabel
    `);
    
    console.log('\nFinal roles:', finalRoles.map(r => r.enumlabel).join(', '));
    
  } catch (err) {
    console.error('Error:', err.message);
  } finally {
    await pool.end();
  }
}

addMDRRMORole();
