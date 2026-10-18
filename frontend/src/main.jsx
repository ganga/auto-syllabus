import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { firebaseEnabled, firebaseToken, logout, observeAuth, signInWithGoogle } from "./firebase";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const localDemoMode = import.meta.env.VITE_LOCAL_DEMO_MODE === "true";
const authRequired = firebaseEnabled && !localDemoMode;
const levels = ["beginner", "intermediate", "advanced"];
const demoScenarios = [
  { topic: "Learn Gen AI", timeframe_days: 3, current_skill_level: "beginner" },
  { topic: "Learn guitar", timeframe_days: 3, current_skill_level: "intermediate" },
  { topic: "Learn SFMC", timeframe_days: 3, current_skill_level: "advanced" },
];

function App() {
  const [form, setForm] = useState({ topic: "Master Gen AI", timeframe_days: 7, current_skill_level: "beginner" });
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(!authRequired);
  const [chatMessage, setChatMessage] = useState("");
  const isRefining = job?.status === "processing" && Boolean(job?.result);

  useEffect(() => {
    if (!authRequired) return;
    return observeAuth(nextUser => { setUser(nextUser); setAuthReady(true); });
  }, []);

  useEffect(() => {
    if (!job?.jobId || ["completed", "failed"].includes(job.status)) return;
    const poll = setInterval(async () => {
      try { const token = await firebaseToken(); const response = await fetch(`${API_URL}/curriculum/job/${job.jobId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }); const next = await response.json(); setJob(next); } catch { setError("Could not reach the curriculum service."); }
    }, 1200);
    return () => clearInterval(poll);
  }, [job?.jobId, job?.status]);

  async function submit(event) {
    event.preventDefault(); setError(""); setJob({ status: "processing", current_agent: "Starting", message: "Creating your plan" });
    try {
      const token = await firebaseToken();
      const response = await fetch(`${API_URL}/curriculum/generate`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify(form) });
      if (!response.ok) throw new Error("Request failed");
      setJob({ ...(await response.json()), status: "processing", current_agent: "Queued", message: "Starting your plan" });
    } catch { setError("Could not start your curriculum. Is the API running?"); setJob(null); }
  }

  async function refine(event) {
    event.preventDefault();
    const message = chatMessage.trim();
    if (!message || !job?.jobId) return;
    setError("");
    try {
      const token = await firebaseToken();
      const response = await fetch(`${API_URL}/curriculum/job/${job.jobId}/refine`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ message }) });
      if (!response.ok) throw new Error("Refinement failed");
      setChatMessage("");
      setJob({ ...job, status: "processing", current_agent: "Learner Profiler", message: "Applying your additional context", conversation: [...(job.conversation || []), { role: "user", content: message }] });
    } catch { setError("Could not update your curriculum. Please try again."); }
  }

  async function login() { try { setError(""); await signInWithGoogle(); } catch { setError("Google sign-in was cancelled or unavailable. Please try again."); } }

  if (!authReady) return <main className="login-shell"><p className="eyebrow">AUTO-SYLLABUS</p><p>Checking your session…</p></main>;
  if (authRequired && !user) return <LoginScreen error={error} onLogin={login} />;

  return <main><header>{authRequired && <div className="account"><span>{user.displayName || user.email}</span><button className="sign-in" type="button" onClick={logout}>Sign out</button></div>}</header><section className="hero"><p className="eyebrow">PERSONAL LEARNING, PACED FOR YOU</p><h1>Learn with intent.<br/><i>Watch with a plan.</i></h1><p>Auto-Syllabus builds a concise YouTube curriculum around your goal.</p></section>
  <section className="card">{localDemoMode && <div className="demo-presets"><p className="eyebrow">DEMO SCENARIOS</p>{demoScenarios.map(scenario => <button type="button" className="preset" key={scenario.topic} onClick={() => setForm(scenario)}>{scenario.topic} · {scenario.current_skill_level}</button>)}</div>}<form onSubmit={submit}><label>What do you want to learn?<input value={form.topic} onChange={e => setForm({...form, topic: e.target.value})} /></label><div className="row"><label>Days<input type="number" min="1" max="30" value={form.timeframe_days} onChange={e => setForm({...form, timeframe_days: Number(e.target.value)})}/></label><label className="level-label"><span className="level-heading">Current level <span className="tooltip" tabIndex="0" aria-label="Current level help">?<span className="tooltip-text">Beginner: new to the topic. Intermediate: know the basics and want practical depth. Advanced: ready for specialized, production-level material.</span></span></span><select value={form.current_skill_level} onChange={e => setForm({...form, current_skill_level: e.target.value})}>{levels.map(level => <option key={level}>{level}</option>)}</select></label></div><button>Build my syllabus →</button></form></section>
  {error && <p className="error">{error}</p>}{job && <section className="status"><strong>{job.current_agent}</strong><span>{job.message}</span>{job.status !== "completed" && job.status !== "failed" && <div className="pulse"/>}</section>}
  {isRefining && <section className="refinement-loader" aria-live="polite"><div className="loader-ring"/><div><p className="eyebrow">UPDATING YOUR CURRICULUM</p><h2>Applying your new context</h2><p>Your previous plan is hidden while the agent rebuilds a better fit.</p></div></section>}
  {job?.result && !isRefining && <section className="curriculum"><h2>{job.result.title}</h2>{job.result.days.map(day => <article key={day.day}><div><p className="day">DAY {day.day}</p><h3>{day.title}</h3><p>{day.objective}</p><small>{day.why_chosen}</small></div><iframe title={day.video.title} src={`https://www.youtube-nocookie.com/embed/${day.video.video_id}`} allowFullScreen /></article>)}</section>}
  {job?.result && !isRefining && <section className="chat"><p className="eyebrow">REFINE YOUR PLAN</p><h2>Tell the planner more</h2><p>For example: “I only have 15 minutes a day” or “include more hands-on projects.”</p>{job.conversation?.map((item, index) => <p className={`chat-message ${item.role}`} key={index}>{item.content}</p>)}<form onSubmit={refine}><textarea value={chatMessage} maxLength="800" onChange={e => setChatMessage(e.target.value)} placeholder="Add learning preferences or constraints…"/><button>Update my plan →</button></form></section>}</main>;
}

function LoginScreen({ error, onLogin }) {
  return <main className="login-shell"><section className="login-card"><p className="eyebrow">AUTO-SYLLABUS</p><h1>Your next skill,<br/><i>made clear.</i></h1><p>Sign in to create and save a paced, personalized video curriculum.</p><button className="google-button" onClick={onLogin}><span>G</span> Continue with Google</button>{error && <p className="error">{error}</p>}<small>We use your account only to secure your learning plans.</small></section></main>;
}
createRoot(document.getElementById("root")).render(<App />);
