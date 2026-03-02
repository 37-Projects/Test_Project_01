from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .resume_analyzer import ResumeAnalysis


def generate_overview(analysis: ResumeAnalysis, salary_guidance: str) -> Path:
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = Path(f"data/processed/resume_overview_{timestamp}.txt")

    recommended_roles = [
        f"{analysis.primary_domain} Engineer",
        f"Senior {analysis.primary_domain} Specialist",
        f"{analysis.secondary_domain} Consultant",
        "Technical Program Manager",
    ]

    lines = [
        "=== Structured Candidate Summary ===",
        f"Name: {analysis.full_name}",
        f"Contact: {', '.join(analysis.contact_information) or 'N/A'}",
        f"Seniority: {analysis.seniority_level}",
        f"Total Experience: {analysis.total_years_of_experience} years",
        "",
        "=== Skill Matrix ===",
        ", ".join(analysis.technical_skills) or "N/A",
        "",
        "=== Experience Breakdown by Industry ===",
    ]
    lines.extend([f"- {k.title()}: {v} years" for k, v in analysis.experience_per_domain.items()])
    lines.extend(
        [
            "",
            "=== Career Trajectory Summary ===",
            analysis.career_trajectory_summary,
            "",
            "=== Strength Analysis ===",
            *[f"- {item}" for item in analysis.strengths],
            "",
            "=== Gap Analysis ===",
            *[f"- {item}" for item in analysis.gaps],
            "",
            "=== Recommended Job Titles (Ranked) ===",
            *[f"{idx}. {title}" for idx, title in enumerate(recommended_roles, start=1)],
            "",
            "=== Recommended Industries ===",
            ", ".join(analysis.sector_industry),
            "",
            "=== Skills to Enhance ===",
            "- Advanced System Design",
            "- Stakeholder Communication",
            "- Domain-specific tooling depth",
            "",
            "=== Certifications Suggested ===",
            "- AWS/GCP Associate",
            "- Scrum/Agile Certification",
            "- Domain-relevant professional certification",
            "",
            "=== Job Search Strategy Advice ===",
            "- Prioritize roles posted in the last 24 hours",
            "- Tailor resume keywords to JD terms",
            "- Apply to product companies and startup/scale-up roles",
            "",
            "=== Salary Positioning Guidance (Bangalore) ===",
            salary_guidance,
            "",
        ]
    )

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path
