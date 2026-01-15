require("dotenv").config();

const path = require("path");
const express = require("express");
const morgan = require("morgan");
const { initDb, query } = require("./db");
const { scheduleAllJobs, scheduleJob, unscheduleJob, runJob } = require("./scheduler");

const PORT = process.env.PORT || 3000;

async function main() {
  if (!process.env.POSTGRESQL_URL) {
    throw new Error("POSTGRESQL_URL is required");
  }

  await initDb();
  await scheduleAllJobs();

  const app = express();
  app.use(morgan("dev"));
  app.use(express.json());
  app.use(express.static(path.join(__dirname, "..", "public")));

  app.get("/api/health", (req, res) => {
    res.json({ status: "ok" });
  });

  app.get("/api/jobs", async (req, res) => {
    const result = await query("SELECT * FROM download_jobs ORDER BY id ASC");
    res.json(result.rows);
  });

  app.post("/api/jobs", async (req, res) => {
    const { name, url, cron, enabled = true } = req.body || {};
    if (!name || !url || !cron) {
      return res.status(400).json({ error: "name, url, and cron are required" });
    }

    const result = await query(
      "INSERT INTO download_jobs (name, url, cron, enabled) VALUES ($1, $2, $3, $4) RETURNING *",
      [name, url, cron, enabled]
    );

    const job = result.rows[0];
    scheduleJob(job);
    res.status(201).json(job);
  });

  app.put("/api/jobs/:id", async (req, res) => {
    const id = Number(req.params.id);
    if (Number.isNaN(id)) {
      return res.status(400).json({ error: "invalid id" });
    }

    const { name, url, cron, enabled } = req.body || {};
    const result = await query(
      "UPDATE download_jobs SET name = $1, url = $2, cron = $3, enabled = $4, updated_at = NOW() WHERE id = $5 RETURNING *",
      [name, url, cron, enabled, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: "not found" });
    }

    const job = result.rows[0];
    scheduleJob(job);
    res.json(job);
  });

  app.delete("/api/jobs/:id", async (req, res) => {
    const id = Number(req.params.id);
    if (Number.isNaN(id)) {
      return res.status(400).json({ error: "invalid id" });
    }

    const result = await query("DELETE FROM download_jobs WHERE id = $1 RETURNING *", [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: "not found" });
    }

    unscheduleJob(id);
    res.status(204).send();
  });

  app.post("/api/jobs/:id/run", async (req, res) => {
    const id = Number(req.params.id);
    if (Number.isNaN(id)) {
      return res.status(400).json({ error: "invalid id" });
    }

    const result = await query("SELECT * FROM download_jobs WHERE id = $1", [id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: "not found" });
    }

    runJob(result.rows[0]);
    res.status(202).json({ status: "queued" });
  });

  app.get("/api/jobs/:id/logs", async (req, res) => {
    const id = Number(req.params.id);
    if (Number.isNaN(id)) {
      return res.status(400).json({ error: "invalid id" });
    }

    const result = await query(
      "SELECT * FROM download_logs WHERE job_id = $1 ORDER BY started_at DESC LIMIT 50",
      [id]
    );
    res.json(result.rows);
  });

  app.listen(PORT, () => {
    console.log(`MediaDownloader running on http://localhost:${PORT}`);
  });
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
