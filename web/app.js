const tools = ['images', 'yts', 'rarbg', 'porn', 'bitmagnet'];
let activeTool = 'images';
let activeJobId = null;

const toolButtons = document.getElementById('toolButtons');
const configEditor = document.getElementById('configEditor');
const loadConfigBtn = document.getElementById('loadConfig');
const saveConfigBtn = document.getElementById('saveConfig');
const startJobBtn = document.getElementById('startJob');
const jobList = document.getElementById('jobList');
const jobLogs = document.getElementById('jobLogs');

const renderToolButtons = () => {
  toolButtons.innerHTML = '';
  tools.forEach((tool) => {
    const button = document.createElement('button');
    button.textContent = tool;
    if (tool === activeTool) {
      button.classList.add('secondary');
    }
    button.addEventListener('click', () => {
      activeTool = tool;
      renderToolButtons();
      loadConfig();
    });
    toolButtons.appendChild(button);
  });
};

const loadConfig = async () => {
  const response = await fetch(`/api/config/${activeTool}`);
  if (!response.ok) {
    configEditor.value = `Failed to load config for ${activeTool}`;
    return;
  }
  const data = await response.json();
  configEditor.value = JSON.stringify(data, null, 2);
};

const saveConfig = async () => {
  try {
    const body = JSON.parse(configEditor.value || '{}');
    const response = await fetch(`/api/config/${activeTool}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json();
      alert(err.error || 'Failed to save config');
      return;
    }
    alert('Config saved.');
  } catch (error) {
    alert(`Invalid JSON: ${error.message}`);
  }
};

const startJob = async () => {
  startJobBtn.disabled = true;
  const response = await fetch(`/api/jobs/${activeTool}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: configEditor.value ? configEditor.value : '{}',
  });
  startJobBtn.disabled = false;
  if (!response.ok) {
    const err = await response.json();
    alert(err.error || 'Failed to start job');
    return;
  }
  const job = await response.json();
  activeJobId = job.id;
  await refreshJobs();
};

const renderJobs = (jobs) => {
  jobList.innerHTML = '';
  jobs.forEach((job) => {
    const card = document.createElement('div');
    card.className = 'job-card';
    if (job.id === activeJobId) {
      card.classList.add('active');
    }
    card.innerHTML = `<strong>${job.tool}</strong> — ${job.status}<br/><small>${job.startedAt || ''}</small>`;
    card.addEventListener('click', () => {
      activeJobId = job.id;
      renderJobs(jobs);
      renderLogs(job);
    });
    jobList.appendChild(card);
  });
};

const renderLogs = (job) => {
  if (!job) {
    jobLogs.textContent = '';
    return;
  }
  const lines = (job.logs || []).map((entry) => `[${entry.timestamp}] [${entry.level}] ${entry.message}`);
  jobLogs.textContent = lines.join('\n');
};

const refreshJobs = async () => {
  const response = await fetch('/api/jobs');
  if (!response.ok) return;
  const data = await response.json();
  renderJobs(data.jobs);
  const active = data.jobs.find((job) => job.id === activeJobId);
  if (active) {
    renderLogs(active);
  }
};

renderToolButtons();
loadConfig();
refreshJobs();
setInterval(refreshJobs, 5000);

loadConfigBtn.addEventListener('click', loadConfig);
saveConfigBtn.addEventListener('click', saveConfig);
startJobBtn.addEventListener('click', startJob);
