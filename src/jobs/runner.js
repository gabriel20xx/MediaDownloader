const { registry } = require('../modules');
const { createLogger } = require('../utils/output');
const { createJob, updateJob, appendJobLog } = require('./registry');

const runJob = async ({ tool, overrides = {} }) => {
  if (!registry[tool]) {
    throw new Error(`Unknown tool: ${tool}`);
  }

  const job = createJob(tool);
  updateJob(job.id, { status: 'running', startedAt: new Date().toISOString() });

  const logger = createLogger({
    logsDirectory: overrides.logs_directory || './logs',
    prefix: overrides.prefix || tool.toUpperCase(),
    onLog: (entry) => appendJobLog(job.id, entry),
  });

  try {
    await registry[tool]({ log: logger.log, Level: logger.Level }, overrides);
    updateJob(job.id, { status: 'completed', finishedAt: new Date().toISOString() });
  } catch (error) {
    updateJob(job.id, { status: 'failed', finishedAt: new Date().toISOString(), error: error.message });
    logger.log(`Job failed: ${error.message}`, 'ERROR');
  }

  return job;
};

module.exports = {
  runJob,
};
