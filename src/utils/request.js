const axios = require('axios');
const { setTimeout: delay } = require('timers/promises');

const createClient = (userAgent) => {
  return axios.create({
    timeout: 20000,
    headers: {
      'User-Agent': userAgent,
      Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9',
      'Accept-Language': 'en-US,en;q=0.5',
      Connection: 'keep-alive',
      Referer: 'https://www.google.com/',
    },
    maxRedirects: 5,
  });
};

const retryRequest = async ({ url, userAgent, log, maxRetries = 3, sleepTime = 5, baseUrls = [] }) => {
  const client = createClient(userAgent);
  const candidates = baseUrls.length ? baseUrls.map((base) => new URL(url, base).toString()) : [url];
  let lastError;

  for (let attempt = 1; attempt <= maxRetries; attempt += 1) {
    for (const candidate of candidates) {
      try {
        const response = await client.get(candidate);
        return response;
      } catch (error) {
        lastError = error;
        if (log) {
          log(`Failed to retrieve ${candidate}: ${error.message}. Retrying (${attempt}/${maxRetries})...`, 'WARNING');
        }
      }
    }
    if (attempt < maxRetries) {
      await delay(sleepTime * 1000);
    }
  }

  if (log) {
    log(`Reached the maximum number of retries (${maxRetries}). Could not retrieve the page. Last error: ${lastError ? lastError.message : 'unknown'}`, 'ERROR');
  }
  return null;
};

module.exports = {
  retryRequest,
};
