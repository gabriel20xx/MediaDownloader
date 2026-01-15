const { runImages } = require('./images');
const { runYts } = require('./yts');
const { runRarbg } = require('./rarbg');
const { runPorn } = require('./porn');
const { runBitmagnet } = require('./bitmagnet');

const registry = {
  images: runImages,
  yts: runYts,
  rarbg: runRarbg,
  porn: runPorn,
  bitmagnet: runBitmagnet,
};

module.exports = {
  registry,
};
