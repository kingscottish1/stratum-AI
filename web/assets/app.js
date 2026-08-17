/* Stratum AI — frontend application (vanilla JS SPA, no build step) */
"use strict";

const API = "/api";
const TOKEN_KEY = "stratum_token";
const USER_KEY = "stratum_user";

const state = {
  token: localStorage.getItem(TOKEN_KEY) || "",
  user: JSON.parse(localStorage.getItem(USER_KEY) || "null"),
  system: null,
  clients: [],
};

// ---------------------------------------------------------------- helpers
async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const resp = await fetch(API + path, { ...opts, headers });
  if (resp.status === 401) { logout(); throw new Error("Session expired — sign in again"); }
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.detail || data.message || `HTTP ${resp.status}`);
  return data;
}

function toast(msg, kind = "") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${kind}`;
  setTimeout(() => el.classList.add("hidden"), 3200);
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function money(n) { return "$" + Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }); }

function badge(status) {
  const map = { ok: "ok", connected: "ok", live: "ok", paid: "ok", success: "ok", enabled: "ok",
    warn: "warn", pending: "warn", onboarding: "warn", error: "bad", bad: "bad", paused: "neutral",
    disabled: "neutral", new: "neutral", held: "warn" };
  return `<span class="badge ${map[status] || "neutral"}">${esc(status)}</span>`;
}

function navActive(name) {
  document.querySelectorAll("#nav a").forEach(a => a.classList.toggle("active", a.dataset.nav === name));
}

// ---------------------------------------------------------------- auth
function setSession(token, user) {
  state.token = token; state.user = user;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  document.getElementById("topbar").classList.remove("hidden");
  document.getElementById("foot").classList.remove("hidden");
  document.getElementById("who").innerHTML = `<b>${esc(user.name)}</b> · ${esc(user.role)} · <a href="#" onclick="logout();return false">sign out</a>`;
}

function logout() {
  state.token = ""; state.user = null;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  location.hash = "#/login";
}

function requireAuth() {
  if (!state.token) { location.hash = "#/login"; return false; }
  return true;
}

// ---------------------------------------------------------------- views
const views = {};

views.login = async (root) => {
  document.getElementById("topbar").classList.add("hidden");
  document.getElementById("foot").classList.add("hidden");
  root.innerHTML = `
  <div class="login-wrap">
    <h1>STRATUM <span style="color:var(--brand)">AI</span></h1>
    <p class="sub">Operations platform — Care · Realty · Freight</p>
    <div id="login-error"></div>
    <form id="login-form">
      <div class="field"><label>Email</label><input type="email" id="li-email" required></div>
      <div class="field"><label>Password</label><input type="password" id="li-password" required></div>
      <button type="submit" style="width:100%">Sign in</button>
    </form>
    <div class="hint">First run? Register the owner account: <a href="#/register">create account</a></div>
    <div class="hint" style="margin-top:8px">Built by <b>kingscottishDEV · N.A.S</b></div>
  </div>`;
  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const data = await api("/auth/login", { method: "POST", body: JSON.stringify({
        email: document.getElementById("li-email").value,
        password: document.getElementById("li-password").value }) });
      setSession(data.token, data.user);
      location.hash = "#/dashboard";
    } catch (err) {
      document.getElementById("login-error").innerHTML = `<div class="error">${esc(err.message)}</div>`;
    }
  });
};

views.register = async (root) => {
  document.getElementById("topbar").classList.add("hidden");
  document.getElementById("foot").classList.add("hidden");
  root.innerHTML = `
  <div class="login-wrap">
    <h1>Create account</h1>
    <p class="sub">The first account on a fresh install becomes the <b>owner</b>.</p>
    <div id="reg-error"></div>
    <form id="reg-form">
      <div class="field"><label>Name</label><input id="rg-name" required></div>
      <div class="field"><label>Email</label><input type="email" id="rg-email" required></div>
      <div class="field"><label>Password (min 8 chars)</label><input type="password" id="rg-password" minlength="8" required></div>
      <button type="submit" style="width:100%">Create account</button>
    </form>
    <div class="hint">Already have an account? <a href="#/login">Sign in</a></div>
  </div>`;
  document.getElementById("reg-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const data = await api("/auth/register", { method: "POST", body: JSON.stringify({
        name: document.getElementById("rg-name").value,
        email: document.getElementById("rg-email").value,
        password: document.getElementById("rg-password").value }) });
      setSession(data.token, data.user);
      location.hash = "#/dashboard";
    } catch (err) {
      document.getElementById("reg-error").innerHTML = `<div class="error">${esc(err.message)}</div>`;
    }
  });
};

views.dashboard = async (root) => {
  navActive("dashboard");
  const [status, clientsData] = await Promise.all([api("/system/status"), api("/clients")]);
  state.system = status.system; state.clients = clientsData.clients;
  const live = state.clients.filter(c => c.status === "live").length;
  root.innerHTML = `
  <h1>Dashboard</h1>
  <p class="sub">Stratum AI · ${esc(state.system.environment)} · LLM: ${esc(state.system.llm_provider)} (${esc(state.system.llm_model_fast)} / ${esc(state.system.llm_model_quality)})</p>
  <div class="cards">
    <div class="card"><div class="v">${state.clients.length}</div><div class="l">Client instances</div><div class="s">${live} live</div></div>
    <div class="card"><div class="v">${esc(state.system.environment)}</div><div class="l">Environment</div><div class="s">demo: ${state.system.demo_mode}</div></div>
    <div class="card"><div class="v">${state.system.llm_configured ? "Configured" : "Missing key"}</div><div class="l">BYO-LLM</div><div class="s">${esc(state.system.llm_provider)}</div></div>
    <div class="card"><div class="v">${state.system.db.ok ? "Connected" : "Error"}</div><div class="l">Database</div><div class="s">${esc(state.system.db)}</div></div>
  </div>
  <div class="panel">
    <div class="row" style="margin-bottom:12px"><h2 style="margin:0">Client instances</h2><span class="grow"></span>
      <a class="btn small" href="#/clients">Manage →</a></div>
    <table>
      <tr><th>ID</th><th>Name</th><th>Vertical</th><th>Status</th><th>Enabled</th><th>Created</th></tr>
      ${state.clients.map(c => `<tr class="clickable" onclick="location.hash='#/client/${c.id}'">
        <td>${c.id}</td><td><b>${esc(c.name)}</b></td><td>${esc(c.vertical)}</td>
        <td>${badge(c.status)}</td><td>${c.enabled ? "✅" : "⛔"}</td><td>${esc((c.created_at || "").slice(0, 10))}</td></tr>`).join("") || `<tr><td colspan="6" class="empty">No clients yet — <a href="#/clients">create one</a> or <a href="#" onclick="seedDemo();return false">load demo data</a></td></tr>`}
    </table>
  </div>`;
  window.seedDemo = async () => {
    try { await api("/demo/seed", { method: "POST" }); toast("Demo data loaded", "ok"); location.hash = "#/dashboard"; }
    catch (err) { toast(err.message, "bad"); }
  };
};

views.clients = async (root) => {
  navActive("clients");
  const data = await api("/clients");
  state.clients = data.clients;
  root.innerHTML = `
  <h1>Clients</h1>
  <p class="sub">Client instances — each with its own encrypted integrations, workflows, billing and audit trail.</p>
  <div class="panel">
    <h2>New client</h2>
    <form id="client-form" class="row">
      <div class="grow"><input id="c-name" placeholder="Client name" required></div>
      <select id="c-vertical" style="max-width:260px">
        <option value="medical_dental_clinics">Stratum Care — Medical/Dental</option>
        <option value="real_estate_brokerages">Stratum Realty — Real Estate</option>
        <option value="logistics_freight">Stratum Freight — Logistics</option>
      </select>
      <button type="submit">Create client</button>
    </form>
  </div>
  <div class="panel">
    <table>
      <tr><th>ID</th><th>Name</th><th>Vertical</th><th>Status</th><th>Enabled</th><th></th></tr>
      ${state.clients.map(c => `<tr>
        <td>${c.id}</td><td><b>${esc(c.name)}</b></td><td>${esc(c.vertical)}</td>
        <td>${badge(c.status)}</td><td>${c.enabled ? "✅" : "⛔"}</td>
        <td style="text-align:right"><a class="btn small secondary" href="#/client/${c.id}">Open</a></td></tr>`).join("") || `<tr><td colspan="6" class="empty">No clients yet.</td></tr>`}
    </table>
  </div>`;
  document.getElementById("client-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/clients", { method: "POST", body: JSON.stringify({
        name: document.getElementById("c-name").value,
        vertical: document.getElementById("c-vertical").value }) });
      toast("Client created", "ok"); location.hash = "#/clients";
    } catch (err) { toast(err.message, "bad"); }
  });
};

views.client = async (root, id) => {
  navActive("clients");
  const [clientData, integrations, workflows, billing, conversations, runs] = await Promise.all([
    api(`/clients/${id}`), api(`/clients/${id}/integrations`), api(`/clients/${id}/workflows`),
    api(`/clients/${id}/billing`), api(`/clients/${id}/conversations?limit=20`), api(`/clients/${id}/runs?limit=20`),
  ]);
  const c = clientData.client;
  root.innerHTML = `
  <div class="row" style="margin-bottom:4px">
    <h1 style="margin:0">${esc(c.name)}</h1><span class="grow"></span>${badge(c.status)}
  </div>
  <p class="sub">client #${c.id} · ${esc(c.vertical)} · created ${esc((c.created_at || "").slice(0, 10))} · ${c.enabled ? "enabled" : "disabled"}</p>
  <div class="tabs">
    <button data-tab="integrations" class="active">Integrations</button>
    <button data-tab="workflows">Workflows</button>
    <button data-tab="billing">Billing</button>
    <button data-tab="activity">Activity</button>
    <button data-tab="config">Config</button>
  </div>
  <div id="tab-content"></div>`;

  const tabs = {
    integrations: () => `
      <div class="panel">
        <h2>Connected systems</h2>
        <p class="sub">API keys are AES-256-GCM encrypted at rest — never stored or returned in plaintext.</p>
        <table>
          <tr><th>Name</th><th>Category</th><th>Base URL</th><th>Key</th><th></th></tr>
          ${integrations.integrations.map(i => `<tr>
            <td><b>${esc(i.name)}</b></td><td>${esc(i.category)}</td><td class="mono" style="font-size:12px">${esc(i.base_url || "—")}</td>
            <td>${i.has_key ? `<span class="badge ok">encrypted ✓</span>` : "—"}</td>
            <td style="text-align:right"><button class="btn small danger" onclick="delIntegration(${i.id})">Delete</button></td></tr>`).join("") || `<tr><td colspan="5" class="empty">No integrations configured.</td></tr>`}
        </table>
      </div>
      <div class="panel">
        <h2>Add integration</h2>
        <form id="int-form" class="grid2">
          <div class="field"><label>Name</label><input id="i-name" placeholder="e.g. twilio" required></div>
          <div class="field"><label>Category</label><input id="i-cat" placeholder="e.g. Channels"></div>
          <div class="field"><label>Base URL / from number</label><input id="i-url" placeholder="https://..."></div>
          <div class="field"><label>API key / secret <span style="color:var(--warn)">(encrypted at rest)</span></label><input id="i-key" type="password" required></div>
          <div style="grid-column:1/-1"><button type="submit">Save integration</button></div>
        </form>
      </div>`,
    workflows: () => `
      <div class="panel">
        <h2>Workflows</h2>
        ${workflows.workflows.map(w => `
          <div class="wf">
            <label class="switch"><input type="checkbox" ${w.enabled ? "checked" : ""} onchange="toggleWorkflow(${c.id},'${w.id}',this.checked)">
              <span class="slider"></span></label>
            <div class="meta"><b>${esc(w.name)}</b> <span class="badge ${w.enabled ? "ok" : "neutral"}">${esc(w.mode)}</span>
              <p>${esc(w.description)}</p></div>
            <select onchange="setMode(${c.id},'${w.id}',this.value)">
              <option value="auto" ${w.mode === "auto" ? "selected" : ""}>auto</option>
              <option value="auto-book" ${w.mode === "auto-book" ? "selected" : ""}>auto-book</option>
              <option value="confirm-first" ${w.mode === "confirm-first" ? "selected" : ""}>confirm-first</option>
            </select>
          </div>`).join("") || `<div class="empty">No workflows.</div>`}
      </div>`,
    billing: () => `
      <div class="panel">
        <h2>Billing records</h2>
        <table>
          <tr><th>Month</th><th>Platform</th><th>Add-ons</th><th>Total</th><th>Status</th></tr>
          ${billing.billing.map(b => `<tr><td><b>${esc(b.month)}</b></td><td>${money(b.platform)}</td><td>${money(b.addons)}</td><td><b>${money(b.total)}</b></td><td>${badge(b.status)}</td></tr>`).join("") || `<tr><td colspan="5" class="empty">No billing records.</td></tr>`}
        </table>
      </div>
      <div class="panel">
        <h2>Add record</h2>
        <form id="bill-form" class="row">
          <input id="b-month" placeholder="YYYY-MM" style="max-width:140px" required>
          <input id="b-platform" type="number" placeholder="Platform $" style="max-width:140px">
          <input id="b-addons" type="number" placeholder="Add-ons $" style="max-width:140px">
          <select id="b-status" style="max-width:140px"><option>pending</option><option>paid</option></select>
          <button type="submit">Add</button>
        </form>
      </div>`,
    activity: () => `
      <div class="panel"><h2>Agent runs</h2>
        <table><tr><th>Agent</th><th>Status</th><th>Latency</th><th>LLM</th><th>Cost</th><th>When</th></tr>
        ${runs.runs.map(r => `<tr><td>${esc(r.agent)}</td><td>${badge(r.status)}</td><td>${r.elapsed_ms} ms</td>
          <td class="mono" style="font-size:11px">${esc(r.llm_model || "—")}</td><td>$${Number(r.llm_cost_usd || 0).toFixed(5)}</td>
          <td>${esc((r.created_at || "").slice(0, 19))}</td></tr>`).join("") || `<tr><td colspan="6" class="empty">No runs yet — try the <a href="#/agents">Agents console</a>.</td></tr>`}</table>
      </div>
      <div class="panel"><h2>Conversations</h2>
        <table><tr><th>Role</th><th>Channel</th><th>Message</th><th>When</th></tr>
        ${conversations.conversations.map(x => `<tr><td>${badge(x.role === "assistant" ? "ok" : "neutral")} ${esc(x.role)}</td>
          <td>${esc(x.channel)}</td><td>${esc(x.content.slice(0, 140))}</td><td>${esc((x.created_at || "").slice(0, 19))}</td></tr>`).join("") || `<tr><td colspan="4" class="empty">No conversations.</td></tr>`}</table>
      </div>`,
    config: () => `
      <div class="panel"><h2>Configuration (non-sensitive)</h2>
        <div class="kv">${Object.entries(c.config_json || {}).map(([k, v]) => `<b>${esc(k)}</b><span>${esc(JSON.stringify(v))}</span>`).join("") || `<span>Empty config.</span>`}</div>
        <div style="margin-top:16px"><button class="btn secondary small" onclick="editConfig(${c.id})">Edit config (JSON)</button>
        <button class="btn danger small" onclick="delClient(${c.id})">Delete client</button></div>
      </div>`,
  };

  function renderTab(name) {
    document.querySelectorAll(".tabs button").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
    document.getElementById("tab-content").innerHTML = tabs[name]();
    bindForms();
  }
  function bindForms() {
    const intForm = document.getElementById("int-form");
    if (intForm) intForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        await api(`/clients/${c.id}/integrations`, { method: "POST", body: JSON.stringify({
          name: document.getElementById("i-name").value, category: document.getElementById("i-cat").value,
          base_url: document.getElementById("i-url").value, api_key: document.getElementById("i-key").value }) });
        toast("Integration saved (encrypted)", "ok"); renderTab("integrations");
      } catch (err) { toast(err.message, "bad"); }
    });
    const billForm = document.getElementById("bill-form");
    if (billForm) billForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        await api(`/clients/${c.id}/billing`, { method: "POST", body: JSON.stringify({
          month: document.getElementById("b-month").value,
          platform: Number(document.getElementById("b-platform").value || 0),
          addons: Number(document.getElementById("b-addons").value || 0),
          status: document.getElementById("b-status").value }) });
        toast("Billing record added", "ok"); renderTab("billing");
      } catch (err) { toast(err.message, "bad"); }
    });
  }
  document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => renderTab(b.dataset.tab)));
  renderTab("integrations");

  window.delIntegration = async (iid) => {
    if (!confirm("Delete this integration and its encrypted secret?")) return;
    try { await api(`/clients/${c.id}/integrations/${iid}`, { method: "DELETE" }); toast("Deleted", "ok"); renderTab("integrations"); }
    catch (err) { toast(err.message, "bad"); }
  };
  window.toggleWorkflow = async (cid, wid, on) => {
    try { await api(`/clients/${cid}/workflows/${wid}`, { method: "PATCH", body: JSON.stringify({ enabled: on }) }); toast("Workflow " + (on ? "enabled" : "disabled"), "ok"); }
    catch (err) { toast(err.message, "bad"); }
  };
  window.setMode = async (cid, wid, mode) => {
    try { await api(`/clients/${cid}/workflows/${wid}`, { method: "PATCH", body: JSON.stringify({ mode }) }); toast("Mode → " + mode, "ok"); }
    catch (err) { toast(err.message, "bad"); }
  };
  window.editConfig = async (cid) => {
    const raw = prompt("config_json (JSON):", JSON.stringify(c.config_json || {}));
    if (!raw) return;
    try { await api(`/clients/${cid}`, { method: "PATCH", body: JSON.stringify({ config_json: JSON.parse(raw) }) }); toast("Config saved", "ok"); location.hash = "#/client/" + cid; }
    catch (err) { toast(err.message, "bad"); }
  };
  window.delClient = async (cid) => {
    if (!confirm("Permanently delete this client and all its data?")) return;
    try { await api(`/clients/${cid}`, { method: "DELETE" }); toast("Client deleted", "ok"); location.hash = "#/clients"; }
    catch (err) { toast(err.message, "bad"); }
  };
};

views.agents = async (root) => {
  navActive("agents");
  if (!state.clients.length) { const d = await api("/clients"); state.clients = d.clients; }
  root.innerHTML = `
  <h1>Agents console</h1>
  <p class="sub">Send a message to a client's agent suite and watch it run. ${state.system && state.system.demo_mode ? "<b>Demo mode: mock connectors.</b>" : "Production mode: real connectors from encrypted credentials."}</p>
  <div class="grid2">
    <div class="panel">
      <h2>1 · Pick client &amp; agent</h2>
      <div class="field"><label>Client</label><select id="ag-client">${state.clients.map(c => `<option value="${c.id}">${esc(c.name)} (${esc(c.vertical)})</option>`).join("")}</select></div>
      <div class="field"><label>Agent</label><select id="ag-agent"><option>— select client first —</option></select></div>
      <div class="field"><label>Message</label><textarea id="ag-message" rows="4" placeholder='e.g. "Hi! Can I book a cleaning this week?"'></textarea></div>
      <button id="ag-run">Run agent →</button>
    </div>
    <div class="panel">
      <h2>2 · Result</h2>
      <div id="ag-result" class="empty">Waiting…</div>
    </div>
  </div>`;
  const loadAgents = async () => {
    const cid = document.getElementById("ag-client").value;
    const data = await api(`/clients/${cid}/agents`);
    document.getElementById("ag-agent").innerHTML = data.agents.map(a => `<option>${esc(a)}</option>`).join("");
  };
  document.getElementById("ag-client").addEventListener("change", loadAgents);
  if (state.clients.length) loadAgents();
  document.getElementById("ag-run").addEventListener("click", async () => {
    const out = document.getElementById("ag-result");
    out.className = "empty"; out.textContent = "Running…";
    try {
      const res = await api(`/clients/${document.getElementById("ag-client").value}/agents/${document.getElementById("ag-agent").value}/run`, {
        method: "POST", body: JSON.stringify({ message: document.getElementById("ag-message").value }) });
      out.className = "";
      out.innerHTML = `<div class="mono">${esc(JSON.stringify(res, null, 2))}</div>`;
    } catch (err) { out.className = ""; out.innerHTML = `<div class="error">${esc(err.message)}</div>`; }
  });
};

views.audit = async (root) => {
  navActive("audit");
  const data = await api("/audit?limit=300");
  root.innerHTML = `
  <h1>Audit log</h1>
  <p class="sub">Every sensitive action — logins, secret changes, billing, deletions — recorded immutably.</p>
  <div class="panel">
    <table>
      <tr><th>When</th><th>User</th><th>Client</th><th>Action</th><th>Resource</th><th>Detail</th></tr>
      ${data.audit.map(a => `<tr><td class="mono" style="font-size:11px">${esc((a.created_at || "").slice(0, 19))}</td>
        <td>${esc(a.user_email)}</td><td>${a.client_id ?? "—"}</td>
        <td><span class="badge neutral">${esc(a.action)}</span></td><td>${esc(a.resource)}</td>
        <td style="max-width:340px">${esc(a.detail.slice(0, 120))}</td></tr>`).join("") || `<tr><td colspan="6" class="empty">No audit events yet.</td></tr>`}
    </table>
  </div>`;
};

views.settings = async (root) => {
  navActive("settings");
  const [status, users] = await Promise.all([api("/system/status"), api("/users")]);
  const s = status.system;
  root.innerHTML = `
  <h1>Settings</h1>
  <p class="sub">System configuration — all values come from your environment / secret store. Nothing is hardcoded.</p>
  <div class="grid2">
    <div class="panel">
      <h2>System status</h2>
      <div class="kv">
        <b>Environment</b><span>${esc(s.environment)}</span>
        <b>Demo mode</b><span>${s.demo_mode ? `<span class="badge warn">ON — testing only</span>` : `<span class="badge ok">OFF — production</span>`}</span>
        <b>LLM provider</b><span>${esc(s.llm_provider)}</span>
        <b>Fast model</b><span class="mono">${esc(s.llm_model_fast)}</span>
        <b>Quality model</b><span class="mono">${esc(s.llm_model_quality)}</span>
        <b>LLM configured</b><span>${s.llm_configured ? `<span class="badge ok">yes</span>` : `<span class="badge bad">missing API key</span>`}</span>
        <b>Fallback provider</b><span>${esc(s.llm_fallback_provider || "—")}</span>
        <b>Database</b><span>${esc(s.db)}</span>
      </div>
      ${status.llm_error ? `<div class="error" style="margin-top:12px">LLM: ${esc(status.llm_error)}</div>` : ""}
      <p class="sub" style="margin-top:14px">Bring your own LLM: set <span class="mono">LLM_PROVIDER</span>, <span class="mono">LLM_API_KEY</span>, <span class="mono">LLM_MODEL_FAST</span>, <span class="mono">LLM_MODEL_QUALITY</span> in <span class="mono">.env</span> — supported: openai, anthropic, azure, openrouter, groq, together, ollama, openai_compatible. Restart to apply.</p>
    </div>
    <div class="panel">
      <h2>Team</h2>
      <table>
        <tr><th>Name</th><th>Email</th><th>Role</th><th>Active</th></tr>
        ${users.users.map(u => `<tr><td><b>${esc(u.name)}</b></td><td>${esc(u.email)}</td><td>${badge(u.role === "owner" ? "ok" : "neutral")} ${esc(u.role)}</td><td>${u.is_active ? "✅" : "⛔"}</td></tr>`).join("")}
      </table>
      <p class="sub" style="margin-top:12px">Built by <b>kingscottishDEV · N.A.S</b> · Stratum AI v1.0.0</p>
    </div>
  </div>`;
};

// ---------------------------------------------------------------- router
async function router() {
  const root = document.getElementById("view");
  const hash = location.hash || "#/dashboard";
  if (!state.token && !hash.startsWith("#/login") && !hash.startsWith("#/register")) { location.hash = "#/login"; return; }
  try {
    if (hash === "#/login") return views.login(root);
    if (hash === "#/register") return views.register(root);
    if (!requireAuth()) return;
    const parts = hash.split("/");
    if (hash === "#/dashboard") return views.dashboard(root);
    if (hash === "#/clients") return views.clients(root);
    if (parts[1] === "client") return views.client(root, Number(parts[2]));
    if (hash === "#/agents") return views.agents(root);
    if (hash === "#/audit") return views.audit(root);
    if (hash === "#/settings") return views.settings(root);
    root.innerHTML = `<div class="panel"><h1>404</h1><p class="sub">Page not found.</p></div>`;
  } catch (err) {
    if (err.message.includes("Session")) { location.hash = "#/login"; return; }
    root.innerHTML = `<div class="panel"><div class="error">${esc(err.message)}</div></div>`;
  }
}

window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", async () => {
  // preload system status for the demo banner
  if (state.token) {
    try { const s = await api("/system/status"); state.system = s.system; } catch (e) { /* ignore */ }
  }
  const banner = document.getElementById("demo-banner");
  if (state.system && state.system.demo_mode) banner.classList.remove("hidden");
  router();
});

