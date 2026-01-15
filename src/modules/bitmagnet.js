const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { readConfiguration } = require('../utils/config');

const DEFAULTS = {
  base_urls: ['http://192.168.2.45:3333'],
  use_index_page: false,
  use_search_queries: true,
  magnet_file: path.join(process.cwd(), 'Magnets.txt'),
  max_pages: 0,
  search_queries: [],
  include_one: null,
  include_all: null,
  exclude_one: null,
  exclude_all: null,
};

const ensureFile = (filePath) => {
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, '');
  }
};

const loadExisting = (filePath) => {
  if (!fs.existsSync(filePath)) return new Set();
  return new Set(fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean));
};

const saveMagnet = (magnetFile, link, log) => {
  const existing = loadExisting(magnetFile);
  if (existing.has(link)) {
    log(`Magnet link already exists in the file for this torrent: ${link}`, 'INFO');
    return 0;
  }
  fs.appendFileSync(magnetFile, `${link}\n`);
  log(`Added magnet link: ${link}`, 'SUCCESS', 'download');
  return 1;
};

const runSearch = async ({ baseUrl, magnetFile, maxPages, searchQuery, log }) => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });

  if (searchQuery) {
    log(`Using search query: ${searchQuery}`, 'INFO');
    await page.waitForTimeout(3000);
    await page.fill("input[placeholder='Search']", searchQuery);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(5000);
  }

  let pageNum = 1;
  let done = false;
  while (!done && (maxPages === 0 || pageNum <= maxPages)) {
    log(`Crawling page ${pageNum}`, 'INFO');

    const links = await page.$$eval('a[href^="magnet:"]', (anchors) => anchors.map((a) => a.href));
    for (const link of links) {
      saveMagnet(magnetFile, link, log);
    }

    const nextButton = await page.$("button[mattooltip='Next page']");
    if (!nextButton) {
      done = true;
      break;
    }

    const enabled = await nextButton.isEnabled();
    if (!enabled) {
      log('Reached the last page, going to next query.', 'INFO');
      done = true;
      break;
    }

    await nextButton.click();
    await page.waitForTimeout(3000);
    pageNum += 1;
  }

  await browser.close();
};

const runBitmagnet = async ({ log }, overrides = {}) => {
  const config = readConfiguration('bitmagnet.yml');
  const settings = { ...DEFAULTS, ...config, ...overrides };

  ensureFile(settings.magnet_file);

  if (settings.use_index_page) {
    await runSearch({
      baseUrl: settings.base_urls[0],
      magnetFile: settings.magnet_file,
      maxPages: settings.max_pages,
      searchQuery: null,
      log,
    });
  }

  if (settings.use_search_queries) {
    for (const query of settings.search_queries || []) {
      await runSearch({
        baseUrl: settings.base_urls[0],
        magnetFile: settings.magnet_file,
        maxPages: settings.max_pages,
        searchQuery: query,
        log,
      });
    }
  }
};

module.exports = {
  runBitmagnet,
};
