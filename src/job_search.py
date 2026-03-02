from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .resume_analyzer import ResumeAnalysis


@dataclass
class JobRecord:
    job_title: str
    company_name: str
    industry: str
    location: str
    salary: str
    match_percentage: float
    experience_fit_score: float
    date_posted: datetime
    required_skills: str
    responsibilities: str
    job_description_summary: str
    company_summary: str
    apply_link: str
    recency_bucket: str


def _tokenize(text: str) -> set:
    return {token.strip(".,()[]{}:;!?\"").lower() for token in text.split() if token.strip()}


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
def _fetch_adzuna_jobs(app_id: str, app_key: str, location: str) -> List[Dict]:
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 50,
        "what": "software OR data OR cloud",
        "where": location,
        "content-type": "application/json",
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    return payload.get("results", [])


def _synthetic_jobs(domain: str, location: str, total: int = 120) -> List[Dict]:
    jobs = []
    base_date = datetime.now()
    for i in range(1, total + 1):
        jobs.append(
            {
                "title": f"{domain} Engineer {i}",
                "company": {"display_name": f"Tech Company {i}"},
                "location": {"display_name": location},
                "salary_min": 1200000 + (i * 5000),
                "salary_max": 1800000 + (i * 7000),
                "description": f"Looking for {domain} engineer with Python, SQL, Cloud, APIs, stakeholder collaboration.",
                "created": (base_date - timedelta(days=i % 16)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "redirect_url": f"https://example.com/jobs/{i}",
                "category": {"label": domain},
            }
        )
    return jobs


def _bucketize(posted: datetime) -> str:
    delta = datetime.now() - posted
    if delta <= timedelta(days=1):
        return "24_hours"
    if delta <= timedelta(days=7):
        return "7_days"
    return "15_days"


def _experience_fit(candidate_years: float, title: str) -> float:
    t = title.lower()
    target = 1 if "junior" in t else 4 if "engineer" in t else 8 if "senior" in t else 10
    return max(0.0, 100 - abs(candidate_years - target) * 10)


def _score_job(candidate: ResumeAnalysis, job: Dict, weights: Dict[str, float]) -> Tuple[float, float]:
    jd = (job.get("description") or "")
    skill_overlap = _jaccard(" ".join(candidate.technical_skills), jd)
    keyword_similarity = _jaccard(candidate.career_trajectory_summary, jd)
    domain_match = 1.0 if candidate.primary_domain.lower() in jd.lower() else 0.5
    exp_fit = _experience_fit(candidate.total_years_of_experience, job.get("title", "")) / 100
    posted = datetime.strptime(job.get("created", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")), "%Y-%m-%dT%H:%M:%SZ")
    recency = 1.0 if datetime.now() - posted <= timedelta(days=1) else 0.7 if datetime.now() - posted <= timedelta(days=7) else 0.5

    weighted = (
        weights["skill_overlap"] * skill_overlap
        + weights["keyword_similarity"] * keyword_similarity
        + weights["domain_match"] * domain_match
        + weights["experience_fit"] * exp_fit
        + weights["recency"] * recency
    )
    return round(min(100.0, weighted * 100), 2), round(exp_fit * 100, 2)


def search_and_rank_jobs(candidate: ResumeAnalysis, settings: Dict, env: Dict[str, str]) -> List[JobRecord]:
    location = settings["app"]["location"]
    weights = settings["job_search"]["weights"]

    raw_jobs: List[Dict]
    app_id, app_key = env.get("ADZUNA_APP_ID", ""), env.get("ADZUNA_APP_KEY", "")
    if app_id and app_key:
        logger.info("Using Adzuna API job feed")
        try:
            raw_jobs = _fetch_adzuna_jobs(app_id, app_key, location)
        except Exception as exc:
            logger.warning(f"Adzuna fetch failed ({exc}); falling back to synthetic jobs")
            raw_jobs = _synthetic_jobs(candidate.primary_domain, location)
    else:
        logger.info("No API keys configured; using synthetic job dataset")
        raw_jobs = _synthetic_jobs(candidate.primary_domain, location)

    records: List[JobRecord] = []
    for job in raw_jobs:
        posted_raw = job.get("created", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        posted = datetime.strptime(posted_raw, "%Y-%m-%dT%H:%M:%SZ")
        match, exp_fit = _score_job(candidate, job, weights)
        salary_min, salary_max = job.get("salary_min"), job.get("salary_max")
        salary = f"₹{int(salary_min):,} - ₹{int(salary_max):,}" if salary_min and salary_max else "Not disclosed"
        recency = _bucketize(posted)

        records.append(
            JobRecord(
                job_title=job.get("title", "Unknown Role"),
                company_name=job.get("company", {}).get("display_name", "Unknown Company"),
                industry=job.get("category", {}).get("label", candidate.primary_domain),
                location=job.get("location", {}).get("display_name", location),
                salary=salary,
                match_percentage=match,
                experience_fit_score=exp_fit,
                date_posted=posted,
                required_skills=", ".join(candidate.technical_skills[:8]) or "Python, SQL, Cloud",
                responsibilities="Design, build, and maintain scalable systems.",
                job_description_summary=(job.get("description") or "")[: settings["job_search"]["max_description_chars"]],
                company_summary=f"{job.get('company', {}).get('display_name', 'Company')} is hiring in {location}.",
                apply_link=job.get("redirect_url", "https://example.com"),
                recency_bucket=recency,
            )
        )

    records.sort(
        key=lambda item: (
            item.match_percentage,
            int("".join(ch for ch in item.salary if ch.isdigit()) or 0),
            item.date_posted,
        ),
        reverse=True,
    )
    top_n = settings["app"]["top_n_jobs"]
    return records[:top_n]


def split_by_recency(records: List[JobRecord]) -> Dict[str, List[JobRecord]]:
    buckets = {"24_hours": [], "7_days": [], "15_days": []}
    for record in records:
        buckets[record.recency_bucket].append(record)

    def sorter(item: JobRecord):
        numeric_salary = int("".join(ch for ch in item.salary if ch.isdigit()) or 0)
        return (item.match_percentage, numeric_salary, item.date_posted)

    for key in buckets:
        buckets[key].sort(key=sorter, reverse=True)
    return buckets


def to_rows(records: List[JobRecord]) -> List[Dict]:
    rows = []
    for index, rec in enumerate(records, start=1):
        row = asdict(rec)
        row["serial_number"] = index
        row["date_posted"] = rec.date_posted.strftime("%Y-%m-%d")
        rows.append(row)
    return rows
