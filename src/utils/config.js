const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const getConfigCandidates = (configName) => {
  return [
    path.join(process.cwd(), configName),
    path.join(process.cwd(), 'configs', configName),
    path.join(__dirname, '..', '..', 'configs', configName),
  ];
};

const readConfiguration = (configName) => {
  const candidates = getConfigCandidates(configName);
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      const content = fs.readFileSync(candidate, 'utf-8');
      return yaml.load(content) || {};
    }
  }
  throw new Error(`Config ${configName} not found in ${candidates.join(', ')}`);
};

const writeConfiguration = (configName, data) => {
  const target = path.join(process.cwd(), configName);
  const content = yaml.dump(data, { lineWidth: 120 });
  fs.writeFileSync(target, content, 'utf-8');
  return target;
};

module.exports = {
  readConfiguration,
  writeConfiguration,
};
