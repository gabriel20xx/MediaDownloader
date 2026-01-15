const express = require('express');
const { runJob } = require('../jobs/runner');
const { getJob, listJobs } = require('../jobs/registry');
const { readConfiguration, writeConfiguration } = require('../utils/config');

const CONFIG_MAP = {
  images: 'images.yaml',
  yts: 'yts.yml',
  rarbg: 'rarbg.yml',
  porn: 'porn.yml',
  bitmagnet: 'bitmagnet.yml',
};

const createApiRouter = () => {
  const router = express.Router();

  router.get('/health', (req, res) => {
    res.json({ status: 'ok' });
  });

  router.get('/jobs', (req, res) => {
    res.json({ jobs: listJobs() });
  });

  router.get('/jobs/:id', (req, res) => {
    const job = getJob(req.params.id);
    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }
    return res.json(job);
  });

  router.post('/jobs/:tool/start', async (req, res) => {
    const tool = req.params.tool;
    try {
      const job = await runJob({ tool, overrides: req.body || {} });
      res.json(job);
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  });

  router.get('/config/:tool', (req, res) => {
    const tool = req.params.tool;
    const configName = CONFIG_MAP[tool];
    if (!configName) {
      return res.status(404).json({ error: 'Unknown tool' });
    }
    try {
      const config = readConfiguration(configName);
      return res.json(config);
    } catch (error) {
      return res.status(404).json({ error: error.message });
    }
  });

  router.put('/config/:tool', (req, res) => {
    const tool = req.params.tool;
    const configName = CONFIG_MAP[tool];
    if (!configName) {
      return res.status(404).json({ error: 'Unknown tool' });
    }
    try {
      const savedPath = writeConfiguration(configName, req.body || {});
      return res.json({ savedPath });
    } catch (error) {
      return res.status(500).json({ error: error.message });
    }
  });

  return router;
};

module.exports = {
  createApiRouter,
};
