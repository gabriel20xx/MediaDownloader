const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const cheerio = require('cheerio');
const { chromium } = require('playwright');
const { readConfiguration } = require('../utils/config');
const { retryRequest } = require('../utils/request');

const WEBSITES_JSON_PATH = path.join(process.cwd(), 'utils', 'websites.json');

const DEFAULTS = {
  verbose: false,
  websites: [],
  search_queries: [],
  scraped_filename: 'scraped_links.txt',
  downloaded_filename: 'downloaded_links.txt',
  file_path: '.',
  download_path: './downloads',
  logs_directory: './logs',
  prefix: 'PORN',
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
  downloader: 'yt-dlp',
  categories: [],
  sort_option: 'mv',
  date_filter: 'w',
  country_filter: 'world',
  max_videos: 1000,
  yt_dlp_path: 'yt-dlp',
  ffmpeg_path: 'ffmpeg',
};

const categoryMapping = {
  '60FPS': 105,
  Amateur: 3,
  Anal: 35,
  Arab: 98,
  Asian: 1,
  Babe: 'babe',
  Babysitter: 89,
  BBW: 6,
  'Behind The Scenes': 141,
  'Big Ass': 4,
  'Big Dick': 7,
  'Big Tits': 8,
  'Bisexual Male': 76,
  Blonde: 9,
  Blowjob: 13,
  Bondage: 10,
  Brazilian: 102,
  British: 96,
  Brunette: 11,
  Bukkake: 14,
  Cartoon: 86,
  Casting: 90,
  Celebrity: 12,
  'Closed Captions': 732,
  College: 'college',
  Compilation: 57,
  Cosplay: 241,
  Creampie: 15,
  Cuckold: 242,
  Cumshot: 16,
  Czech: 100,
  'Described Video': 'described-video',
  'Double Penetration': 72,
  Ebony: 17,
  Euro: 55,
  Exclusive: 115,
  Feet: 93,
  'Female Orgasm': 502,
  Fetish: 18,
  Fingering: 592,
  Fisting: 19,
  French: 94,
  Funny: 32,
  Gaming: 881,
  Gangbang: 80,
  Gay: 'gayporn',
  German: 95,
  Handjob: 20,
  Hardcore: 21,
  'HD Porn': 'hd',
  Hentai: 'hentai',
  Indian: 101,
  Interactive: 'interactive',
  Interracial: 25,
  Italian: 97,
  Japanese: 111,
  Korean: 103,
  Latina: 26,
  Lesbian: 27,
  Massage: 78,
  Masturbation: 22,
  Mature: 28,
  MILF: 29,
  'Muscular Men': 512,
  Music: 121,
  'Old/Young': 181,
  Orgy: 2,
  Parody: 201,
  Party: 53,
  Pissing: 211,
  'Popular With Women': 'popularwithwomen',
  Pornstar: 'pornstar',
  POV: 41,
  Public: 24,
  'Pussy Licking': 131,
  Reality: 31,
  'Red Head': 42,
  'Role Play': 81,
  Romantic: 522,
  'Rough Sex': 67,
  Russian: 99,
  School: 88,
  SFW: 'sfw',
  'Small Tits': 59,
  Smoking: 91,
  'Solo Female': 492,
  'Solo Male': 92,
  Squirt: 69,
  'Step Fantasy': 444,
  'Strap On': 542,
  Striptease: 33,
  'Tattooed Women': 562,
  Teen: 'teen',
  Threesome: 65,
  Toys: 23,
  Transgender: 'transgender',
  'Verified Amateurs': 138,
  'Verified Couples': 482,
  'Verified Models': 139,
  Vintage: 43,
  'Virtual Reality': 'vr',
  Webcam: 61,
};

const getCategoryNumber = (category) => categoryMapping[category] ?? category;

const loadWebsites = () => {
  const content = fs.readFileSync(WEBSITES_JSON_PATH, 'utf-8');
  return JSON.parse(content);
};

const ensureFile = (filePath) => {
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, '');
  }
};

const readLines = (filePath) => {
  if (!fs.existsSync(filePath)) return [];
  return fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);
};

const appendLine = (filePath, line) => {
  fs.appendFileSync(filePath, `${line}\n`);
};

const buildUrl = ({ template, params }) => {
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = params[key];
    return value !== undefined && value !== null ? String(value) : '';
  });
};

const buildLegacyUrl = ({ name, baseUrl, videoOverviewUrl, searchUrl, searchQueryParameter, pageIndexParameter, urlSuffix, query, page }) => {
  if ([
    'XNXX',
    'RedPorn',
    'HornyBank',
    'TeensYoung',
    'HelloPorn',
    'DirtyHomeClips',
    'Eporner',
    'PornTrex',
    'PornGo',
  ].includes(name)) {
    return `${baseUrl}${searchUrl}/${query}/${page}`;
  }
  if (['XVideos', 'RedTube', 'HQPorner'].includes(name)) {
    return `${baseUrl}?${searchQueryParameter}=${query}&${pageIndexParameter}=${page}`;
  }
  if (['Porn', 'Tnaflix', 'PornOne', '4Tube', 'PornTube', 'Bellesa'].includes(name)) {
    return `${baseUrl}${searchUrl}?${searchQueryParameter}=${query}&${pageIndexParameter}=${page}`;
  }
  if (['XHamster', 'SexyPorn', 'Motherless'].includes(name)) {
    return `${baseUrl}${searchUrl}/${query}?${pageIndexParameter}=${page}`;
  }
  if (['TabooTube', 'NewPorn'].includes(name)) {
    return `${baseUrl}${searchUrl}/${query}`;
  }
  if (name === 'PornHub') {
    return `${baseUrl}${videoOverviewUrl}/${searchUrl}?${searchQueryParameter}=${query}&${pageIndexParameter}=${page}`;
  }
  if (name === 'SpankBang') {
    return `${baseUrl}${searchQueryParameter}/${query}/${page}/?${urlSuffix}`;
  }
  if (name === 'YouPorn') {
    return `${baseUrl}${searchUrl}/?${searchQueryParameter}=${query}&${pageIndexParameter}=${page}`;
  }
  if (name === 'Fuq') {
    return `${baseUrl}${searchUrl}/${searchQueryParameter}/${query}?${pageIndexParameter}=${page}`;
  }
  if (name === 'NudeVista') {
    return `${baseUrl}?${searchQueryParameter}=${query}&${pageIndexParameter}=${(page - 1) * 25}`;
  }
  if (name === 'Beeg') {
    return `${baseUrl}${query}`;
  }
  if (name === 'SXYPrn') {
    return `${baseUrl}${query}.html?${pageIndexParameter}=${page}`;
  }
  if (name === 'YouJizz') {
    return `${baseUrl}${searchUrl}/${query}-${page}.html?`;
  }
  if (name === '3Movs') {
    return `${baseUrl}${searchUrl}/?${searchQueryParameter}=${query}`;
  }
  return null;
};

const fetchPageHtml = async ({ url, userAgent, preClickSelector, infiniteScroll, log }) => {
  if (preClickSelector || infiniteScroll) {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ userAgent });
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    if (preClickSelector) {
      try {
        await page.click(preClickSelector, { timeout: 10000 });
      } catch (error) {
        log(`Pre-click action failed: ${error.message}`, 'WARNING');
      }
    }

    if (infiniteScroll) {
      let previousHeight = 0;
      for (let i = 0; i < 25; i += 1) {
        const height = await page.evaluate(() => document.body.scrollHeight);
        if (height === previousHeight) break;
        previousHeight = height;
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await page.waitForTimeout(1500);
      }
    }

    const html = await page.content();
    await browser.close();
    return html;
  }

  const response = await retryRequest({ url, userAgent, log, maxRetries: 3, sleepTime: 2, baseUrls: [] });
  return response ? response.data : null;
};

const extractLinks = (html, selector, baseUrl) => {
  if (!html) return [];
  const $ = cheerio.load(html);
  return $(selector)
    .map((_, el) => $(el).attr('href'))
    .get()
    .filter(Boolean)
    .map((href) => (href.startsWith('/') ? new URL(href, baseUrl).toString() : href))
    .filter((href) => !href.includes('javascript:void(0)'));
};

const downloadVideo = async ({ ytDlpPath, ffmpegPath, downloadPath, filePath, videoName, href, log }) => {
  ensureFile(filePath);
  const existing = readLines(filePath);
  if (existing.includes(href)) {
    log(`Video already downloaded. Skipping: ${href}`, 'SKIP');
    return 'skipped';
  }

  fs.mkdirSync(downloadPath, { recursive: true });

  return new Promise((resolve) => {
    const args = [
      '-P',
      downloadPath,
      '--extractor-args',
      'generic:impersonate=chrome',
      '--ffmpeg-location',
      ffmpegPath,
      '-o',
      videoName,
      href,
    ];

    const proc = spawn(ytDlpPath, args, { stdio: 'inherit' });
    proc.on('close', (code) => {
      if (code === 0) {
        appendLine(filePath, href);
        log('Download successful.', 'SUCCESS');
        resolve('saved');
      } else {
        log(`Download failed with exit code ${code}.`, 'ERROR');
        resolve('failed');
      }
    });
  });
};

const runPorn = async ({ log }, overrides = {}) => {
  const config = readConfiguration('porn.yml');
  const settings = { ...DEFAULTS, ...config, ...overrides };

  const websites = loadWebsites();
  const selected = settings.websites.length
    ? websites.filter((site) => settings.websites.includes(site.name))
    : websites;

  const scrapedFile = path.join(settings.file_path, settings.scraped_filename);
  const downloadedFile = path.join(settings.file_path, settings.downloaded_filename);
  ensureFile(scrapedFile);
  ensureFile(downloadedFile);

  const scrapedLinks = new Set(readLines(scrapedFile));
  const downloadedLinks = new Set(readLines(downloadedFile));
  let totalSaved = 0;
  let totalSkipped = 0;
  let totalFailed = 0;

  for (const site of selected) {
    const baseUrl = site.base_url || site.baseUrl || '';
    const videoLocation = site.video_location;
    const preClickSelector = site.pre_click_action || null;
    const infiniteScroll = (site.site_property || site.site_properties || []).includes('has_infinite_scroll') || site.has_infinite_scroll;

    const queries = settings.search_queries.length ? settings.search_queries : [null];
    const categories = settings.categories.length ? settings.categories : [null];

    for (const query of queries) {
      for (const category of categories) {
        let page = 1;
        while (true) {
          let template = site.template_search_url || null;
          if (category && (site.template_category_url || site.template_special_category_url)) {
            if (site.category_special && site.template_special_category_url && site.category_special.includes(category)) {
              template = site.template_special_category_url;
            } else {
              template = site.template_category_url;
            }
          }

          const params = {
            base_url: baseUrl,
            query,
            category: site.name === 'PornHub' && category ? getCategoryNumber(category) : category,
            sort: settings.sort_option,
            date_filter: settings.date_filter,
            country_filter: settings.country_filter,
            page,
          };

          let url = null;
          if (template) {
            url = buildUrl({ template, params });
          } else if (query) {
            url = buildLegacyUrl({
              name: site.name,
              baseUrl,
              videoOverviewUrl: site.video_overview_url || '',
              searchUrl: site.search_url || '',
              searchQueryParameter: site.search_query_parameter || '',
              pageIndexParameter: site.page_index_parameter || '',
              urlSuffix: site.url_suffix || '',
              query,
              page,
            });
          }

          if (!url) {
            break;
          }
          log(`Parsing page ${page}: ${url}`, 'INFO');

          const html = await fetchPageHtml({
            url,
            userAgent: settings.user_agent,
            preClickSelector,
            infiniteScroll: !!site.has_infinite_scroll || !!site.site_property?.includes('has_infinite_scroll'),
            log,
          });

          const links = extractLinks(html, videoLocation, baseUrl);
          if (!links.length) {
            break;
          }

          for (const href of links) {
            if (scrapedLinks.has(href)) continue;
            scrapedLinks.add(href);
            appendLine(scrapedFile, href);
          }

          if (!site.is_first_page_different && !template.includes('{page}')) {
            break;
          }

          page += 1;
        }
      }
    }
  }

  const pendingLinks = Array.from(scrapedLinks).filter((link) => !downloadedLinks.has(link));
  const limited = pendingLinks.slice(0, settings.max_videos);

  for (const href of limited) {
    const result = await downloadVideo({
      ytDlpPath: settings.yt_dlp_path,
      ffmpegPath: settings.ffmpeg_path,
      downloadPath: settings.download_path,
      filePath: downloadedFile,
      videoName: '%(title)s.%(ext)s',
      href,
      log,
    });

    if (result === 'saved') totalSaved += 1;
    if (result === 'skipped') totalSkipped += 1;
    if (result === 'failed') totalFailed += 1;
  }

  log(`Videos Saved: ${totalSaved}, Skipped: ${totalSkipped}, Failed: ${totalFailed}, Total: ${limited.length}`, 'INFO');
};

module.exports = {
  runPorn,
};
