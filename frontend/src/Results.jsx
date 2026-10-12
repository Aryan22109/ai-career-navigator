function ScoreRing({ score }) {
  const r = 52, c = 2 * Math.PI * r;
  const color = score >= 80 ? "#16a34a" : score >= 60 ? "#2563eb" : score >= 40 ? "#d97706" : "#dc2626";
  return (
    <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={`Job readiness score ${score} out of 100`}>
      <circle cx="70" cy="70" r={r} fill="none" stroke="#e5e7eb" strokeWidth="12" />
      <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} transform="rotate(-90 70 70)" />
      <text x="70" y="78" textAnchor="middle" fontSize="30" fontWeight="700">{Math.round(score)}</text>
    </svg>
  );
}

const Chip = ({ children, kind }) => <span className={`chip ${kind}`} role="listitem">{children}</span>;

export default function Results({ data, headingRef }) {
  return (
    <section className="results" aria-labelledby="results-heading">
      <div className="card score">
        <ScoreRing score={data.job_readiness_score} />
        <div>
          <h2 id="results-heading" ref={headingRef} tabIndex={-1}>{data.readiness_label}</h2>
          <p className="muted">Job Readiness Score for <strong>{data.role.name}</strong></p>
        </div>
      </div>

      <div className="card">
        <h3>Skills you already show ({data.matched_skills.length})</h3>
        <div className="chips" role="list">
          {data.matched_skills.map((m) => (
            <Chip key={m.skill} kind={m.evidence === "applied" ? "good" : "ok"}>
              {m.skill}{m.evidence === "listed" ? " (listed only)" : ""}
            </Chip>
          ))}
        </div>
        <p className="muted small">Skills used in projects or experience count fully; skills only listed count 70%.</p>
      </div>

      <div className="card">
        <h3>Skill gaps ({data.missing_skills.length})</h3>
        <div className="chips" role="list">
          {data.missing_skills.map((m) => <Chip key={m.skill} kind={m.tier}>{m.skill} · {m.tier} priority</Chip>)}
        </div>
      </div>

      <div className="card">
        <h3>Learning roadmap</h3>
        {data.roadmap.length === 0 && <p>No gaps found for this role. Nice work.</p>}
        <ol className="roadmap">
          {data.roadmap.map((s) => (
            <li key={s.skill}>
              <strong>{s.skill}</strong> <span className="muted">· {s.priority} · ~{s.estimated_weeks} wk</span>
              <p>{s.build_task}</p>
              <a href={s.learn_from} target="_blank" rel="noreferrer">Learn {s.skill} (opens in a new tab)</a>
            </li>
          ))}
        </ol>
      </div>

      {data.resume_tips.length > 0 && (
        <div className="card">
          <h3>Resume tips</h3>
          <ul>{data.resume_tips.map((t) => <li key={t}>{t}</li>)}</ul>
        </div>
      )}
    </section>
  );
}
