from __future__ import annotations

import os
from pathlib import Path


DEFAULT_SETTINGS = {
    "resume": {"supported_extensions": [".pdf", ".docx"]},
    "salary_benchmarks_bangalore": {
        "entry": "₹5L - ₹10L",
        "mid": "₹10L - ₹22L",
        "senior": "₹22L - ₹40L",
        "lead": "₹35L - ₹60L+",
    },
}


def _find_resume(settings: dict) -> Path:
    resumes_dir = Path("data/resumes")
    allowed = set(settings["resume"]["supported_extensions"])
    files = [p for p in resumes_dir.glob("*") if p.suffix.lower() in allowed]
    if not files:
        raise FileNotFoundError(
            "No resume found in data/resumes. Please place PDF/DOCX resume file(s) there and re-run."
        )
    return files[0]


def _salary_guidance(settings: dict, seniority_level: str) -> str:
    return settings["salary_benchmarks_bangalore"].get(seniority_level.lower(), "₹8L - ₹20L")


def _run_full_pipeline() -> None:
    from dotenv import load_dotenv
    from loguru import logger

    from src.config_loader import load_settings
    from src.exporter import export_jobs_to_excel
    from src.job_search import search_and_rank_jobs, split_by_recency, to_rows
    from src.logger_setup import configure_logger
    from src.overview_generator import generate_overview
    from src.resume_analyzer import analyze_resume

    load_dotenv()
    settings = load_settings()
    configure_logger(settings["app"]["log_level"])

    logger.info("=== Starting AI Resume Analysis + Intelligent Job Search Agent ===")

    resume_file = _find_resume(settings)
    analysis = analyze_resume(resume_file)
    overview_path = generate_overview(analysis, _salary_guidance(settings, analysis.seniority_level))

    records = search_and_rank_jobs(analysis, settings, os.environ)
    bucketed = split_by_recency(records)
    bucketed_rows = {bucket: to_rows(items) for bucket, items in bucketed.items()}
    excel_path = export_jobs_to_excel(bucketed_rows)

    logger.info("Pipeline completed successfully.")
    print("\n=== Execution Summary ===")
    print(f"Resume processed: {resume_file}")
    print(f"Overview generated: {overview_path}")
    print(f"Top jobs collected: {len(records)}")
    print(f"Excel generated: {excel_path}")


def main() -> None:
    try:
        _run_full_pipeline()
    except ModuleNotFoundError as exc:
        missing_module = str(exc).split("'")[-2] if "'" in str(exc) else str(exc)
        print(f"Dependency '{missing_module}' is missing. Switching to minimal fallback mode.")
        from src.minimal_fallback import run_fallback_pipeline

        run_fallback_pipeline()


if __name__ == "__main__":
    main()
