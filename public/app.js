const jobsContainer = document.getElementById("jobs");
const jobTemplate = document.getElementById("job-template");
const jobForm = document.getElementById("job-form");
const refreshButton = document.getElementById("refresh");

async function fetchJson(url, options) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || "Request failed");
  }

  if (response.status === 204) return null;
  return response.json();
}

function setLoading(isLoading) {
  refreshButton.disabled = isLoading;
  refreshButton.textContent = isLoading ? "Loading..." : "Refresh";
}

async function loadJobs() {
  setLoading(true);
  try {
    const jobs = await fetchJson("/api/jobs");
    jobsContainer.innerHTML = "";

    if (jobs.length === 0) {
      jobsContainer.innerHTML = "<p class=\"empty\">No jobs yet. Add one above.</p>";
      return;
    }

    for (const job of jobs) {
      const node = jobTemplate.content.cloneNode(true);
      const article = node.querySelector(".job");
      const name = node.querySelector(".job-name");
      const meta = node.querySelector(".job-meta");
      const toggleButton = node.querySelector(".toggle");
      const deleteButton = node.querySelector(".delete");
      const runButton = node.querySelector(".run");
      const logs = node.querySelector(".job-logs");

      name.textContent = job.name;
      meta.textContent = `${job.url} • ${job.cron}`;
      toggleButton.textContent = job.enabled ? "Disable" : "Enable";

      async function refreshLogs() {
        const logEntries = await fetchJson(`/api/jobs/${job.id}/logs`);
        logs.innerHTML = logEntries
          .map(
            (log) =>
              `<div class=\"log ${log.status}\"><span>${new Date(log.started_at).toLocaleString()}</span><span>${log.status}</span><span>${log.message || ""}</span></div>`
          )
          .join("");
      }

      toggleButton.addEventListener("click", async () => {
        await fetchJson(`/api/jobs/${job.id}`, {
          method: "PUT",
          body: JSON.stringify({
            name: job.name,
            url: job.url,
            cron: job.cron,
            enabled: !job.enabled,
          }),
        });
        await loadJobs();
      });

      deleteButton.addEventListener("click", async () => {
        await fetchJson(`/api/jobs/${job.id}`, { method: "DELETE" });
        await loadJobs();
      });

      runButton.addEventListener("click", async () => {
        await fetchJson(`/api/jobs/${job.id}/run`, { method: "POST" });
        await refreshLogs();
      });

      await refreshLogs();
      jobsContainer.appendChild(article);
    }
  } catch (error) {
    jobsContainer.innerHTML = `<p class=\"error\">${error.message}</p>`;
  } finally {
    setLoading(false);
  }
}

jobForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(jobForm);
  const payload = {
    name: formData.get("name"),
    url: formData.get("url"),
    cron: formData.get("cron"),
    enabled: formData.get("enabled") === "on",
  };

  try {
    await fetchJson("/api/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    jobForm.reset();
    jobForm.elements.enabled.checked = true;
    await loadJobs();
  } catch (error) {
    alert(error.message);
  }
});

refreshButton.addEventListener("click", loadJobs);

loadJobs();
