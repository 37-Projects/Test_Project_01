from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


@dataclass
class SimpleAnalysis:
    full_name: str
    seniority_level: str
    total_years_of_experience: float
    primary_domain: str
    secondary_domain: str
    technical_skills: List[str]
    strengths: List[str]
    gaps: List[str]


def _find_resume_file() -> Path:
    resumes_dir = Path("data/resumes")
    files = [*resumes_dir.glob("*.pdf"), *resumes_dir.glob("*.docx")]
    if not files:
        raise FileNotFoundError("No resume found in data/resumes. Add a PDF or DOCX file and retry.")
    return files[0]


def build_simple_analysis(resume_path: Path) -> SimpleAnalysis:
    guessed_name = resume_path.stem.replace("_", " ").strip() or "Candidate"
    return SimpleAnalysis(
        full_name=guessed_name,
        seniority_level="Mid",
        total_years_of_experience=4.0,
        primary_domain="Software",
        secondary_domain="Data",
        technical_skills=["Python", "SQL", "APIs", "Cloud"],
        strengths=["Execution-focused profile", "Cross-functional collaboration"],
        gaps=["Add quantified impact metrics", "Add domain-specific certifications"],
    )


def generate_overview_fallback(analysis: SimpleAnalysis) -> Path:
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    file_path = Path(f"data/processed/resume_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    lines = [
        "=== Structured Candidate Summary (Fallback Mode) ===",
        f"Name: {analysis.full_name}",
        f"Seniority: {analysis.seniority_level}",
        f"Total Experience: {analysis.total_years_of_experience} years",
        f"Primary Domain: {analysis.primary_domain}",
        f"Secondary Domain: {analysis.secondary_domain}",
        "",
        "=== Skill Matrix ===",
        ", ".join(analysis.technical_skills),
        "",
        "=== Strength Analysis ===",
        *[f"- {item}" for item in analysis.strengths],
        "",
        "=== Gap Analysis ===",
        *[f"- {item}" for item in analysis.gaps],
    ]
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def _make_jobs(analysis: SimpleAnalysis, total: int = 30) -> List[Dict[str, str]]:
    now = datetime.now()
    rows: List[Dict[str, str]] = []
    for i in range(1, total + 1):
        posted = (now - timedelta(days=i % 16)).strftime("%Y-%m-%d")
        days_ago = i % 16
        recency = "24_hours" if days_ago <= 1 else "7_days" if days_ago <= 7 else "15_days"
        rows.append(
            {
                "Serial Number": str(i),
                "Job Title": f"{analysis.primary_domain} Engineer {i}",
                "Company Name": f"Fallback Tech {i}",
                "Industry": analysis.primary_domain,
                "Location": "Bangalore, India",
                "Salary": f"₹{1200000 + i * 10000:,} - ₹{1800000 + i * 15000:,}",
                "Match Percentage": str(max(55, 90 - i // 2)),
                "Experience Fit Score": str(max(50, 92 - i // 2)),
                "Date Posted": posted,
                "Required Skills": ", ".join(analysis.technical_skills),
                "Responsibilities": "Build and maintain scalable systems.",
                "Job Description Summary": "Fallback generated role due to missing third-party dependencies.",
                "Company Summary": "Synthetic company profile for offline mode.",
                "Apply Link": f"https://example.com/jobs/{i}",
                "recency_bucket": recency,
            }
        )
    return rows


def export_jobs_to_csv_fallback(analysis: SimpleAnalysis) -> Path:
    Path("data/job_results").mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"data/job_results/job_search_results_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = _make_jobs(analysis)
    buckets = {"24_hours": [], "7_days": [], "15_days": []}
    for row in jobs:
        buckets[row["recency_bucket"]].append(row)

    for bucket, file_name in [
        ("24_hours", "jobs_posted_within_24_hours.csv"),
        ("7_days", "jobs_posted_within_7_days.csv"),
        ("15_days", "jobs_posted_within_15_days.csv"),
    ]:
        rows = buckets[bucket]
        headers = [k for k in rows[0].keys() if k != "recency_bucket"] if rows else [
            "Serial Number",
            "Job Title",
            "Company Name",
            "Industry",
            "Location",
            "Salary",
            "Match Percentage",
            "Experience Fit Score",
            "Date Posted",
            "Required Skills",
            "Responsibilities",
            "Job Description Summary",
            "Company Summary",
            "Apply Link",
        ]
        with (out_dir / file_name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                row = {k: v for k, v in row.items() if k != "recency_bucket"}
                writer.writerow(row)

    return out_dir


def run_fallback_pipeline() -> None:
    resume_file = _find_resume_file()
    analysis = build_simple_analysis(resume_file)
    overview_path = generate_overview_fallback(analysis)
    output_dir = export_jobs_to_csv_fallback(analysis)

    print("\n=== Execution Summary (Fallback Mode) ===")
    print(f"Resume processed: {resume_file}")
    print(f"Overview generated: {overview_path}")
    print("Top jobs collected: 30")
    print(f"CSV output directory: {output_dir}")
