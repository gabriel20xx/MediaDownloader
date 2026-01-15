const cron = require("node-cron");
const path = require("path");
const { downloadFile } = require("./downloader");
const { query } = require("./db");

const scheduledTasks = new Map();
const downloadsDir = path.join(process.cwd(), "downloads");

async function runJob(job) {
  const logStart = await query(
    "INSERT INTO download_logs (job_id, status, message) VALUES ($1, $2, $3) RETURNING id",
    [job.id, "running", "started"]
  );
  const logId = logStart.rows[0].id;

  try {
    const filePath = await downloadFile(job.url, downloadsDir);
    await query(
      "UPDATE download_logs SET status = $1, message = $2, finished_at = NOW() WHERE id = $3",
      ["success", `saved to ${filePath}`, logId]
    );
  } catch (error) {
    await query(
      "UPDATE download_logs SET status = $1, message = $2, finished_at = NOW() WHERE id = $3",
      ["failed", error.message, logId]
    );
  }
}

function unscheduleJob(jobId) {
  const existing = scheduledTasks.get(jobId);
  if (existing) {
    existing.stop();
    scheduledTasks.delete(jobId);
  }
}

function scheduleJob(job) {
  unscheduleJob(job.id);
  if (!job.enabled) return;

  if (!cron.validate(job.cron)) {
    throw new Error("Invalid cron expression");
  }

  const task = cron.schedule(job.cron, () => {
    runJob(job);
  });

  scheduledTasks.set(job.id, task);
}

async function scheduleAllJobs() {
  const result = await query("SELECT * FROM download_jobs ORDER BY id ASC");
  for (const job of result.rows) {
    scheduleJob(job);
  }
}

module.exports = {
  runJob,
  scheduleJob,
  scheduleAllJobs,
  unscheduleJob,
};
