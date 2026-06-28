from __future__ import annotations


def render_chat_ui() -> str:
    return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RAG System</title>
    <style>
      :root {
        --bg: #f6f1e8;
        --panel: rgba(255, 252, 247, 0.88);
        --panel-strong: #fffaf1;
        --line: #d8c6ad;
        --text: #2f2418;
        --muted: #74624e;
        --accent: #0f766e;
        --accent-dark: #134e4a;
        --warm: #b45309;
        --shadow: 0 22px 60px rgba(63, 41, 19, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Instrument Sans", "Segoe UI", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 28%),
          radial-gradient(circle at top right, rgba(180, 83, 9, 0.16), transparent 24%),
          linear-gradient(180deg, #fbf7f1 0%, var(--bg) 42%, #efe3d0 100%);
      }

      .shell {
        width: min(1180px, calc(100vw - 32px));
        margin: 32px auto;
        display: grid;
        grid-template-columns: 360px minmax(0, 1fr);
        gap: 22px;
      }

      .panel {
        background: var(--panel);
        border: 1px solid rgba(216, 198, 173, 0.75);
        border-radius: 24px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
      }

      .sidebar {
        padding: 26px;
        position: sticky;
        top: 24px;
        height: fit-content;
      }

      .kicker {
        font-size: 12px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--warm);
        margin: 0 0 10px;
      }

      h1 {
        margin: 0;
        font-family: "Iowan Old Style", "Palatino Linotype", serif;
        font-size: clamp(2.1rem, 3vw, 3.2rem);
        line-height: 0.95;
      }

      .lede {
        margin: 16px 0 0;
        color: var(--muted);
        line-height: 1.6;
      }

      .card-list {
        display: grid;
        gap: 14px;
        margin-top: 24px;
      }

      .mini-card {
        padding: 16px;
        border-radius: 18px;
        background: rgba(255, 250, 241, 0.92);
        border: 1px solid rgba(216, 198, 173, 0.72);
      }

      .mini-card strong {
        display: block;
        margin-bottom: 8px;
        font-size: 0.95rem;
      }

      .mini-card p {
        margin: 0;
        font-size: 0.95rem;
        color: var(--muted);
        line-height: 1.5;
      }

      .workspace {
        padding: 24px;
        display: grid;
        gap: 18px;
      }

      .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        padding: 6px 6px 0;
      }

      .toolbar-stack {
        display: grid;
        gap: 8px;
      }

      .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(15, 118, 110, 0.09);
        color: var(--accent-dark);
        font-size: 0.92rem;
      }

      .status-badge[data-state="degraded"] {
        background: rgba(180, 83, 9, 0.12);
        color: #92400e;
      }

      .status-badge[data-state="checking"] {
        background: rgba(116, 98, 78, 0.12);
        color: var(--muted);
      }

      .status-dot {
        width: 9px;
        height: 9px;
        border-radius: 999px;
        background: var(--accent);
      }

      .status-badge[data-state="degraded"] .status-dot {
        background: var(--warm);
      }

      .status-badge[data-state="checking"] .status-dot {
        background: var(--line);
      }

      .readiness-note {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.5;
      }

      .request-id {
        color: var(--muted);
        font-size: 0.92rem;
        padding-top: 10px;
      }

      .session-bar {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(0, 1fr) auto auto;
        gap: 12px;
        align-items: end;
        padding: 18px 24px 0;
      }

      .session-field[hidden] {
        display: none;
      }

      .composer {
        display: grid;
        gap: 16px;
        padding: 24px;
        border-radius: 22px;
        background: var(--panel-strong);
        border: 1px solid rgba(216, 198, 173, 0.75);
      }

      label {
        display: block;
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 8px;
      }

      textarea,
      input,
      select {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        font: inherit;
        color: var(--text);
        background: rgba(255, 255, 255, 0.86);
      }

      textarea {
        min-height: 160px;
        resize: vertical;
      }

      .field-grid {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 14px;
      }

      .actions {
        display: flex;
        align-items: center;
        gap: 14px;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 14px 22px;
        font: inherit;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
        cursor: pointer;
        box-shadow: 0 14px 30px rgba(15, 118, 110, 0.22);
      }

      button:disabled {
        opacity: 0.6;
        cursor: progress;
      }

      .hint {
        color: var(--muted);
        font-size: 0.92rem;
      }

      .session-state {
        color: var(--muted);
        font-size: 0.92rem;
        padding-bottom: 4px;
      }

      .result-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
        gap: 18px;
      }

      .result-card,
      .sources-card,
      .history-card {
        padding: 22px;
        border-radius: 22px;
        border: 1px solid rgba(216, 198, 173, 0.75);
        background: rgba(255, 250, 241, 0.92);
      }

      .section-title {
        margin: 0 0 14px;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--warm);
      }

      .answer {
        margin: 0;
        white-space: pre-wrap;
        line-height: 1.7;
      }

      .answer-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 18px;
      }

      .meta-pill {
        display: inline-flex;
        gap: 6px;
        align-items: center;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(15, 118, 110, 0.08);
        color: var(--accent-dark);
        font-size: 0.9rem;
      }

      .meta-pill strong {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }

      .sources {
        display: grid;
        gap: 12px;
      }

      .source-pill {
        padding: 14px;
        border-radius: 16px;
        background: white;
        border: 1px solid rgba(216, 198, 173, 0.82);
      }

      .source-pill strong {
        display: block;
        margin-bottom: 6px;
      }

      .source-pill span {
        color: var(--muted);
        font-size: 0.92rem;
      }

      .empty {
        color: var(--muted);
        line-height: 1.6;
      }

      .error {
        padding: 14px 16px;
        border-radius: 16px;
        background: rgba(190, 24, 93, 0.08);
        border: 1px solid rgba(190, 24, 93, 0.18);
        color: #9f1239;
      }

      .history-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 16px;
      }

      .history-subtitle {
        margin: 0;
        color: var(--muted);
        line-height: 1.5;
      }

      .history-list {
        display: grid;
        gap: 12px;
      }

      .history-item {
        width: 100%;
        padding: 16px 18px;
        border-radius: 18px;
        border: 1px solid rgba(216, 198, 173, 0.82);
        background: white;
        box-shadow: none;
        color: var(--text);
        display: grid;
        gap: 8px;
        text-align: left;
      }

      .history-item:hover {
        transform: translateY(-1px);
      }

      .history-item strong {
        display: block;
        font-size: 1rem;
      }

      .history-preview {
        color: var(--muted);
        line-height: 1.5;
      }

      .history-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        color: var(--muted);
        font-size: 0.9rem;
      }

      .ghost-button {
        background: transparent;
        color: var(--accent-dark);
        border: 1px solid rgba(15, 118, 110, 0.18);
        box-shadow: none;
      }

      @media (max-width: 940px) {
        .shell {
          grid-template-columns: 1fr;
        }

        .sidebar {
          position: static;
        }

        .result-grid,
        .field-grid,
        .session-bar {
          grid-template-columns: 1fr;
        }

        .history-header {
          flex-direction: column;
        }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="panel sidebar">
        <p class="kicker">Internal Knowledge</p>
        <h1>Ask your docs, not your memory.</h1>
        <p class="lede">
          This UI uses the same RAG pipeline as the API: retrieve grounded
          context from Elasticsearch, then generate an answer with OpenAI.
        </p>
        <div class="card-list">
          <article class="mini-card">
            <strong>How it works</strong>
            <p>
              Your question is matched against indexed chunks, then the best
              context is passed to the model for a grounded response.
            </p>
          </article>
          <article class="mini-card">
            <strong>What you get</strong>
            <p>
              A concise answer, the model used, the request id, and source
              references for fast follow-up.
            </p>
          </article>
          <article class="mini-card">
            <strong>Auth</strong>
            <p>
              If auth is enabled, sign in below with the deployment's configured
              login method before sending your request.
            </p>
          </article>
        </div>
      </section>

      <section class="panel workspace">
        <div class="toolbar">
          <div class="toolbar-stack">
            <div class="status-badge" id="readiness-badge" data-state="checking">
              <span class="status-dot"></span>
              <span id="readiness-label">Checking deployment readiness...</span>
            </div>
            <div class="readiness-note" id="readiness-note">
              Verifying Elasticsearch, OpenAI, and auth configuration.
            </div>
          </div>
          <div class="request-id" id="request-id">Request ID: waiting</div>
        </div>

        <div class="session-bar">
          <div class="session-field" id="username-field" hidden>
            <label for="username">Username</label>
            <input id="username" type="text" placeholder="Enter your session username" />
          </div>
          <div class="session-field" id="password-field" hidden>
            <label for="password">Password</label>
            <input id="password" type="password" placeholder="Enter your session password" />
          </div>
          <div class="session-field" id="token-field">
            <label for="token">API Token</label>
            <input id="token" type="password" placeholder="Login once if token-based session auth is enabled" />
          </div>
          <div class="session-state" id="session-state">Auth status: checking…</div>
          <button id="login" type="button">Sign In</button>
          <button id="logout" type="button">Sign Out</button>
        </div>

        <section class="composer">
          <div>
            <label for="question">Question</label>
            <textarea id="question" placeholder="Ask something like: How does RAG reduce hallucinations?"></textarea>
          </div>

          <div class="field-grid">
            <div>
              <label for="top-k">Top K</label>
              <select id="top-k">
                <option value="2">2 chunks</option>
                <option value="3" selected>3 chunks</option>
                <option value="5">5 chunks</option>
                <option value="8">8 chunks</option>
              </select>
            </div>
            <div class="hint" id="auth-hint">
              Use the sign-in controls above if the API is protected. Once the
              session cookie is set, the browser UI can call <code>/ask</code>
              directly.
            </div>
          </div>

          <div class="actions">
            <button id="submit">Ask the RAG System</button>
            <span class="hint">This sends a POST request to <code>/ask</code>.</span>
          </div>

          <div id="error" class="error" hidden></div>
        </section>

        <section class="result-grid">
          <article class="result-card">
            <p class="section-title">Answer</p>
            <div id="answer-meta" class="answer-meta">
              <div class="empty">Model and retrieval details will appear here.</div>
            </div>
            <p id="answer" class="empty">
              Your grounded answer will appear here once you submit a question.
            </p>
          </article>

          <article class="sources-card">
            <p class="section-title">Sources</p>
            <div id="sources" class="sources">
              <div class="empty">Source references will appear here.</div>
            </div>
          </article>
        </section>

        <section class="history-card">
          <div class="history-header">
            <div>
              <p class="section-title">Recent Questions</p>
              <p class="history-subtitle">
                Saved in this browser so you can reopen past answers and reuse
                good prompts quickly.
              </p>
            </div>
            <button id="clear-history" type="button" class="ghost-button">Clear History</button>
          </div>
          <div id="history" class="history-list">
            <div class="empty">Questions you answer here will appear in this history.</div>
          </div>
        </section>
      </section>
    </main>

    <script>
      const HISTORY_STORAGE_KEY = "rag-system-history";
      const MAX_HISTORY_ITEMS = 8;
      const questionEl = document.getElementById("question");
      const tokenEl = document.getElementById("token");
      const usernameEl = document.getElementById("username");
      const passwordEl = document.getElementById("password");
      const topKEl = document.getElementById("top-k");
      const submitEl = document.getElementById("submit");
      const loginEl = document.getElementById("login");
      const logoutEl = document.getElementById("logout");
      const sessionStateEl = document.getElementById("session-state");
      const usernameFieldEl = document.getElementById("username-field");
      const passwordFieldEl = document.getElementById("password-field");
      const tokenFieldEl = document.getElementById("token-field");
      const readinessBadgeEl = document.getElementById("readiness-badge");
      const readinessLabelEl = document.getElementById("readiness-label");
      const readinessNoteEl = document.getElementById("readiness-note");
      const authHintEl = document.getElementById("auth-hint");
      const answerMetaEl = document.getElementById("answer-meta");
      const answerEl = document.getElementById("answer");
      const sourcesEl = document.getElementById("sources");
      const historyEl = document.getElementById("history");
      const clearHistoryEl = document.getElementById("clear-history");
      const errorEl = document.getElementById("error");
      const requestIdEl = document.getElementById("request-id");
      let historyItems = [];
      let authState = {
        auth_enabled: false,
        authenticated: false,
        session_login_enabled: false,
        token_login_enabled: false
      };

      function createEmptyState(message) {
        const emptyEl = document.createElement("div");
        emptyEl.className = "empty";
        emptyEl.textContent = message;
        return emptyEl;
      }

      function createMetaPill(label, value) {
        const pillEl = document.createElement("div");
        pillEl.className = "meta-pill";

        const labelEl = document.createElement("strong");
        labelEl.textContent = label;

        const valueEl = document.createElement("span");
        valueEl.textContent = value;

        pillEl.append(labelEl, valueEl);
        return pillEl;
      }

      function renderAnswerMeta(payload) {
        answerMetaEl.replaceChildren();

        if (!payload) {
          answerMetaEl.append(createEmptyState("Model and retrieval details will appear here."));
          return;
        }

        answerMetaEl.append(
          createMetaPill("Model", payload.model || "unknown"),
          createMetaPill("Chunks", String(payload.retrieved_chunk_count ?? 0)),
          createMetaPill("Sources", String((payload.sources || []).length)),
          createMetaPill("Response ID", payload.response_id || "n/a")
        );
      }

      function renderSources(sources) {
        sourcesEl.replaceChildren();

        if (!sources.length) {
          sourcesEl.append(createEmptyState("No sources returned."));
          return;
        }

        sources.forEach((source) => {
          const articleEl = document.createElement("article");
          articleEl.className = "source-pill";

          const titleEl = document.createElement("strong");
          titleEl.textContent = source.source || "unknown source";

          const metaEl = document.createElement("span");
          metaEl.textContent = `id=${source.id || "n/a"} | chunk=${source.chunk_index ?? "n/a"} | score=${source.score ?? "n/a"}`;

          articleEl.append(titleEl, metaEl);
          sourcesEl.append(articleEl);
        });
      }

      function renderResult(payload, requestId) {
        answerEl.textContent = payload.answer;
        answerEl.className = "answer";
        renderAnswerMeta(payload);
        renderSources(payload.sources || []);

        if (requestId) {
          requestIdEl.textContent = `Request ID: ${requestId}`;
        }
      }

      function loadHistory() {
        try {
          const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
          if (!raw) {
            return [];
          }

          const parsed = JSON.parse(raw);
          return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
          return [];
        }
      }

      function persistHistory() {
        try {
          window.localStorage.setItem(
            HISTORY_STORAGE_KEY,
            JSON.stringify(historyItems.slice(0, MAX_HISTORY_ITEMS))
          );
        } catch (error) {
          // Ignore storage failures and keep the current page functional.
        }
      }

      function formatSavedAt(savedAt) {
        if (!savedAt) {
          return "saved recently";
        }

        try {
          return new Intl.DateTimeFormat(undefined, {
            dateStyle: "medium",
            timeStyle: "short"
          }).format(new Date(savedAt));
        } catch (error) {
          return savedAt;
        }
      }

      function renderHistory() {
        historyEl.replaceChildren();
        clearHistoryEl.disabled = historyItems.length === 0;

        if (!historyItems.length) {
          historyEl.append(
            createEmptyState("Questions you answer here will appear in this history.")
          );
          return;
        }

        historyItems.forEach((item, index) => {
          const buttonEl = document.createElement("button");
          buttonEl.type = "button";
          buttonEl.className = "history-item";
          buttonEl.addEventListener("click", () => {
            questionEl.value = item.question || "";
            topKEl.value = String(item.top_k || 3);
            renderResult(item, item.request_id || "history");
          });

          const titleEl = document.createElement("strong");
          titleEl.textContent = item.question || "Untitled question";

          const previewEl = document.createElement("div");
          previewEl.className = "history-preview";
          previewEl.textContent = item.answer || "No answer saved.";

          const metaEl = document.createElement("div");
          metaEl.className = "history-meta";
          metaEl.textContent = `${formatSavedAt(item.saved_at)} | model ${item.model || "unknown"} | ${item.retrieved_chunk_count ?? 0} chunks | ${(item.sources || []).length} sources`;

          buttonEl.append(titleEl, previewEl, metaEl);
          historyEl.append(buttonEl);
        });
      }

      function storeHistoryEntry(payload, requestId) {
        const entry = {
          question: payload.question,
          answer: payload.answer,
          sources: payload.sources || [],
          model: payload.model || "unknown",
          response_id: payload.response_id || null,
          retrieved_chunk_count: payload.retrieved_chunk_count ?? 0,
          top_k: Number(topKEl.value),
          request_id: requestId || "missing",
          saved_at: new Date().toISOString()
        };

        historyItems = [
          entry,
          ...historyItems.filter((item) => {
            return !(
              item.question === entry.question &&
              item.answer === entry.answer &&
              item.request_id === entry.request_id
            );
          })
        ].slice(0, MAX_HISTORY_ITEMS);

        persistHistory();
        renderHistory();
      }

      function summarizeReadinessChecks(checks) {
        const failingChecks = Object.entries(checks || {}).filter(([, check]) => {
          return check.status !== "ok";
        });

        if (!failingChecks.length) {
          return "Elasticsearch, OpenAI, and auth configuration are ready.";
        }

        return failingChecks
          .map(([name, check]) => `${name}: ${check.detail}`)
          .join(" | ");
      }

      async function refreshReadiness() {
        readinessBadgeEl.dataset.state = "checking";
        readinessLabelEl.textContent = "Checking deployment readiness...";
        readinessNoteEl.textContent = "Verifying Elasticsearch, OpenAI, and auth configuration.";

        const response = await fetch("/ready");
        const payload = await response.json();
        const requestId = response.headers.get("X-Request-ID") || "missing";
        requestIdEl.textContent = `Request ID: ${requestId}`;

        if (payload.status === "ready") {
          readinessBadgeEl.dataset.state = "ready";
          readinessLabelEl.textContent = "Deployment ready for questions";
        } else {
          readinessBadgeEl.dataset.state = "degraded";
          readinessLabelEl.textContent = "Deployment needs setup";
        }

        readinessNoteEl.textContent = summarizeReadinessChecks(payload.checks);
        return payload;
      }

      function applyAuthState(payload) {
        authState = payload;
        const useSessionCredentials = payload.session_login_enabled;
        const authEnabled = payload.auth_enabled;

        usernameFieldEl.hidden = !authEnabled || !useSessionCredentials;
        passwordFieldEl.hidden = !authEnabled || !useSessionCredentials;
        tokenFieldEl.hidden = !authEnabled || useSessionCredentials;
        loginEl.hidden = !authEnabled;
        logoutEl.hidden = !authEnabled;

        if (!authEnabled) {
          sessionStateEl.textContent = "Auth status: token not required";
          authHintEl.innerHTML = "Auth is disabled for this deployment. The browser can call <code>/ask</code> directly.";
          return;
        }

        if (useSessionCredentials) {
          authHintEl.innerHTML = "This deployment expects a dedicated username and password before the browser can call <code>/ask</code> directly.";
        } else {
          authHintEl.innerHTML = "This deployment uses a shared API token for browser sign-in. Once the session cookie is set, the browser UI can call <code>/ask</code> directly.";
        }

        sessionStateEl.textContent = payload.authenticated
          ? "Auth status: signed in"
          : "Auth status: sign in required";
      }

      async function refreshAuthStatus() {
        const response = await fetch("/auth/status");
        const payload = await response.json();
        const requestId = response.headers.get("X-Request-ID") || "missing";
        requestIdEl.textContent = `Request ID: ${requestId}`;
        applyAuthState(payload);
        return payload;
      }

      async function login() {
        let body;

        if (authState.session_login_enabled) {
          const username = usernameEl.value.trim();
          const password = passwordEl.value;

          if (!username || !password) {
            errorEl.textContent = "Enter your username and password before signing in.";
            errorEl.hidden = false;
            return;
          }

          body = { username, password };
        } else {
          const token = tokenEl.value.trim();
          if (!token) {
            errorEl.textContent = "Enter the API token before signing in.";
            errorEl.hidden = false;
            return;
          }

          body = { token };
        }

        errorEl.hidden = true;

        try {
          const response = await fetch("/session", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
          });

          const payload = await response.json();
          const requestId = response.headers.get("X-Request-ID") || "missing";
          requestIdEl.textContent = `Request ID: ${requestId}`;

          if (!response.ok) {
            throw new Error(payload.detail || "Sign-in failed.");
          }

          tokenEl.value = "";
          usernameEl.value = "";
          passwordEl.value = "";
          await refreshAuthStatus();
        } catch (error) {
          errorEl.textContent = error.message;
          errorEl.hidden = false;
        }
      }

      async function logout() {
        errorEl.hidden = true;
        await fetch("/session", { method: "DELETE" });
        await refreshAuthStatus();
      }

      async function askQuestion() {
        const question = questionEl.value.trim();
        if (!question) {
          errorEl.textContent = "Enter a question before sending the request.";
          errorEl.hidden = false;
          return;
        }

        errorEl.hidden = true;
        submitEl.disabled = true;
        submitEl.textContent = "Working...";
        answerEl.textContent = "Fetching answer...";
        answerEl.className = "answer";
        renderAnswerMeta(null);
        sourcesEl.replaceChildren(createEmptyState("Loading sources..."));

        try {
          const response = await fetch("/ask", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              question,
              top_k: Number(topKEl.value)
            })
          });

          const requestId = response.headers.get("X-Request-ID") || "missing";
          requestIdEl.textContent = `Request ID: ${requestId}`;

          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.detail || "Request failed.");
          }

          renderResult(payload, requestId);
          storeHistoryEntry(payload, requestId);
        } catch (error) {
          answerEl.textContent = "No answer available.";
          answerEl.className = "empty";
          renderAnswerMeta(null);
          sourcesEl.replaceChildren(createEmptyState("No sources available."));
          errorEl.textContent = error.message;
          errorEl.hidden = false;
        } finally {
          submitEl.disabled = false;
          submitEl.textContent = "Ask the RAG System";
        }
      }

      clearHistoryEl.addEventListener("click", () => {
        historyItems = [];
        persistHistory();
        renderHistory();
      });
      submitEl.addEventListener("click", askQuestion);
      loginEl.addEventListener("click", login);
      logoutEl.addEventListener("click", logout);
      questionEl.addEventListener("keydown", (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          askQuestion();
        }
      });

      historyItems = loadHistory().slice(0, MAX_HISTORY_ITEMS);
      renderHistory();
      renderAnswerMeta(null);
      refreshReadiness().catch(() => {
        readinessBadgeEl.dataset.state = "degraded";
        readinessLabelEl.textContent = "Readiness check unavailable";
        readinessNoteEl.textContent = "The browser could not load /ready.";
      });
      refreshAuthStatus().catch(() => {
        sessionStateEl.textContent = "Auth status: unavailable";
      });
    </script>
  </body>
</html>
"""
