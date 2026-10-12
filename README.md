# AI Career Navigator

![CI](https://github.com/Aryan22109/ai-career-navigator/actions/workflows/ci.yml/badge.svg)

A full-stack web app that analyzes a resume against a target role (SDE, AI/ML, DevOps, Data Scientist) and returns:

- a **Job Readiness Score** (0–100),
- a **skill-gap report** (matched, missing, and extra skills),
- a **personalized learning roadmap** with a build task and a learning source for each gap,
- **resume tips** (missing sections, no dates, too short, etc.).

**Stack:** Python, Flask, spaCy, SQLAlchemy, MySQL (SQLite fallback for local dev), React (Vite), Docker.

## Screenshots

These screenshots show the resume-analysis interface and example outputs for multiple target roles. The file name in the overview image has been anonymized.

### Application and report preview

![AI Career Navigator upload form and report preview](docs/screenshots/01-app-overview.png)

### Software Development Engineer example

![Job-readiness score and matched skills for the Software Development Engineer role](docs/screenshots/02-software-engineer-score-and-skills.png)

![Skill gaps and recommended next steps for the Software Development Engineer role](docs/screenshots/03-software-engineer-skill-gaps.png)

![Further learning-roadmap recommendations](docs/screenshots/04-learning-roadmap-details.png)

### Data Scientist example

![Job-readiness score and matched skills for the Data Scientist role](docs/screenshots/05-data-scientist-score-and-skills.png)

![Data Scientist skill gaps and learning roadmap](docs/screenshots/06-data-scientist-gaps-and-roadmap.png)

## How it works

1. **Parse**: text is extracted from PDF, DOCX or TXT (`pypdf`, `python-docx`).
2. **Extract skills**: a spaCy `PhraseMatcher` matches a taxonomy of ~60 skills with aliases. The resume is split into sections, so a skill used in *Projects/Experience* counts as **applied** and a skill only in a skills list counts as **listed**.
3. **Score**: each role is a weighted benchmark stored in the database (core = 3, important = 2, bonus = 1). Applied skills earn full credit, listed skills earn 70%. Score = earned weight ÷ total weight × 100.
4. **Roadmap**: missing skills are ordered by weight and mapped to a concrete build task and a documentation source.

Resume text is never stored; the database keeps only role benchmarks and aggregate analysis results (role, score, counts).

## Run locally

Start the backend and frontend in **two separate terminals**.

### Windows (PowerShell)

Backend terminal:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m spacy download en_core_web_sm
.\.venv\Scripts\python.exe wsgi.py
```
The backend listens on `http://localhost:5000` and uses SQLite by default. Calling the root URL `/` may return 404; check the health route at `http://localhost:5000/api/health`.

Frontend terminal (from the repository root):
```powershell
cd frontend
npm install
npm run dev
```
Open the Vite URL printed in the terminal, usually `http://localhost:5173`. The Vite dev server proxies `/api` requests to port 5000.

### macOS / Linux

Backend terminal:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
python wsgi.py
```
Frontend terminal (from the repository root):
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

To use MySQL, set `DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/career_navigator`.

### Docker (MySQL + backend + frontend)
```bash
cp .env.example .env      # set real passwords
docker compose up --build # open http://localhost:8080
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/roles` | Available target roles |
| POST | `/api/analyze` | `multipart/form-data` with `role` and either `file` or `text` |
| GET | `/api/history` | Last 10 analyses (role, score, time) |
| GET | `/api/stats` | Aggregate usage: total analyses and average score per role |

## Tests and evaluation

```bash
cd backend
python -m pytest                         # unit + API tests
python scripts/evaluate_extraction.py    # precision / recall on labelled resumes
```
The bundled labelled set is small (5 hand-written resumes) and is only a smoke test. To measure extraction accuracy honestly, add your own anonymised resumes as `rN.txt` plus `rN.json` (the list of skills a human would extract) in `backend/tests/data/labeled/` and re-run the script.

## Goals and success metrics

| Goal | Metric | Target | Current status |
|---|---|---|---|
| Accurate skill extraction | Precision / recall / F1 on labelled resumes | F1 ≥ 85% on real resumes | 100% on the 5 bundled hand-written samples (smoke test only). **Not yet measured on real resumes.** |
| Fast feedback | Median `/api/analyze` latency (text input, local machine) | < 500 ms | ~18 ms median, ~21 ms p95 (40 runs, SQLite, no network) |
| Reliability | Automated tests passing in CI | 100% | 19 tests (parser, scoring, API, security) |
| Useful output | Share of analyses that return a roadmap | Track over time | Aggregates available at `GET /api/stats` |
| Real usability | Feedback from users | 5–10 testers | Not started |

Update the "Current status" column as you gather real data.

## How it compares

| | AI Career Navigator | JD-based ATS scanners (e.g. Jobscan) |
|---|---|---|
| Input | Resume + a target **role** | Resume + a specific **job description** |
| Output | Weighted skill-gap report, learning roadmap with build tasks | Match rate, missing keywords, formatting checks |
| Strength | Tells you what to **learn next** and in what order | Tailors a resume to one posting and checks ATS formatting |
| Limitation | No job-description input, no formatting checks, small skill taxonomy | Focused on keyword matching rather than skill development |

They solve different problems: scanners help you tailor a resume for one job, while this app helps you decide what to build or learn for a role. A natural next step is to accept a pasted job description as the benchmark.

## Security and privacy

- Uploads are checked by **file signature**, not just extension (real PDF/DOCX/TXT), limited to 2 MB, 10 PDF pages, and a DOCX unpack-size cap.
- `/api/analyze` is **rate limited** per client IP (default 20/min, `RATE_LIMIT_PER_MIN`). The limiter is in-memory; use Redis if you run several workers.
- Behind nginx or a load balancer set `TRUST_PROXY=1` so the real client IP is used.
- Responses send `X-Content-Type-Options: nosniff` and `Cache-Control: no-store`.
- Resume text and personal details are **never stored**; only role, score and counts are saved.
- CORS is restricted to `CORS_ORIGINS`. Use strong database passwords (see `.env.example`).

## Accessibility

The UI aims for WCAG 2.1 AA: labelled form controls, a skip link, visible focus outlines, errors and loading announced to screen readers (`role="alert"` / `aria-live`), focus moved to the results heading after analysis, text that does not rely on colour alone, and reduced-motion support. A full manual audit with a screen reader is still recommended.

## Continuous integration

`.github/workflows/ci.yml` runs the backend tests and extraction evaluation and builds the frontend on every push and pull request.

## Roadmap

- Accept a pasted job description as the benchmark.
- Evaluate extraction on a larger set of real, anonymised resumes and publish the numbers.
- Add OCR support for scanned PDFs.
- Deploy a public demo and gather feedback from 5–10 users.
- Optional: Redis-backed rate limiting and caching for multi-instance deployments.

## Limitations

- Skill matching is keyword/alias based, so unusual wording can be missed. Extend `backend/app/skills_data.py` to improve coverage.
- Scanned (image-only) PDFs are not supported; there is no OCR.
- The score measures skill coverage against a benchmark, not hiring probability.

## License
MIT
