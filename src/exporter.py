from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd


COLUMN_MAP = {
    "serial_number": "Serial Number",
    "job_title": "Job Title",
    "company_name": "Company Name",
    "industry": "Industry",
    "location": "Location",
    "salary": "Salary",
    "match_percentage": "Match Percentage",
    "experience_fit_score": "Experience Fit Score",
    "date_posted": "Date Posted",
    "required_skills": "Required Skills",
    "responsibilities": "Responsibilities",
    "job_description_summary": "Job Description Summary",
    "company_summary": "Company Summary",
    "apply_link": "Apply Link",
}


def export_jobs_to_excel(bucketed_rows: Dict[str, List[dict]]) -> Path:
    Path("data/job_results").mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"data/job_results/job_search_results_{ts}.xlsx")

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for bucket, sheet_name in [
            ("24_hours", "Jobs posted within 24 hours"),
            ("7_days", "Jobs posted within 7 days"),
            ("15_days", "Jobs posted within 15 days"),
        ]:
            df = pd.DataFrame(bucketed_rows[bucket])
            if not df.empty:
                df = df[[*COLUMN_MAP.keys(), "recency_bucket"]].drop(columns=["recency_bucket"]).rename(columns=COLUMN_MAP)
            else:
                df = pd.DataFrame(columns=COLUMN_MAP.values())
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    return output_path
