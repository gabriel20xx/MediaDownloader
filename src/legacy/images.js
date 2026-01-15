const { downloadFile } = require("../downloader");

async function runImages({ url, outputDir }) {
  if (!url) {
    throw new Error("url is required");
  }
  return downloadFile(url, outputDir);
}

module.exports = {
  runImages,
};
