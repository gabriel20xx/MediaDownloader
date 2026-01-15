const { downloadFile } = require("../downloader");

async function runPorn({ url, outputDir }) {
  if (!url) {
    throw new Error("url is required");
  }
  return downloadFile(url, outputDir);
}

module.exports = {
  runPorn,
};
