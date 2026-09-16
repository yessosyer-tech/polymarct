/* POLYMARCT / API client

   The site runs in two modes and decides which on load:

     LIVE    a Polymarct server is answering at /api. Prices, balances,
             positions and settlement are real records in a database.
     DEMO    no server, which is the case on the static host. The browser
             simulation in engine.js drives the numbers instead.

   Nothing here assumes LIVE. Every call that needs a server is guarded, so the
   public site keeps working exactly as before when there is no backend behind
   it. Balances are demo USDC issued by a faucet; no chain, no custody. */

const API = (() => {
  let live = false, me = null, ready = null;

  async function call(path, body, opts){
    const o = Object.assign({ method: body ? "POST" : "GET", credentials: "same-origin" }, opts || {});
    if (body){ o.headers = { "Content-Type": "application/json" }; o.body = JSON.stringify(body); }
    const r = await fetch("/api" + path, o);
    let data = {};
    try { data = await r.json(); } catch (e) {}
    if (!r.ok) throw new Error(data.error || ("request failed: " + r.status));
    return data;
  }

  async function probe(){
    try {
      const c = new AbortController();
      const t = setTimeout(() => c.abort(), 2500);
      const r = await fetch("/api/health", { signal: c.signal, credentials: "same-origin" });
      clearTimeout(t);
      if (!r.ok) return false;
      const h = await r.json();
      live = !!h.ok;
      if (live){ try { me = (await call("/me")).user; } catch (e) { me = null; } }
      return live;
    } catch (e) { return false; }
  }

  function init(){ return ready || (ready = probe()); }

  const money = v => (v / 1e6);
  const fmtUsd = v => "$" + money(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmtShares = v => money(v).toLocaleString("en-US", { maximumFractionDigits: 2 });

  /* ---------- session ---------- */
  async function signup(handle, email, password){
    const d = await call("/auth/signup", { handle, email, password });
    me = d.user; return me;
  }
  async function login(email, password){
    const d = await call("/auth/login", { email, password });
    me = d.user; return me;
  }
  async function logout(){ await call("/auth/logout", {}); me = null; }
  async function refresh(){ try { me = (await call("/me")).user; } catch (e) { me = null; } return me; }
  async function faucet(){ const d = await call("/faucet", {}); await refresh(); return d; }

  /* ---------- markets ---------- */
  const markets = (q) => call("/markets" + (q || ""));
  const market = (id) => call("/markets/" + encodeURIComponent(id));
  const quote = (id, side, action, v) =>
    call("/quote?market=" + encodeURIComponent(id) + "&side=" + side + "&action=" + action +
         (action === "buy" ? "&amount=" + v : "&shares=" + v));
  const trade = (id, side, action, v) =>
    call("/trade", action === "buy"
      ? { market: id, side, action, amount: v }
      : { market: id, side, action, shares: v });
  const portfolio = () => call("/portfolio");
  const ledger = () => call("/ledger");
  const leaderboard = () => call("/leaderboard");
  const createMarket = (spec) => call("/markets", spec);
  const dispute = (market, reason) => call("/dispute", { market, reason });

  /* ---------- the sign in sheet ---------- */
  function authSheet(afterwards){
    const box = `
      <div class="panel-h"><span>ACCOUNT</span><span class="mono acid">DEMO USDC</span></div>
      <div class="filters" style="margin-bottom:18px">
        <button id="tab-in" class="on">SIGN IN</button><button id="tab-up">CREATE ACCOUNT</button>
      </div>
      <div id="f-up" class="hide"><div class="field"><label>HANDLE</label><input id="a-handle" autocomplete="username"></div></div>
      <div class="field"><label>EMAIL</label><input id="a-email" type="email" autocomplete="email"></div>
      <div class="field"><label>PASSWORD</label><input id="a-pass" type="password" autocomplete="current-password">
        <div class="hint">At least 10 characters.</div></div>
      <div class="errmsg hide" id="a-err"></div>
      <button class="btn btn--primary btn--block" id="a-go">SIGN IN</button>
      <p class="muted" style="font-size:11px;line-height:1.6;margin:14px 0 0">Balances are demo USDC issued by a faucet so the market can be used end to end. No wallet is connected, no chain is touched and no real funds exist here.</p>`;
    UI.openModal(box);
    let mode = "in";
    const $ = id => document.getElementById(id);
    const setMode = m => {
      mode = m;
      $("tab-in").classList.toggle("on", m === "in");
      $("tab-up").classList.toggle("on", m === "up");
      $("f-up").classList.toggle("hide", m !== "up");
      $("a-go").textContent = m === "in" ? "SIGN IN" : "CREATE ACCOUNT";
      $("a-pass").autocomplete = m === "in" ? "current-password" : "new-password";
    };
    $("tab-in").onclick = () => setMode("in");
    $("tab-up").onclick = () => setMode("up");
    $("a-go").onclick = async () => {
      const err = $("a-err");
      err.classList.add("hide");
      try {
        if (mode === "in") await login($("a-email").value.trim(), $("a-pass").value);
        else await signup($("a-handle").value.trim(), $("a-email").value.trim(), $("a-pass").value);
        UI.closeModal();
        paintAccount();
        UI.toast("SIGNED IN // " + me.handle.toUpperCase());
        if (afterwards) afterwards();
      } catch (e) {
        err.textContent = e.message;
        err.classList.remove("hide");
      }
    };
  }

  /* ---------- the header, once we know which mode we are in ---------- */
  function paintAccount(){
    const btn = document.getElementById("connect");
    if (!btn) return;
    if (!live){
      btn.textContent = "CONNECT WALLET";
      return;
    }
    if (me){
      btn.textContent = me.handle.toUpperCase() + " // " + fmtUsd(me.balance);
      btn.onclick = accountSheet;
    } else {
      btn.textContent = "SIGN IN";
      btn.onclick = () => authSheet();
    }
  }

  function accountSheet(){
    UI.openModal(`
      <div class="panel-h"><span>ACCOUNT</span><span class="mono acid">${me.handle}</span></div>
      <div class="kv"><span class="k">BALANCE</span><span>${fmtUsd(me.balance)} USDC</span></div>
      <div class="kv"><span class="k">NETWORK</span><span>DEMO LEDGER</span></div>
      <div class="kv"><span class="k">ACCEPTED ASSET</span><span class="acid">USDC ONLY</span></div>
      <a class="btn btn--block" style="margin-top:16px" href="portfolio.html">OPEN PORTFOLIO</a>
      <button class="btn btn--block" style="margin-top:8px" id="a-faucet">TOP UP DEMO BALANCE</button>
      <button class="btn btn--block" style="margin-top:8px" id="a-out">SIGN OUT</button>`);
    document.getElementById("a-faucet").onclick = async () => {
      try { const d = await faucet(); UI.toast("CREDITED " + fmtUsd(d.credited)); UI.closeModal(); paintAccount(); }
      catch (e) { UI.toast(e.message.toUpperCase()); }
    };
    document.getElementById("a-out").onclick = async () => {
      await logout(); UI.closeModal(); paintAccount(); UI.toast("SIGNED OUT");
    };
  }

  function requireUser(then){
    if (me) return then();
    authSheet(then);
  }

  /* wire the header as soon as the mode is known */
  init().then(() => {
    paintAccount();
    if (live) document.body.dataset.api = "live";
  });

  return { init, get live(){ return live; }, get me(){ return me; },
           call, signup, login, logout, refresh, faucet,
           markets, market, quote, trade, portfolio, ledger, leaderboard,
           createMarket, dispute,
           money, fmtUsd, fmtShares, authSheet, paintAccount, requireUser };
})();
