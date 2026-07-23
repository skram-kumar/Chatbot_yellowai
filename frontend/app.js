const API_BASE = "http://127.0.0.1:8000";
const TOKEN_KEY = "chatbot_jwt";

const state = {
  token: localStorage.getItem(TOKEN_KEY),
  authMode: "login",
  currentProject: null,
};

const views = {
  auth: document.getElementById("auth-view"),
  dashboard: document.getElementById("dashboard-view"),
  project: document.getElementById("project-view"),
};

function showView(name) {
  Object.entries(views).forEach(([key, el]) => {
    el.classList.toggle("hidden", key !== name);
  });
}

function setError(el, message) {
  if (!message) {
    el.classList.add("hidden");
    el.textContent = "";
    return;
  }
  el.textContent = message;
  el.classList.remove("hidden");
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new Error("Could not reach the server. Is the API running?");
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const detail = data && data.detail;
    let message = `Request failed (${response.status})`;
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail) && detail[0] && detail[0].msg) {
      message = detail[0].msg;
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}

function handleAuthExpired(message) {
  state.token = null;
  state.currentProject = null;
  localStorage.removeItem(TOKEN_KEY);
  setAuthMode("login");
  authForm.reset();
  setError(authError, message || "Your session expired. Please log in again.");
  showView("auth");
}

// ---------- Auth view ----------
const authForm = document.getElementById("auth-form");
const authError = document.getElementById("auth-error");
const authSubmit = document.getElementById("auth-submit");
const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");

function setAuthMode(mode) {
  state.authMode = mode;
  tabLogin.classList.toggle("active", mode === "login");
  tabRegister.classList.toggle("active", mode === "register");
  authSubmit.textContent = mode === "login" ? "Log In" : "Register";
  setError(authError, "");
}

tabLogin.addEventListener("click", () => setAuthMode("login"));
tabRegister.addEventListener("click", () => setAuthMode("register"));

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(authError, "");
  const email = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;

  authSubmit.disabled = true;
  try {
    if (state.authMode === "register") {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
    }
    const loginData = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    state.token = loginData.access_token;
    localStorage.setItem(TOKEN_KEY, state.token);
    authForm.reset();
    await loadDashboard();
  } catch (err) {
    setError(authError, err.message);
  } finally {
    authSubmit.disabled = false;
  }
});

document.querySelectorAll(".logout-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.token = null;
    state.currentProject = null;
    localStorage.removeItem(TOKEN_KEY);
    setAuthMode("login");
    authForm.reset();
    showView("auth");
  });
});

// ---------- Dashboard view ----------
const projectListEl = document.getElementById("project-list");
const projectListEmptyEl = document.getElementById("project-list-empty");
const newProjectForm = document.getElementById("new-project-form");
const dashboardError = document.getElementById("dashboard-error");

async function loadDashboard() {
  showView("dashboard");
  setError(dashboardError, "");
  try {
    const projects = await apiFetch("/projects");
    renderProjectList(projects);
  } catch (err) {
    if (err.status === 401) return handleAuthExpired();
    setError(dashboardError, err.message);
  }
}

function renderProjectList(projects) {
  projectListEl.innerHTML = "";
  projectListEmptyEl.classList.toggle("hidden", projects.length > 0);
  projects.forEach((project) => {
    const li = document.createElement("li");
    li.className = "project-item";

    const title = document.createElement("strong");
    title.textContent = project.name;

    const desc = document.createElement("span");
    desc.className = "muted";
    desc.textContent = project.description || "No description";

    li.appendChild(title);
    li.appendChild(desc);
    li.addEventListener("click", () => openProject(project));
    projectListEl.appendChild(li);
  });
}

newProjectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(dashboardError, "");
  const name = document.getElementById("project-name").value.trim();
  const description = document.getElementById("project-description").value.trim();
  try {
    await apiFetch("/projects", {
      method: "POST",
      body: JSON.stringify({ name, description: description || null }),
    });
    newProjectForm.reset();
    await loadDashboard();
  } catch (err) {
    if (err.status === 401) return handleAuthExpired();
    setError(dashboardError, err.message);
  }
});

// ---------- Project / chat view ----------
const projectTitleEl = document.getElementById("project-title");
const promptSetupEl = document.getElementById("prompt-setup");
const promptForm = document.getElementById("prompt-form");
const promptError = document.getElementById("prompt-error");
const chatAreaEl = document.getElementById("chat-area");
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send");
const chatError = document.getElementById("chat-error");
const backBtn = document.getElementById("back-btn");

backBtn.addEventListener("click", () => {
  state.currentProject = null;
  loadDashboard();
});

async function openProject(project) {
  state.currentProject = project;
  projectTitleEl.textContent = project.name;
  setError(promptError, "");
  setError(chatError, "");
  showView("project");

  try {
    const prompts = await apiFetch(`/projects/${project.id}/prompts`);
    if (prompts.length === 0) {
      promptSetupEl.classList.remove("hidden");
      chatAreaEl.classList.add("hidden");
    } else {
      promptSetupEl.classList.add("hidden");
      chatAreaEl.classList.remove("hidden");
      await loadMessages();
    }
  } catch (err) {
    if (err.status === 401) return handleAuthExpired();
    setError(chatError, err.message);
  }
}

promptForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(promptError, "");
  const content = document.getElementById("prompt-content").value.trim();
  try {
    await apiFetch(`/projects/${state.currentProject.id}/prompts`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    promptForm.reset();
    promptSetupEl.classList.add("hidden");
    chatAreaEl.classList.remove("hidden");
    await loadMessages();
  } catch (err) {
    if (err.status === 401) return handleAuthExpired();
    setError(promptError, err.message);
  }
});

async function loadMessages() {
  messagesEl.innerHTML = "";
  try {
    const messages = await apiFetch(`/projects/${state.currentProject.id}/chat`);
    messages.forEach(appendMessage);
    scrollMessagesToBottom();
  } catch (err) {
    if (err.status === 401) return handleAuthExpired();
    setError(chatError, err.message);
  }
}

function appendMessage(message) {
  const div = document.createElement("div");
  div.className = `msg ${message.role}`;
  div.textContent = message.content;
  messagesEl.appendChild(div);
  return div;
}

function scrollMessagesToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(chatError, "");
  const content = chatInput.value.trim();
  if (!content) return;

  appendMessage({ role: "user", content });
  chatInput.value = "";
  chatInput.disabled = true;
  chatSendBtn.disabled = true;

  const loadingEl = document.createElement("div");
  loadingEl.className = "msg assistant loading";
  loadingEl.textContent = "Thinking...";
  messagesEl.appendChild(loadingEl);
  scrollMessagesToBottom();

  try {
    const result = await apiFetch(`/projects/${state.currentProject.id}/chat`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    loadingEl.remove();
    const assistantMessage = result[result.length - 1];
    appendMessage(assistantMessage);
    scrollMessagesToBottom();
  } catch (err) {
    loadingEl.remove();
    if (err.status === 401) return handleAuthExpired();
    setError(chatError, err.message);
  } finally {
    chatInput.disabled = false;
    chatSendBtn.disabled = false;
    chatInput.focus();
  }
});

// ---------- Init ----------
setAuthMode("login");
if (state.token) {
  loadDashboard();
} else {
  showView("auth");
}
