import { useEffect, useRef, useState } from "react";
import { analyze, getRoles } from "./api";
import Results from "./Results.jsx";

export default function App() {
  const [roles, setRoles] = useState([]);
  const [role, setRole] = useState("");
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const resultsRef = useRef(null);

  useEffect(() => {
    getRoles()
      .then((r) => { setRoles(r); if (r.length) setRole(r[0].key); })
      .catch(() => setError("Cannot reach the server. Is the backend running?"));
  }, []);

  useEffect(() => {
    if (result && resultsRef.current) resultsRef.current.focus(); // move keyboard/screen-reader focus to the report
  }, [result]);

  async function onSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null);
    if (!file && text.trim().length < 30) { setError("Upload a resume or paste its text."); return; }
    setLoading(true);
    try { setResult(await analyze({ role, file, text })); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  return (
    <>
    <a className="skip-link" href="#main">Skip to main content</a>
    <main className="container" id="main">
      <header>
        <h1>AI Career Navigator</h1>
        <p className="muted">Upload your resume, pick a target role, and get a skill-gap report with a learning roadmap.</p>
      </header>

      <form className="card" onSubmit={onSubmit} aria-busy={loading}>
        <label>Target role
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            {roles.map((r) => <option key={r.key} value={r.key}>{r.name}</option>)}
          </select>
        </label>

        <label>Resume file (PDF, DOCX or TXT, max 2 MB)
          <input type="file" accept=".pdf,.docx,.txt" aria-describedby="privacy-note"
            onChange={(e) => setFile(e.target.files[0] || null)} />
        </label>

        {!file && (
          <label>Or paste resume text
            <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste your resume here..." />
          </label>
        )}

        <button disabled={loading || !role}>{loading ? "Analyzing..." : "Analyze my resume"}</button>
        <p className="error" role="alert">{error}</p>
        <p className="visually-hidden" role="status" aria-live="polite">{loading ? "Analyzing your resume" : ""}</p>
        <p id="privacy-note" className="muted small">Your resume text is processed to compute the report and is not stored.</p>
      </form>

      {result && <Results data={result} headingRef={resultsRef} />}
    </main>
    </>
  );
}
