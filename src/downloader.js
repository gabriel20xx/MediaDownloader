const fs = require("fs");
const path = require("path");
const { pipeline } = require("stream");
const { promisify } = require("util");
const axios = require("axios");

const streamPipeline = promisify(pipeline);

function getFileNameFromHeaders(headers) {
  const disposition = headers["content-disposition"];
  if (!disposition) return null;
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : null;
}

function getFileNameFromUrl(url) {
  try {
    const parsed = new URL(url);
    const base = path.basename(parsed.pathname);
    return base || null;
  } catch {
    return null;
  }
}

async function downloadFile(url, outputDir) {
  await fs.promises.mkdir(outputDir, { recursive: true });

  const response = await axios.get(url, {
    responseType: "stream",
    maxRedirects: 5,
    timeout: 30000,
  });

  const fileName =
    getFileNameFromHeaders(response.headers) ||
    getFileNameFromUrl(url) ||
    `download-${Date.now()}`;

  const filePath = path.join(outputDir, fileName);
  await streamPipeline(response.data, fs.createWriteStream(filePath));
  return filePath;
}

module.exports = {
  downloadFile,
};
