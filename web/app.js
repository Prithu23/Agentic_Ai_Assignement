const $ = (id) => document.getElementById(id);
const EMOJI = { Amazon: "📦", Google: "🔍", Microsoft: "🪟", Flipkart: "🛒", Infosys: "🏢", TCS: "💼", Nvidia: "🎮" };
const COLORS = { correctness: "#5ee6a8", depth: "#7ad7ff", communication: "#ff8fc7", overall: "#b79cff" };

let options = {}, company = null, role = null, num = 5;
let sid = null, xp = 0, streak = 0, busy = false;

async function api(path, body) {
  const res = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

/* ---------- setup ---------- */
async function init() {
  const data = await api("/api/options");
  options = data.options;
  $("companies").innerHTML = "";
  Object.keys(options).forEach((c) => {
    const d = document.createElement("div");
    d.className = "card";
    d.innerHTML = `<span class="em">${EMOJI[c] || "🏆"}</span>`;
    d.append(c);
    d.onclick = () => pickCompany(c, d);
    $("companies").append(d);
  });
  [3, 5, 8].forEach((n) => {
    const b = chip(`${n} questions`, () => { num = n; mark("counts", b); });
    if (n === num) b.classList.add("on");
    $("counts").append(b);
  });
}

function chip(text, onclick) {
  const b = document.createElement("button");
  b.className = "chip"; b.type = "button"; b.textContent = text; b.onclick = onclick;
  return b;
}
function mark(boxId, el) {
  document.querySelectorAll(`#${boxId} > *`).forEach((x) => x.classList.remove("on"));
  el.classList.add("on");
}

function pickCompany(c, el) {
  company = c; role = null; mark("companies", el);
  buddyMood("happy", "Great pick!", $("buddyHero"));
  $("roles").innerHTML = "";
  options[c].forEach((r) => {
    const b = chip(r, () => { role = r; mark("roles", b); $("startBtn").disabled = false; });
    $("roles").append(b);
  });
  if (options[c].length === 1) $("roles").firstChild.click(); else $("startBtn").disabled = true;
}

$("startBtn").onclick = async () => {
  $("startBtn").disabled = true;
  try {
    const d = await api("/api/start", { company, role, num });
    sid = d.session_id; xp = 0; streak = 0; updateStats();
    $("setup").hidden = true; $("reportScreen").hidden = true; $("chat").hidden = false; $("stats").hidden = false;
    $("log").innerHTML = "";
    $("who").textContent = `${EMOJI[company] || ""} ${company} · ${role}`;
    setProgress(d.progress);
    addMsg("Interviewer", `Welcome to your ${company} mock interview! Answer like it's the real thing. Use the buttons on the left if you need a hint, want to skip, or want coaching.`);
    showQuestion(d.next);
  } catch (e) { alert(e.message); $("startBtn").disabled = false; }
};

/* ---------- chat ---------- */
function addMsg(agent, text, extra) {
  const m = document.createElement("div");
  m.className = `msg ${agent}`;
  const tag = document.createElement("span");
  tag.className = "tag";
  tag.textContent = agent === "user" ? "You" : agent;
  m.append(tag);
  if (text) m.append(document.createTextNode(text));
  if (extra) m.append(extra);
  $("log").append(m);
  $("log").scrollTop = $("log").scrollHeight;
  return m;
}

function showQuestion(n) {
  const wrap = document.createElement("div");
  const q = document.createElement("span");
  q.className = "qtext"; q.textContent = n.question;
  const meta = document.createElement("div");
  meta.className = "qmeta";
  [n.meta.round, n.meta.category, n.meta.difficulty].forEach((t, i) => {
    const s = document.createElement("span");
    s.textContent = t; if (i === 2) s.className = t;
    meta.append(s);
  });
  wrap.append(q, meta);
  addMsg("Interviewer", n.lead + "\n", wrap);
  buddyMood("think", "Hmm, take your time…");
}

function meters(sc) {
  const box = document.createElement("div");
  box.className = "meters";
  ["correctness", "depth", "communication", "overall"].forEach((k) => {
    const row = document.createElement("div");
    row.className = "meter";
    row.innerHTML = `<span>${k[0].toUpperCase() + k.slice(1)}</span><div class="track"><div class="fill" style="background:${COLORS[k]}"></div></div><b>${sc[k]}</b>`;
    box.append(row);
    setTimeout(() => (row.querySelector(".fill").style.width = sc[k] * 10 + "%"), 60);
  });
  const lists = document.createElement("div");
  lists.className = "lists";
  if (sc.strengths.length) lists.append(line("✅ " + sc.strengths.join(" · ")));
  if (sc.gaps.length) lists.append(line("🎯 " + sc.gaps.join(" · ")));
  box.append(lists);
  return box;
}
const line = (t) => Object.assign(document.createElement("div"), { textContent: t });

function sources(items) {
  if (!items || !items.length) return null;
  const d = document.createElement("details");
  d.className = "srcs";
  d.innerHTML = "<summary>📚 Based on real past feedback</summary>";
  const ul = document.createElement("ul");
  items.forEach((f) => { const li = document.createElement("li"); li.textContent = `(${f.round}, ${f.outcome}) ${f.text}`; ul.append(li); });
  d.append(ul);
  return d;
}

function typing() {
  const t = document.createElement("div");
  t.className = "msg Interviewer typing";
  t.innerHTML = "<i></i><i></i><i></i>";
  $("log").append(t); $("log").scrollTop = $("log").scrollHeight;
  return t;
}

async function send(text) {
  text = text.trim();
  if (!text || busy) return;
  busy = true; $("send").disabled = true;
  addMsg("user", text);
  $("input").value = "";
  buddyMood("think", "Let me check that…");
  const t = typing();
  try {
    const d = await api("/api/chat", { session_id: sid, message: text });
    t.remove();
    setProgress(d.progress);
    for (const m of d.messages) {
      if (m.kind === "scores") addMsg("Evaluator", m.text, d.scores ? meters(d.scores) : null);
      else if (m.kind === "coach") addMsg("Coach", m.text, sources(d.sources));
      else if (m.kind !== "report") addMsg(m.agent, m.text);
    }
    if (d.intent === "practice" && d.scores) reward(d.scores.overall);
    if (d.next) showQuestion(d.next);
    if (d.report) setTimeout(() => showReport(d.report), 1200);
  } catch (e) { t.remove(); addMsg("Interviewer", "Oops: " + e.message); }
  busy = false; $("send").disabled = false; $("input").focus();
}

function reward(score) {
  const gain = Math.round(score * 10);
  xp += gain; streak = score >= 6 ? streak + 1 : 0;
  updateStats(true);
  if (score >= 7.5) { buddyMood("happy", `Wow! +${gain} XP 🎉`); confetti(); }
  else if (score >= 5) buddyMood("happy", `Nice one! +${gain} XP`);
  else buddyMood("sad", `Keep going! +${gain} XP`);
}

function updateStats(pop) {
  $("xp").textContent = xp; $("streak").textContent = streak;
  if (pop) document.querySelectorAll(".pill").forEach((p) => { p.classList.remove("pop"); void p.offsetWidth; p.classList.add("pop"); });
}

function setProgress(p) {
  $("barFill").style.width = (p.total ? (p.index / p.total) * 100 : 0) + "%";
  $("barText").textContent = `${Math.min(p.index + 1, p.total)} / ${p.total} questions`;
}

function buddyMood(mood, say, el) {
  const b = el || $("buddy");
  b.className = "buddy" + (b.id === "buddyHero" ? " big" : "") + " " + mood;
  if (!el) $("buddySays").textContent = say;
}

$("form").onsubmit = (e) => { e.preventDefault(); send($("input").value); };
$("input").onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send($("input").value); } };
document.querySelectorAll(".quick button").forEach((b) => (b.onclick = () => send(b.dataset.say)));

/* ---------- report ---------- */
function showReport(r) {
  $("chat").hidden = true; $("reportScreen").hidden = false;
  const o = r.averages.overall;
  const verdict = o >= 8 ? "Interview ready! 🏆" : o >= 6 ? "Getting there! 💪" : o >= 4 ? "Good start, keep practising 🌱" : "Let's build this up 🚀";
  const el = $("report");
  el.innerHTML = "";
  const box = document.createElement("div");
  box.className = "rep";
  box.innerHTML = `<h1 class="grad">${verdict}</h1><div class="muted">${r.company} · ${r.role} · ${r.answered} answered, ${r.skipped} skipped</div>
    <div class="ring" style="--p:${o * 10}"><div>${o}</div></div><div class="meters" style="max-width:420px;margin:auto"></div>`;
  ["correctness", "depth", "communication"].forEach((k) => {
    const row = document.createElement("div");
    row.className = "meter";
    row.innerHTML = `<span>${k[0].toUpperCase() + k.slice(1)}</span><div class="track"><div class="fill" style="background:${COLORS[k]}"></div></div><b>${r.averages[k]}</b>`;
    box.querySelector(".meters").append(row);
    setTimeout(() => (row.querySelector(".fill").style.width = r.averages[k] * 10 + "%"), 100);
  });
  const cols = document.createElement("div");
  cols.className = "cols";
  cols.append(
    section("good", "💪 Strengths", r.strengths, "Answer more questions to reveal strengths!"),
    section("bad", "🎯 Focus areas", r.gaps, "No weak spots, nice!"),
  );
  const plan = section("plan", `📋 Your ${r.company} improvement plan`, r.plan, "", true);
  cols.append(plan);
  box.append(cols);
  const again = document.createElement("button");
  again.className = "go again"; again.textContent = "Practice again 🔁";
  again.onclick = () => { $("reportScreen").hidden = true; $("chat").hidden = true; $("stats").hidden = true; $("setup").hidden = false; $("startBtn").disabled = !role; };
  box.append(again);
  el.append(box);
  if (o >= 6) confetti();
}

function section(cls, title, items, empty, ordered) {
  const d = document.createElement("div");
  d.className = "box " + cls;
  d.innerHTML = `<h4>${title}</h4>`;
  if (!items.length) { d.append(empty); return d; }
  if (ordered) {
    const ol = document.createElement("ol");
    items.forEach((t) => { const li = document.createElement("li"); li.textContent = t; ol.append(li); });
    d.append(ol);
  } else items.forEach((t) => { const s = document.createElement("span"); s.className = "badge"; s.textContent = t; d.append(s); });
  return d;
}

/* ---------- confetti ---------- */
function confetti() {
  const c = $("confetti"), ctx = c.getContext("2d");
  c.width = innerWidth; c.height = innerHeight;
  const cols = ["#ff8fc7", "#b79cff", "#7ad7ff", "#5ee6a8", "#ffdd33", "#ff9f45"];
  const ps = Array.from({ length: 140 }, () => ({
    x: Math.random() * c.width, y: -20 - Math.random() * c.height * 0.4, r: 4 + Math.random() * 6,
    vx: Math.random() * 4 - 2, vy: 2 + Math.random() * 4, a: Math.random() * 6, col: cols[(Math.random() * cols.length) | 0],
  }));
  let frames = 0;
  (function tick() {
    ctx.clearRect(0, 0, c.width, c.height);
    ps.forEach((p) => {
      p.x += p.vx; p.y += p.vy; p.a += 0.1;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.a); ctx.fillStyle = p.col; ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r); ctx.restore();
    });
    if (++frames < 200) requestAnimationFrame(tick); else ctx.clearRect(0, 0, c.width, c.height);
  })();
}

init().catch((e) => alert("Can't reach the server: " + e.message));
