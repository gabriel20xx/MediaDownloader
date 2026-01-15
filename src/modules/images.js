const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');
const axios = require('axios');
const { readConfiguration } = require('../utils/config');

const DEFAULTS = {
  GALLERY_OVERVIEW_BASE_URL_INPUT: 'https://izispicy.com/babes/',
  GALLERY_LINK_SELECTOR: 'h1.zag_block > a',
  GALLERY_TITLE_SELECTOR: 'h1.zag_block',
  IMAGE_SELECTOR: 'div.imgbox img',
  GALLERY_NEXT_PAGE_SELECTOR: '#post-list > div:nth-child(6) > div > b:nth-child(3) > a',
  DOWNLOAD_FOLDER: 'Z:/Samples/Izispicy',
  REQUEST_TIMEOUT: 30,
  IMAGE_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'],
  VIDEO_SKIP_PHRASE: '(VIDEO)',
};

const sanitizeFilename = (name) => {
  const safe = String(name)
    .replace(/[<>:"/\\|?*]/g, '_')
    .replace(/[\s_]+/g, '_')
    .replace(/^[_\s]+|[_\s]+$/g, '');

  if (safe === extractAndFormatDate(safe)) {
    return `${safe}_gallery`;
  }
  return safe || 'untitled_gallery';
};

const extractAndFormatDate = (urlString) => {
  const match = urlString.match(/(\d{4})\/(\d{2})\/(\d{2})/);
  if (!match) return null;
  const [, year, month, day] = match;
  const y = Number(year);
  const m = Number(month);
  const d = Number(day);
  if (y >= 1990 && y <= 2099 && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
    return `${year}_${month}_${day}`;
  }
  return null;
};

const extractCountFromTitle = (title) => {
  if (!title) return null;
  const match = title.match(/\(\s*(\d+)\s*PICS?\s*\)/i);
  if (!match) return null;
  return Number(match[1]);
};

const getBaseOverviewUrl = (urlInput) => {
  const cleaned = urlInput.split('#')[0].split('?')[0].replace(/page\/\d+\/?$/, '');
  return cleaned.endsWith('/') ? cleaned : `${cleaned}/`;
};

const countImageFiles = (dirPath, imageExtensions) => {
  if (!fs.existsSync(dirPath)) return 0;
  const files = fs.readdirSync(dirPath);
  return files.filter((file) => imageExtensions.includes(path.extname(file).toLowerCase())).length;
};

const downloadImage = async (imgUrl, savePath, timeoutSeconds) => {
  const response = await axios.get(imgUrl, { responseType: 'stream', timeout: timeoutSeconds * 1000 });
  await new Promise((resolve, reject) => {
    const writer = fs.createWriteStream(savePath);
    response.data.pipe(writer);
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
};

const fetchHtml = async (url, timeoutSeconds) => {
  const response = await axios.get(url, { timeout: timeoutSeconds * 1000 });
  return { html: response.data, finalUrl: response.request?.res?.responseUrl || url };
};

const runImages = async ({ log }, overrides = {}) => {
  const config = readConfiguration('images.yaml');
  const settings = {
    ...DEFAULTS,
    ...config,
    ...overrides,
  };

  const imageExtensions = new Set(settings.IMAGE_EXTENSIONS || DEFAULTS.IMAGE_EXTENSIONS);
  const downloadFolder = settings.DOWNLOAD_FOLDER;
  fs.mkdirSync(downloadFolder, { recursive: true });

  const processedOrSkipped = new Set();
  const baseOverviewUrl = getBaseOverviewUrl(settings.GALLERY_OVERVIEW_BASE_URL_INPUT);
  log(`Using Base Overview URL for pagination: ${baseOverviewUrl}`, 'INFO');

  let overviewPageNum = 1;
  while (true) {
    const currentOverviewUrl = `${baseOverviewUrl}page/${overviewPageNum}/`;
    log(`Attempting Overview Page ${overviewPageNum}: ${currentOverviewUrl}`, 'INFO');

    let html;
    let actualUrl;
    try {
      const result = await fetchHtml(currentOverviewUrl, settings.REQUEST_TIMEOUT);
      html = result.html;
      actualUrl = result.finalUrl;
    } catch (error) {
      log(`Failed to fetch overview page ${overviewPageNum}. Assuming end. ${error.message}`, 'WARNING');
      break;
    }

    const $ = cheerio.load(html);
    const galleryElements = $(settings.GALLERY_LINK_SELECTOR).toArray();
    log(`Found ${galleryElements.length} potential gallery link elements on this overview page.`, 'INFO');
    if (!galleryElements.length) {
      log(`No gallery links found on overview page ${overviewPageNum}. Assuming end.`, 'WARNING');
      break;
    }

    const galleryLinks = [];
    for (const element of galleryElements) {
      const href = $(element).attr('href');
      if (!href) continue;
      const fullUrl = new URL(href, actualUrl).toString();
      if (!processedOrSkipped.has(fullUrl) && !galleryLinks.includes(fullUrl)) {
        galleryLinks.push(fullUrl);
      }
    }

    log(`Found ${galleryLinks.length} new unique gallery links to check/process from this page.`, 'INFO');

    for (let index = 0; index < galleryLinks.length; index += 1) {
      const galleryUrl = galleryLinks[index];
      log(`Checking Gallery ${index + 1}/${galleryLinks.length}: ${galleryUrl}`, 'INFO');

      let galleryHtml;
      let actualGalleryUrl = galleryUrl;
      try {
        const result = await fetchHtml(galleryUrl, settings.REQUEST_TIMEOUT);
        galleryHtml = result.html;
        actualGalleryUrl = result.finalUrl;
      } catch (error) {
        log(`Failed to fetch gallery page. Skipping. ${error.message}`, 'WARNING');
        processedOrSkipped.add(galleryUrl);
        continue;
      }

      const gallery$ = cheerio.load(galleryHtml);
      const titleElement = gallery$(settings.GALLERY_TITLE_SELECTOR).first();
      const originalTitle = titleElement.text().trim() || 'Untitled';
      log(`Original Title: '${originalTitle}'`, 'INFO');

      if (originalTitle.includes(settings.VIDEO_SKIP_PHRASE)) {
        log(`SKIPPING: Title contains '${settings.VIDEO_SKIP_PHRASE}'.`, 'INFO');
        processedOrSkipped.add(galleryUrl);
        continue;
      }

      const expectedCount = extractCountFromTitle(originalTitle);
      const formattedDate = extractAndFormatDate(galleryUrl);

      const titleNoVideo = originalTitle.replace(settings.VIDEO_SKIP_PHRASE, '').trim();
      const baseTitle = titleNoVideo.replace(/(\s*\(.*\)\s*)$/i, '').trim() || 'untitled_gallery';
      const topLevelFolderName = sanitizeFilename(baseTitle);

      const subFolderParts = [baseTitle];
      if (formattedDate) subFolderParts.push(formattedDate);
      if (expectedCount !== null && expectedCount !== undefined) subFolderParts.push(`(${expectedCount} PICS)`);
      const galleryName = sanitizeFilename(subFolderParts.join(' '));
      const galleryFolderPath = path.join(downloadFolder, topLevelFolderName, galleryName);

      log(`Base Title (for top folder): '${topLevelFolderName}'`, 'INFO');
      log(`Gallery Name (for sub-folder): '${galleryName}'`, 'INFO');
      log(`Expected Image Count from Title: ${expectedCount ?? 'Unknown'}`, 'INFO');
      log(`Checking Folder Path: '${galleryFolderPath}'`, 'INFO');

      const folderExists = fs.existsSync(galleryFolderPath);
      const localFileCount = folderExists ? countImageFiles(galleryFolderPath, Array.from(imageExtensions)) : 0;

      if (folderExists && expectedCount && localFileCount >= expectedCount) {
        log(`SKIPPING download/pagination: Local count (${localFileCount}) >= Expected count (${expectedCount}).`, 'INFO');
        processedOrSkipped.add(galleryUrl);
        continue;
      }

      if (folderExists) {
        log(`PROCESSING: Folder exists but local count (${localFileCount}) < expected count (${expectedCount ?? 'Unknown'}), or expected count unknown.`, 'INFO');
      } else {
        log('PROCESSING: Folder not found. Proceeding with full download.', 'INFO');
      }

      processedOrSkipped.add(galleryUrl);
      fs.mkdirSync(galleryFolderPath, { recursive: true });

      let currentPage = 1;
      let currentGalleryUrl = actualGalleryUrl;

      while (true) {
        log(`Scraping Page ${currentPage} in gallery '${galleryName}'...`, 'INFO');
        log(`Current URL: ${currentGalleryUrl}`, 'INFO');

        if (currentPage > 1) {
          try {
            const result = await fetchHtml(currentGalleryUrl, settings.REQUEST_TIMEOUT);
            galleryHtml = result.html;
            actualGalleryUrl = result.finalUrl;
          } catch (error) {
            log(`Failed to fetch gallery page ${currentPage}. Assuming end. ${error.message}`, 'WARNING');
            break;
          }
        }

        const page$ = cheerio.load(galleryHtml);
        const imageElements = page$(settings.IMAGE_SELECTOR).toArray();
        log(`Found ${imageElements.length} image elements on this page.`, 'INFO');

        for (const element of imageElements) {
          const src = page$(element).attr('src') || page$(element).attr('data-src');
          if (!src) continue;
          const fullImgUrl = new URL(src, actualGalleryUrl).toString();
          const imgName = sanitizeFilename(path.basename(new URL(fullImgUrl).pathname));
          const savePath = path.join(galleryFolderPath, imgName);
          if (fs.existsSync(savePath)) {
            log(`SKIP existing image: ${imgName}`, 'SKIP');
            continue;
          }
          if (!imageExtensions.has(path.extname(imgName).toLowerCase())) {
            continue;
          }
          try {
            await downloadImage(fullImgUrl, savePath, settings.REQUEST_TIMEOUT);
            log(`Downloaded image: ${imgName}`, 'SUCCESS');
          } catch (error) {
            log(`ERROR downloading ${fullImgUrl}: ${error.message}`, 'ERROR');
          }
        }

        const nextLink = page$(settings.GALLERY_NEXT_PAGE_SELECTOR).attr('href');
        if (nextLink) {
          currentGalleryUrl = new URL(nextLink, actualGalleryUrl).toString();
          currentPage += 1;
          continue;
        }

        break;
      }
    }

    overviewPageNum += 1;
  }
};

module.exports = {
  runImages,
};
