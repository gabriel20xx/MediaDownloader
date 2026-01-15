const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');
const { readConfiguration } = require('../utils/config');
const { retryRequest } = require('../utils/request');

const DEFAULTS = {
  base_urls: ['https://yts.mx/', 'https://yts.unblockit.download/'],
  download_directory: path.join(process.cwd(), 'output', 'Downloads'),
  alternative_download_directory: path.join(process.cwd(), 'output', 'Alternative'),
  logs_directory: path.join(process.cwd(), 'logs'),
  resolutions: ['2160p', '1080p.x265', '1080p', '720p'],
  languages: ['ENGLISH', 'GERMAN', 'SPANISH'],
  release_years: ['2020-2029', '2010-2019', '2000-2009', '1990-1999', '1980-1989', '1970-1979', '1950-1969', '1900-1949'],
  genres: ['action', 'adventure', 'animation', 'biography', 'comedy', 'crime', 'documentary', 'drama', 'family', 'film-noir', 'game-show', 'history', 'horror', 'music', 'musical', 'mystery', 'news', 'reality-tv', 'romance', 'sci-fi', 'sport', 'talk-show', 'thriller', 'war', 'western'],
  random_resolutions: false,
  random_languages: false,
  random_release_years: false,
  random_genres: false,
  skipped_threshold: 20,
  max_duration: 720,
  delay: 0,
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
};

const RESOLUTION_PRIORITY = {
  '2160p.x265': 6,
  '2160p': 5,
  '1080p.x265': 4,
  '1080p': 3,
  '720p.x265': 2,
  '720p': 1,
  None: 0,
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const findExisting = (dir, cleanedFilename, resolutionPattern, compressionPattern) => {
  if (!fs.existsSync(dir)) return [];
  const found = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...findExisting(full, cleanedFilename, resolutionPattern, compressionPattern));
    } else if (entry.isFile() && entry.name.includes(cleanedFilename)) {
      const match = entry.name.match(resolutionPattern);
      if (match) {
        let oldResolution = match[1];
        if (compressionPattern.test(entry.name)) oldResolution += '.x265';
        found.push({ path: full, resolution: oldResolution, quality: /\b(BluRay|WEBRip)\b/.exec(entry.name)?.[1] || null });
      }
    }
  }
  return found;
};

const parseDownload = async ({ baseUrls, url, language, alternativeDownloadDirectory, downloadDirectory, userAgent, log }) => {
  const response = await retryRequest({ url, userAgent, log, maxRetries: 5, sleepTime: 0, baseUrls });
  if (!response) {
    log('Failed to retrieve the download.', 'ERROR');
    return false;
  }

  const disposition = response.headers['content-disposition'] || '';
  let originalFilename = null;
  const match = disposition.match(/filename="?([^";]+)"?/i);
  if (match) {
    originalFilename = decodeURIComponent(match[1]);
  }
  if (!originalFilename) {
    originalFilename = path.basename(new URL(url, baseUrls[0]).toString());
  }

  const resolutionPattern = /\[(2160p|1080p|720p)\]/;
  const compressionPattern = /\[(x265)\]/;
  const resolutionMatch = originalFilename.match(resolutionPattern);
  let resolution = resolutionMatch ? resolutionMatch[1] : 'None';
  if (compressionPattern.test(originalFilename)) {
    resolution = `${resolution}.x265`;
  }

  log(`File found: ${originalFilename}`, 'INFO');
  const languagePath = language.charAt(0).toUpperCase() + language.slice(1).toLowerCase();

  const cleanedFilename = originalFilename.replace(/\((\d{4})\).*/, '($1)');
  const existing = findExisting(path.join(alternativeDownloadDirectory, languagePath), cleanedFilename, resolutionPattern, compressionPattern);
  for (const file of existing) {
    if (RESOLUTION_PRIORITY[file.resolution] > RESOLUTION_PRIORITY[resolution]) {
      return false;
    }
    if (RESOLUTION_PRIORITY[file.resolution] === RESOLUTION_PRIORITY[resolution] && file.quality === 'BluRay') {
      return false;
    }
    fs.unlinkSync(file.path);
  }

  const alternativePath = path.join(alternativeDownloadDirectory, languagePath, resolution);
  const downloadPath = path.join(downloadDirectory, languagePath, resolution);
  fs.mkdirSync(alternativePath, { recursive: true });
  fs.mkdirSync(downloadPath, { recursive: true });

  const storePath = path.join(alternativePath, originalFilename);
  const downloadFilePath = path.join(downloadPath, originalFilename);
  if (fs.existsSync(storePath)) {
    log(`File already exists on store path. Skipping...`, 'SKIP');
    return true;
  }

  fs.writeFileSync(downloadFilePath, response.data);
  fs.writeFileSync(storePath, response.data);
  log(`Downloaded file: ${originalFilename}`, 'SUCCESS', 'download');
  return true;
};

const parseWebsite = async ({ baseUrls, url, language, alternativeDownloadDirectory, downloadDirectory, pageNumber, delay, userAgent, log }) => {
  const response = await retryRequest({ url, userAgent, log, maxRetries: 5, sleepTime: 0, baseUrls });
  if (!response) {
    log(`Failed to retrieve the page ${url}`, 'ERROR');
    return false;
  }

  log(`Parsing page ${pageNumber}: ${url}`, 'INFO');
  const $ = cheerio.load(response.data);
  const links = $('div.browse-movie-wrap > a:nth-child(1)').toArray();
  log(`Found ${links.length} links on page ${pageNumber}`, 'INFO');

  for (const link of links) {
    const linkUrl = $(link).attr('href');
    if (!linkUrl) continue;
    const responseFollowed = await retryRequest({ url: linkUrl, userAgent, log, maxRetries: 5, sleepTime: 0, baseUrls });
    if (!responseFollowed) {
      log('Failed to retrieve the movie page.', 'WARNING');
      continue;
    }

    log(`Parsing movie page: ${linkUrl}`, 'INFO');
    const followed = cheerio.load(responseFollowed.data);
    const downloadLinks = followed('div#movie-info > p > a[href*="download"]').toArray();
    if (!downloadLinks.length) {
      log('No matching download link found.', 'WARNING');
      continue;
    }

    const downloadLink = downloadLinks[downloadLinks.length - 1];
    let downloadUrl = followed(downloadLink).attr('href') || '';
    if (!downloadUrl.startsWith('http')) {
      downloadUrl = new URL(downloadUrl, baseUrls[0]).toString();
    }
    log(`Found Download Link: ${downloadUrl}`, 'INFO');

    const result = await parseDownload({
      baseUrls,
      url: downloadUrl,
      language,
      alternativeDownloadDirectory,
      downloadDirectory,
      userAgent,
      log,
    });
    if (!result) {
      return false;
    }
    if (delay) {
      await sleep(delay * 1000);
    }
  }

  return true;
};

const runYts = async ({ log }, overrides = {}) => {
  const config = readConfiguration('yts.yml');
  const settings = { ...DEFAULTS, ...config, ...overrides };

  let { resolutions, languages, release_years: releaseYears, genres } = settings;
  if (settings.random_resolutions) resolutions = [...resolutions].sort(() => Math.random() - 0.5);
  if (settings.random_languages) languages = [...languages].sort(() => Math.random() - 0.5);
  if (settings.random_release_years) releaseYears = [...releaseYears].sort(() => Math.random() - 0.5);
  if (settings.random_genres) genres = [...genres].sort(() => Math.random() - 0.5);

  const startTime = Date.now();
  const maxDurationMs = settings.max_duration * 60 * 1000;
  let skippedSinceLastSuccess = 0;

  const languageMapping = { ENGLISH: 'en', GERMAN: 'de', SPANISH: 'es' };

  for (const resolution of resolutions) {
    for (const language of languages.map((lang) => lang.toUpperCase())) {
      const languageShort = languageMapping[language] || 'en';
      for (const releaseYear of releaseYears) {
        for (const genre of genres) {
          let pageNumber = 1;
          while (true) {
            if (Date.now() - startTime > maxDurationMs) {
              log(`Execution time exceeded ${settings.max_duration} minutes`, 'WARNING');
              return;
            }

            let yearSegment = releaseYear === 'all' ? '0' : releaseYear;
            let url = `browse-movies/0/${resolution}/${genre}/0/featured/${yearSegment}/${languageShort}`;
            if (pageNumber !== 1) {
              url += `?page=${pageNumber}`;
            }

            const result = await parseWebsite({
              baseUrls: settings.base_urls,
              url,
              language,
              alternativeDownloadDirectory: settings.alternative_download_directory,
              downloadDirectory: settings.download_directory,
              pageNumber,
              delay: settings.delay,
              userAgent: settings.user_agent,
              log,
            });

            if (result) {
              pageNumber += 1;
              skippedSinceLastSuccess = 0;
            } else {
              skippedSinceLastSuccess += 1;
              if (settings.skipped_threshold && skippedSinceLastSuccess >= settings.skipped_threshold) {
                log(`Reached the skipped threshold of ${settings.skipped_threshold}.`, 'INFO');
                break;
              }
              break;
            }
          }
        }
      }
    }
  }
};

module.exports = {
  runYts,
};
