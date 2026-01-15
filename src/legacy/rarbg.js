const { downloadFile } = require("../downloader");

async function runRarbg({ url, outputDir }) {
  if (!url) {
    throw new Error("url is required");
  }
  return downloadFile(url, outputDir);
}

module.exports = {
  runRarbg,
};
