const express = require('express');
const path = require('path');
const { createApiRouter } = require('./routes/api');

const createApp = () => {
  const app = express();

  app.use(express.json({ limit: '2mb' }));
  app.use(express.urlencoded({ extended: true }));

  app.use('/api', createApiRouter());

  const webPath = path.join(process.cwd(), 'web');
  app.use(express.static(webPath));

  app.get('*', (req, res) => {
    res.sendFile(path.join(webPath, 'index.html'));
  });

  return app;
};

module.exports = { createApp };
