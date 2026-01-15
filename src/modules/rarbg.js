const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');
const { readConfiguration } = require('../utils/config');
const { retryRequest } = require('../utils/request');

const DEFAULTS = {
  base_urls: [
    'https://www2.rarbggo.to/',
    'https://rargb.to/',
    'https://www.rarbgproxy.to/',
    'https://www.rarbgo.to/',
    'https://www.proxyrarbg.to/',
  ],
  use_index_page: true,
  use_search_queries: false,
  magnet_file: path.join(process.cwd(), 'Magnets.txt'),
  search_queries: [],
  delay: 5,
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const parseMagnet = (magnetFile, magnetLink, title, log) => {
  if (!fs.existsSync(magnetFile)) {
    fs.writeFileSync(magnetFile, `${magnetLink}\n`);
    log(`Created a new file and added magnet link for this torrent: ${title}`, 'INFO');
    return 1;
  }

  const existing = fs.readFileSync(magnetFile, 'utf-8').split('\n');
  if (!existing.includes(magnetLink)) {
    fs.appendFileSync(magnetFile, `${magnetLink}\n`);
    log(`Added magnet link: ${title}`, 'SUCCESS', 'download');
    return 1;
  }
  log(`Magnet link already exists in the file for this torrent: ${title}`, 'INFO');
  return 0;
};

const parseWebsite = async ({ url, baseUrls, magnetFile, userAgent, delay, log }) => {
  await sleep(delay * 1000);
  const response = await retryRequest({ url, userAgent, log, maxRetries: 5, sleepTime: 0, baseUrls });
  if (!response) {
    log(`Failed to retrieve the page: ${url}`, 'ERROR');
    return false;
  }

  log(`Parsing page: ${response.request?.res?.responseUrl || url}`, 'INFO');
  const $ = cheerio.load(response.data);
  const links = $('tr.table2ta > td:nth-child(2) > a').toArray();
  log(`Found ${links.length} links on the page.`, 'INFO');

  if (!links.length) {
    log('No links found on page, exiting script.', 'WARNING');
    return false;
  }

  let downloads = 0;
  for (const link of links) {
    await sleep(delay * 1000);
    const linkUrl = $(link).attr('href');
    if (!linkUrl) continue;

    const responseFollowed = await retryRequest({ url: linkUrl, userAgent, log, maxRetries: 5, sleepTime: 0, baseUrls });
    if (!responseFollowed) {
      log(`Failed to retrieve the movie page: ${linkUrl}`, 'WARNING');
      continue;
    }

    log(`Parsing movie page: ${responseFollowed.request?.res?.responseUrl || linkUrl}`, 'INFO');
    const detail$ = cheerio.load(responseFollowed.data);
    const magnetElement = detail$('td.tlista a').first();
    const magnetLink = magnetElement.attr('href');
    const titleElement = detail$('td.block b h1.black').first();
    const title = titleElement.text().trim();

    if (magnetLink && title) {
      downloads += parseMagnet(magnetFile, magnetLink, title, log);
    } else {
      log('No magnet link and/or title found on the page.', 'ERROR');
    }
  }

  return downloads > 0;
};

const runRarbg = async ({ log }, overrides = {}) => {
  const config = readConfiguration('rarbg.yml');
  const settings = { ...DEFAULTS, ...config, ...overrides };

  if (settings.use_index_page) {
    let pageNumber = 1;
    while (true) {
      const url = `xxx/${pageNumber}/`;
      const result = await parseWebsite({
        url,
        baseUrls: settings.base_urls,
        magnetFile: settings.magnet_file,
        userAgent: settings.user_agent,
        delay: settings.delay,
        log,
      });
      if (result) {
        pageNumber += 1;
      } else {
        break;
      }
    }
  }

  if (settings.use_search_queries) {
    for (const query of settings.search_queries || []) {
      let pageNumber = 1;
      while (true) {
        const url = `search/${pageNumber}/?search=${encodeURIComponent(query)}&category=xxx`;
        const result = await parseWebsite({
          url,
          baseUrls: settings.base_urls,
          magnetFile: settings.magnet_file,
          userAgent: settings.user_agent,
          delay: settings.delay,
          log,
        });
        if (result) {
          pageNumber += 1;
        } else {
          break;
        }
      }
    }
  }
};

module.exports = {
  runRarbg,
};
