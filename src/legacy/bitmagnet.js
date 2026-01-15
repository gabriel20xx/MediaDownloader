const { downloadFile } = require("../downloader");

async function runBitmagnet({ url, outputDir }) {
  if (!url) {
    throw new Error("url is required");
  }
  return downloadFile(url, outputDir);
}

module.exports = {
  runBitmagnet,
};
