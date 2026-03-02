# AI Resume Analysis + Intelligent Job Search Agent

This project processes resumes and generates:
1. Structured resume overview (`data/processed/resume_overview_<timestamp>.txt`)
2. Ranked job matches for **Bangalore, India**
3. Excel output with 3 sheets (`data/job_results/job_search_results_<timestamp>.xlsx`)

## Project Structure

- `data/resumes` → place PDF/DOCX resume(s) here
- `data/processed` → generated resume overview files
- `data/job_results` → generated job search Excel files
- `logs` → execution logs
- `src` → modular pipeline components
- `config/settings.yaml` → runtime configuration

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Optional APIs in `.env`:
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`

If not provided, the system uses a synthetic fallback dataset to keep pipeline execution reliable.

## Run

```bash
python main.py
```

## What the pipeline does

- Resume analysis
  - extracts name, contact, education, work date ranges, skills, certifications
  - computes total years of experience from date ranges
  - infers primary/secondary domain and seniority
- Overview generation
  - strengths, gaps, strategy, recommended roles, Bangalore salary positioning
- Job search & ranking
  - fetches API jobs (if keys available), otherwise synthetic fallback
  - computes match percentage, experience fit, recency bucket
  - ranks and keeps top 100 jobs
- Excel output
  - Sheet 1: Jobs posted within 24 hours
  - Sheet 2: Jobs posted within 7 days
  - Sheet 3: Jobs posted within 15 days

## Notes

- Place resume files in `data/resumes` before execution.
- Logs are stored in `logs/pipeline.log`.
