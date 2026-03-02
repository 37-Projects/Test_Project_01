from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from docx import Document
from loguru import logger
from pypdf import PdfReader


MONTH_PATTERN = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
DATE_RANGE_PATTERN = re.compile(
    rf"({MONTH_PATTERN}\s+\d{{4}}|\d{{4}})\s*[-–to]+\s*(present|current|{MONTH_PATTERN}\s+\d{{4}}|\d{{4}})",
    flags=re.IGNORECASE,
)


@dataclass
class ResumeAnalysis:
    full_name: str
    contact_information: List[str]
    education: List[str]
    work_experience: List[Dict[str, str]]
    total_years_of_experience: float
    sector_industry: List[str]
    domain_expertise: List[str]
    technical_skills: List[str]
    tools_technologies: List[str]
    certifications: List[str]
    leadership_managerial_experience: str
    primary_domain: str
    secondary_domain: str
    experience_per_domain: Dict[str, float]
    seniority_level: str
    career_trajectory_summary: str
    strengths: List[str]
    gaps: List[str]


TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript", "sql", "aws", "azure", "gcp", "docker",
    "kubernetes", "pandas", "numpy", "machine learning", "deep learning", "nlp", "genai",
    "react", "node", "fastapi", "django", "flask", "spark", "hadoop", "tableau", "power bi",
}

DOMAIN_KEYWORDS = {
    "data": ["data", "analytics", "bi", "machine learning", "ai", "etl"],
    "software": ["software", "backend", "frontend", "full stack", "api", "microservice"],
    "cloud": ["cloud", "aws", "azure", "devops", "sre", "kubernetes", "terraform"],
    "security": ["security", "soc", "iam", "vulnerability", "siem"],
    "product": ["product", "roadmap", "stakeholder", "go-to-market"],
}


def _extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        doc = Document(str(file_path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {suffix}")


def _extract_name(lines: List[str]) -> str:
    for line in lines[:5]:
        if 1 <= len(line.split()) <= 4 and not any(ch.isdigit() for ch in line):
            return line.strip()
    return "Unknown Candidate"


def _extract_contact(text: str) -> List[str]:
    items = []
    email_matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_matches = re.findall(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    linkedin_matches = re.findall(r"https?://(?:www\.)?linkedin\.com/[^\s]+", text, flags=re.IGNORECASE)
    items.extend(email_matches + phone_matches + linkedin_matches)
    return list(dict.fromkeys(items))


def _section_lines(text: str, marker_words: List[str]) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result: List[str] = []
    collect = False
    for line in lines:
        lowered = line.lower()
        if any(word in lowered for word in marker_words):
            collect = True
            continue
        if collect and re.match(r"^[A-Z][A-Za-z\s/&-]{2,30}$", line):
            break
        if collect:
            result.append(line)
    return result


def _extract_skills(text: str) -> List[str]:
    lowered = text.lower()
    found = sorted({keyword for keyword in TECH_KEYWORDS if keyword in lowered})
    return [skill.title() for skill in found]


def _extract_certifications(text: str) -> List[str]:
    lines = text.splitlines()
    return [line.strip() for line in lines if "cert" in line.lower()][:10]


def _parse_date(token: str) -> Optional[datetime]:
    token = token.strip().lower()
    if token in {"present", "current"}:
        return datetime.now()
    for fmt in ("%b %Y", "%B %Y", "%Y"):
        try:
            return datetime.strptime(token, fmt)
        except ValueError:
            continue
    return None


def _compute_experience_years(text: str) -> Tuple[float, List[Dict[str, str]]]:
    matches = DATE_RANGE_PATTERN.findall(text)
    total_months = 0
    roles = []
    for index, match in enumerate(matches, start=1):
        start_s, end_s = match[0], match[1]
        start_dt, end_dt = _parse_date(start_s), _parse_date(end_s)
        if not start_dt or not end_dt:
            continue
        months = max(0, (end_dt.year - start_dt.year) * 12 + end_dt.month - start_dt.month)
        total_months += months
        roles.append(
            {
                "company": f"Company {index}",
                "role": f"Role {index}",
                "duration": f"{start_s} - {end_s}",
            }
        )
    return round(total_months / 12, 2), roles


def _infer_domains(text: str) -> Tuple[List[str], str, str, Dict[str, float]]:
    lowered = text.lower()
    scores: Dict[str, int] = {}
    for domain, words in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(lowered.count(word) for word in words)
    sorted_domains = [domain for domain, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score > 0]
    if not sorted_domains:
        sorted_domains = ["software"]
    primary = sorted_domains[0]
    secondary = sorted_domains[1] if len(sorted_domains) > 1 else primary
    total_points = sum(max(v, 1) for v in scores.values())
    exp_map = {domain: round((max(points, 1) / total_points) * 8, 2) for domain, points in scores.items()}
    return sorted_domains, primary.title(), secondary.title(), exp_map


def _seniority(years: float) -> str:
    if years <= 2:
        return "Entry"
    if years <= 6:
        return "Mid"
    if years <= 10:
        return "Senior"
    return "Lead"


def analyze_resume(resume_path: Path) -> ResumeAnalysis:
    logger.info(f"Analyzing resume: {resume_path}")
    text = _extract_text(resume_path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = _extract_name(lines)
    contact = _extract_contact(text)
    education = _section_lines(text, ["education", "academic"])[:10]
    years_exp, work_exp = _compute_experience_years(text)
    domains, primary, secondary, exp_map = _infer_domains(text)
    skills = _extract_skills(text)
    certifications = _extract_certifications(text)
    leadership = "Yes" if any(word in text.lower() for word in ["lead", "manager", "mentored", "managed"]) else "No"

    strengths = [
        "Strong technical foundation" if skills else "Generalist adaptability",
        f"Domain orientation in {primary}",
        "Leadership exposure" if leadership == "Yes" else "Execution-focused profile",
    ]
    gaps = [
        "Add quantified business impact bullets",
        "Enhance certifications for target roles" if not certifications else "Broaden certification depth",
    ]

    return ResumeAnalysis(
        full_name=name,
        contact_information=contact,
        education=education,
        work_experience=work_exp,
        total_years_of_experience=years_exp,
        sector_industry=[domain.title() for domain in domains],
        domain_expertise=[primary, secondary],
        technical_skills=skills,
        tools_technologies=skills,
        certifications=certifications,
        leadership_managerial_experience=leadership,
        primary_domain=primary,
        secondary_domain=secondary,
        experience_per_domain=exp_map,
        seniority_level=_seniority(years_exp),
        career_trajectory_summary=f"Profile indicates {years_exp} years with strongest orientation toward {primary} roles.",
        strengths=strengths,
        gaps=gaps,
    )
