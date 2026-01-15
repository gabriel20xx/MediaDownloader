const { v4: uuidv4 } = require('uuid');

const jobs = new Map();

const createJob = (tool) => {
  const id = uuidv4();
  const job = {
    id,
    tool,
    status: 'queued',
    startedAt: null,
    finishedAt: null,
    error: null,
    logs: [],
  };
  jobs.set(id, job);
  return job;
};

const updateJob = (id, patch) => {
  const job = jobs.get(id);
  if (!job) {
    return null;
  }
  Object.assign(job, patch);
  return job;
};

const appendJobLog = (id, entry) => {
  const job = jobs.get(id);
  if (!job) {
    return null;
  }
  job.logs.push(entry);
  return job;
};

const getJob = (id) => jobs.get(id) || null;

const listJobs = () => Array.from(jobs.values()).sort((a, b) => {
  const aTime = a.startedAt ? new Date(a.startedAt).getTime() : 0;
  const bTime = b.startedAt ? new Date(b.startedAt).getTime() : 0;
  return bTime - aTime;
});

module.exports = {
  createJob,
  updateJob,
  appendJobLog,
  getJob,
  listJobs,
};
