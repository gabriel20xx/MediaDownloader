const { Pool } = require("pg");

let pool;

function getPool() {
  if (!pool) {
    const connectionString = process.env.POSTGRESQL_URL;
    if (!connectionString) {
      throw new Error("POSTGRESQL_URL is not set");
    }
    pool = new Pool({ connectionString });
  }
  return pool;
}

async function initDb() {
  const client = await getPool().connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS download_jobs (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        cron TEXT NOT NULL,
        enabled BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS download_logs (
        id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES download_jobs(id) ON DELETE CASCADE,
        status TEXT NOT NULL,
        message TEXT,
        started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        finished_at TIMESTAMPTZ
      );
    `);
  } finally {
    client.release();
  }
}

async function query(text, params) {
  const res = await getPool().query(text, params);
  return res;
}

module.exports = {
  getPool,
  initDb,
  query,
};
