import re
import datetime
from typing import Dict, Any, Tuple, List, Optional
from backend.app.schemas.credential_schemas.registry import CredentialSchemaRegistry

class ExtractionEngine:
    """
    Intelligent field extraction, confidence scoring, evidence reference extraction,
    and schema matching. Never invents missing data.
    """

    @classmethod
    def process_document_text(cls, raw_text: str) -> Tuple[str, Dict[str, Dict[str, Any]], float]:
        """
        Extracts candidate credential fields, computes individual confidence scores,
        determines the best schema type, and calculates overall confidence.
        """
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        lower_text = raw_text.lower()

        # 1. Determine best schema type
        degree_score = sum(1 for kw in ["degree", "bachelor", "master", "doctor", "university", "gpa", "major", "graduation"] if kw in lower_text)
        skill_score = sum(1 for kw in ["certificate", "completed", "course", "skill", "training", "credential id", "accredited"] if kw in lower_text)
        employment_score = sum(1 for kw in ["employment", "designation", "job title", "salary", "employee", "tenure", "resigned"] if kw in lower_text)

        schema_type = "UniversityDegreeCredential"
        if skill_score > degree_score and skill_score > employment_score:
            schema_type = "SkillCertificateCredential"
        elif employment_score > degree_score and employment_score > skill_score:
            schema_type = "EmploymentCredential"

        extracted_fields: Dict[str, Dict[str, Any]] = {}

        if schema_type == "UniversityDegreeCredential":
            extracted_fields = cls._extract_degree_fields(raw_text, lines)
        elif schema_type == "SkillCertificateCredential":
            extracted_fields = cls._extract_skill_fields(raw_text, lines)
        elif schema_type == "EmploymentCredential":
            extracted_fields = cls._extract_employment_fields(raw_text, lines)

        # Calculate overall confidence
        if extracted_fields:
            overall_conf = round(sum(f["confidence"] for f in extracted_fields.values()) / len(extracted_fields), 2)
        else:
            overall_conf = 0.0

        return schema_type, extracted_fields, overall_conf

    @classmethod
    def _extract_degree_fields(cls, raw_text: str, lines: List[str]) -> Dict[str, Dict[str, Any]]:
        fields: Dict[str, Dict[str, Any]] = {}

        # Student Name (restrict to same line words)
        name_match = re.search(r"(?:this is to certify that|certifies that|awarded to|name\s*[:\-])[ \t]*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,3})", raw_text, re.IGNORECASE)
        if name_match:
            val = name_match.group(1).strip()
            fields["studentName"] = {
                "value": val,
                "confidence": 0.88 if len(val.split()) >= 2 else 0.65,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        # Student ID / Roll Number
        id_match = re.search(r"(?:student\s*id|roll\s*(?:no|number)|registration\s*no)\s*[:\-]?\s*([A-Za-z0-9\-_/]+)", raw_text, re.IGNORECASE)
        if id_match:
            val = id_match.group(1).strip()
            fields["studentId"] = {
                "value": val,
                "confidence": 0.90,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        # Degree (restricted to single-line alpha tokens)
        deg_match = re.search(r"(?:degree of[ \t]+)?(bachelor of [a-zA-Z ]+?|master of [a-zA-Z ]+?|doctor of [a-zA-Z ]+?|b\.tech|m\.tech|b\.sc|m\.sc|ph\.d|bba|mba)(?:[ \t]*(?:\n|\r|\bin\b|\bwith\b|\.|$))", raw_text, re.IGNORECASE)
        if deg_match:
            val = deg_match.group(1).strip().title()
            fields["degree"] = {
                "value": val,
                "confidence": 0.92,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        # Major
        major_match = re.search(r"(?:in|major in|specialization in)\s+([A-Za-z\s]+?)(?:with|dated|at|on|\.|\n|$)", raw_text, re.IGNORECASE)
        if major_match and len(major_match.group(1).strip().split()) <= 4:
            val = major_match.group(1).strip().title()
            fields["major"] = {
                "value": val,
                "confidence": 0.82,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        # Institution Name
        inst_match = re.search(r"([A-Za-z\s]+(?:University|Institute of Technology|College of Engineering|Academy))", raw_text, re.IGNORECASE)
        if inst_match:
            val = inst_match.group(1).strip().title()
            fields["institutionName"] = {
                "value": val,
                "confidence": 0.94,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        # Graduation Date
        date_match = re.search(r"(?:dated|date of completion|conferred on|graduated on|date)\s*[:\-]?\s*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", raw_text, re.IGNORECASE)
        if date_match:
            raw_date = date_match.group(1).strip()
            norm_date = cls._normalize_date(raw_date)
            fields["graduationDate"] = {
                "value": norm_date or raw_date,
                "confidence": 0.89 if norm_date else 0.60,
                "evidence_snippet": cls._find_line_context(lines, raw_date),
                "is_valid": bool(norm_date),
                "human_corrected": False,
            }

        # GPA / Grade (normalized to numeric float where applicable per schema)
        gpa_match = re.search(r"(?:gpa|cgpa|grade)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)", raw_text, re.IGNORECASE)
        if gpa_match:
            try:
                numeric_gpa = float(gpa_match.group(1))
                fields["gpa"] = {
                    "value": numeric_gpa,
                    "confidence": 0.90,
                    "evidence_snippet": cls._find_line_context(lines, gpa_match.group(1)),
                    "is_valid": True,
                    "human_corrected": False,
                }
            except ValueError:
                pass

        return fields

    @classmethod
    def _extract_skill_fields(cls, raw_text: str, lines: List[str]) -> Dict[str, Dict[str, Any]]:
        fields: Dict[str, Dict[str, Any]] = {}

        name_match = re.search(r"(?:presented to|awarded to|certifies that)[ \t]*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,3})", raw_text, re.IGNORECASE)
        if name_match:
            val = name_match.group(1).strip()
            fields["recipientName"] = {
                "value": val,
                "confidence": 0.88,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        title_match = re.search(r"(?:certificate of completion in|successfully completed)\s*([A-Za-z0-9\s]+?)(?:course|training|program|\.|\n)", raw_text, re.IGNORECASE)
        if title_match:
            val = title_match.group(1).strip().title()
            fields["certificateTitle"] = {
                "value": val,
                "confidence": 0.85,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        cert_no_match = re.search(r"(?:certificate\s*(?:id|no|number))\s*[:\-]?\s*([A-Za-z0-9\-_]+)", raw_text, re.IGNORECASE)
        if cert_no_match:
            val = cert_no_match.group(1).strip()
            fields["certificateNumber"] = {
                "value": val,
                "confidence": 0.95,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        return fields

    @classmethod
    def _extract_employment_fields(cls, raw_text: str, lines: List[str]) -> Dict[str, Dict[str, Any]]:
        fields: Dict[str, Dict[str, Any]] = {}

        name_match = re.search(r"(?:certify that|employee|name)\s*[:\-]?[ \t]*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+){1,3})", raw_text, re.IGNORECASE)
        if name_match:
            val = name_match.group(1).strip()
            fields["employeeName"] = {
                "value": val,
                "confidence": 0.85,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        title_match = re.search(r"(?:designation|position|job title|employed as)\s*[:\-]?\s*([A-Za-z\s]+?)(?:in|at|\.|\n|$)", raw_text, re.IGNORECASE)
        if title_match and len(title_match.group(1).strip().split()) <= 4:
            val = title_match.group(1).strip().title()
            fields["jobTitle"] = {
                "value": val,
                "confidence": 0.88,
                "evidence_snippet": cls._find_line_context(lines, val),
                "is_valid": True,
                "human_corrected": False,
            }

        return fields

    @staticmethod
    def _find_line_context(lines: List[str], target: str) -> Optional[str]:
        target_lower = target.lower()
        for idx, line in enumerate(lines):
            if target_lower in line.lower():
                # Return current line plus snippet
                return line[:160]
        return None

    @staticmethod
    def _normalize_date(date_str: str) -> Optional[str]:
        # Try various date formats
        formats = [
            "%Y-%m-%d", "%Y/%m/%d",
            "%d-%m-%Y", "%d/%m/%Y",
            "%B %d, %Y", "%b %d, %Y",
            "%d %B %Y", "%d %b %Y",
        ]
        cleaned = re.sub(r"([0-9]+)(?:st|nd|rd|th)", r"\1", date_str)
        cleaned = cleaned.replace(",", " ")
        cleaned = " ".join(cleaned.split())

        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(cleaned, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None
