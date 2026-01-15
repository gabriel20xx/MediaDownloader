const axios = require("axios");

async function get(url, options = {}) {
  const response = await axios.get(url, options);
  return response.data;
}

module.exports = {
  get,
};
