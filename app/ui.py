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
        align-items: center;
        gap: 16px;
        padding: 6px 6px 0;
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

      .status-dot {
        width: 9px;
        height: 9px;
        border-radius: 999px;
        background: var(--accent);
      }

      .request-id {
        color: var(--muted);
        font-size: 0.92rem;
      }

      .session-bar {
        display: grid;
        grid-template-columns: 1.1fr 1fr auto auto;
        gap: 12px;
        align-items: end;
        padding: 18px 24px 0;
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
      .sources-card {
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
              If API token auth is enabled, paste the bearer token below before
              sending your request.
            </p>
          </article>
        </div>
      </section>

      <section class="panel workspace">
        <div class="toolbar">
          <div class="status-badge">
            <span class="status-dot"></span>
            <span>Connected to the local RAG API</span>
          </div>
          <div class="request-id" id="request-id">Request ID: waiting</div>
        </div>

        <div class="session-bar">
          <div>
            <label for="token">API Token</label>
            <input id="token" type="password" placeholder="Login once if session auth is enabled" />
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
            <div class="hint">
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
      </section>
    </main>

    <script>
      const questionEl = document.getElementById("question");
      const tokenEl = document.getElementById("token");
      const topKEl = document.getElementById("top-k");
      const submitEl = document.getElementById("submit");
      const loginEl = document.getElementById("login");
      const logoutEl = document.getElementById("logout");
      const sessionStateEl = document.getElementById("session-state");
      const answerEl = document.getElementById("answer");
      const sourcesEl = document.getElementById("sources");
      const errorEl = document.getElementById("error");
      const requestIdEl = document.getElementById("request-id");

      async function refreshAuthStatus() {
        const response = await fetch("/auth/status");
        const payload = await response.json();
        const requestId = response.headers.get("X-Request-ID") || "missing";
        requestIdEl.textContent = `Request ID: ${requestId}`;

        if (!payload.auth_enabled) {
          sessionStateEl.textContent = "Auth status: token not required";
          return payload;
        }

        sessionStateEl.textContent = payload.authenticated
          ? "Auth status: signed in"
          : "Auth status: sign in required";
        return payload;
      }

      async function login() {
        const token = tokenEl.value.trim();
        if (!token) {
          errorEl.textContent = "Enter the API token before signing in.";
          errorEl.hidden = false;
          return;
        }

        errorEl.hidden = true;

        try {
          const response = await fetch("/session", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ token })
          });

          const payload = await response.json();
          const requestId = response.headers.get("X-Request-ID") || "missing";
          requestIdEl.textContent = `Request ID: ${requestId}`;

          if (!response.ok) {
            throw new Error(payload.detail || "Sign-in failed.");
          }

          tokenEl.value = "";
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
        sourcesEl.innerHTML = "<div class=\\"empty\\">Loading sources...</div>";

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

          answerEl.textContent = payload.answer;
          answerEl.className = "answer";

          if (!payload.sources.length) {
            sourcesEl.innerHTML = "<div class=\\"empty\\">No sources returned.</div>";
          } else {
            sourcesEl.innerHTML = payload.sources.map((source) => `
              <article class="source-pill">
                <strong>${source.source || "unknown source"}</strong>
                <span>id=${source.id || "n/a"} | chunk=${source.chunk_index ?? "n/a"} | score=${source.score ?? "n/a"}</span>
              </article>
            `).join("");
          }
        } catch (error) {
          answerEl.textContent = "No answer available.";
          answerEl.className = "empty";
          sourcesEl.innerHTML = "<div class=\\"empty\\">No sources available.</div>";
          errorEl.textContent = error.message;
          errorEl.hidden = false;
        } finally {
          submitEl.disabled = false;
          submitEl.textContent = "Ask the RAG System";
        }
      }

      submitEl.addEventListener("click", askQuestion);
      loginEl.addEventListener("click", login);
      logoutEl.addEventListener("click", logout);
      questionEl.addEventListener("keydown", (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          askQuestion();
        }
      });

      refreshAuthStatus().catch(() => {
        sessionStateEl.textContent = "Auth status: unavailable";
      });
    </script>
  </body>
</html>
"""
