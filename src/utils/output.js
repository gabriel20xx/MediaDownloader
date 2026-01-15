const fs = require('fs');
const path = require('path');

const Level = {
  SUCCESS: 'SUCCESS',
  SKIP: 'SKIP',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  INFO: 'INFO',
};

const ensureDir = (dirPath) => {
  fs.mkdirSync(dirPath, { recursive: true });
};

const getLogPaths = (logsDirectory, prefix) => {
  const now = new Date();
  const year = String(now.getFullYear());
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const date = `${year}-${month}-${day}`;
  const directoryPath = path.join(logsDirectory, year, month, day);
  ensureDir(directoryPath);
  return {
    debugLogFile: path.join(directoryPath, `${date}-${prefix}Debug.log`),
    downloadLogFile: path.join(directoryPath, `${date}-${prefix}Download.log`),
  };
};

const formatLine = (message, level) => {
  const now = new Date();
  const time = now.toTimeString().split(' ')[0];
  return `[${time}] [${level}] ${message}`;
};

const writeLog = (filePath, line) => {
  fs.appendFileSync(filePath, `${line}\n`);
};

const createLogger = ({ logsDirectory, prefix, onLog }) => {
  const { debugLogFile, downloadLogFile } = getLogPaths(logsDirectory, prefix);

  const log = (message, level = Level.INFO, logger = 'debug') => {
    const line = formatLine(message, level);
    const targetFile = logger === 'download' ? downloadLogFile : debugLogFile;
    writeLog(targetFile, line);
    if (onLog) {
      onLog({ timestamp: new Date().toISOString(), level, message, logger });
    }
    // eslint-disable-next-line no-console
    console.log(line);
  };

  return {
    log,
    Level,
  };
};

module.exports = {
  Level,
  createLogger,
};
