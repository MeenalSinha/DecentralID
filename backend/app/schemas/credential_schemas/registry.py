from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

class SchemaFieldDefinition(BaseModel):
    name: str
    type: str # string, number, array, boolean, object
    required: bool
    description: str
    example: Any = None

class CredentialSchemaDefinition(BaseModel):
    schema_id: str
    name: str
    version: str
    description: str
    fields: List[SchemaFieldDefinition]

# Built-in data-driven versioned schemas
SCHEMAS: Dict[str, CredentialSchemaDefinition] = {
    "UniversityDegreeCredential": CredentialSchemaDefinition(
        schema_id="https://decentralid.org/schemas/degree-v1.json",
        name="University Degree Credential",
        version="1.0.0",
        description="Formal university bachelor, master, or doctoral degree credential.",
        fields=[
            SchemaFieldDefinition(name="studentName", type="string", required=True, description="Full legal name of the graduate"),
            SchemaFieldDefinition(name="degree", type="string", required=True, description="Degree awarded (e.g. Bachelor of Technology)"),
            SchemaFieldDefinition(name="major", type="string", required=True, description="Field of study or specialization"),
            SchemaFieldDefinition(name="institutionName", type="string", required=True, description="Accredited institution awarding the degree"),
            SchemaFieldDefinition(name="graduationDate", type="string", required=True, description="ISO-8601 graduation date (YYYY-MM-DD)"),
            SchemaFieldDefinition(name="honors", type="string", required=False, description="Academic honors or distinction"),
            SchemaFieldDefinition(name="gpa", type="number", required=False, description="Cumulative Grade Point Average"),
        ],
    ),
    "AcademicTranscriptCredential": CredentialSchemaDefinition(
        schema_id="https://decentralid.org/schemas/transcript-v1.json",
        name="Academic Transcript Credential",
        version="1.0.0",
        description="Official academic record listing completed courses and grades.",
        fields=[
            SchemaFieldDefinition(name="studentName", type="string", required=True, description="Full name of the student"),
            SchemaFieldDefinition(name="programName", type="string", required=True, description="Academic program enrolled in"),
            SchemaFieldDefinition(name="institutionName", type="string", required=True, description="Issuing educational institution"),
            SchemaFieldDefinition(name="semester", type="string", required=True, description="Academic term / semester"),
            SchemaFieldDefinition(name="courses", type="array", required=True, description="List of course codes, titles, and grades"),
            SchemaFieldDefinition(name="creditsEarned", type="number", required=True, description="Total credits earned"),
            SchemaFieldDefinition(name="cumulativeGpa", type="number", required=False, description="Cumulative GPA"),
        ],
    ),
    "CourseCompletionCertificate": CredentialSchemaDefinition(
        schema_id="https://decentralid.org/schemas/course-completion-v1.json",
        name="Course Completion Certificate",
        version="1.0.0",
        description="Certificate of completion for online or executive education courses.",
        fields=[
            SchemaFieldDefinition(name="recipientName", type="string", required=True, description="Name of the course participant"),
            SchemaFieldDefinition(name="courseName", type="string", required=True, description="Title of the completed course"),
            SchemaFieldDefinition(name="completionDate", type="string", required=True, description="Date completed (YYYY-MM-DD)"),
            SchemaFieldDefinition(name="instructor", type="string", required=True, description="Lead instructor or department"),
            SchemaFieldDefinition(name="grade", type="string", required=False, description="Performance grade or Pass"),
            SchemaFieldDefinition(name="credentialUrl", type="string", required=False, description="Digital course reference URL"),
        ],
    ),
    "ProfessionalCertification": CredentialSchemaDefinition(
        schema_id="https://decentralid.org/schemas/professional-cert-v1.json",
        name="Professional Certification",
        version="1.0.0",
        description="Industry or board certification verifying specialized professional skills.",
        fields=[
            SchemaFieldDefinition(name="candidateName", type="string", required=True, description="Certified professional name"),
            SchemaFieldDefinition(name="certificationName", type="string", required=True, description="Certification title"),
            SchemaFieldDefinition(name="issuingBody", type="string", required=True, description="Certification authority or board"),
            SchemaFieldDefinition(name="licenseNumber", type="string", required=True, description="Unique certification or license ID"),
            SchemaFieldDefinition(name="issuedDate", type="string", required=True, description="Date of award (YYYY-MM-DD)"),
            SchemaFieldDefinition(name="expirationDate", type="string", required=False, description="Expiration date if renewal required"),
        ],
    ),
    "EmploymentVerificationCredential": CredentialSchemaDefinition(
        schema_id="https://decentralid.org/schemas/employment-verification-v1.json",
        name="Employment Verification Credential",
        version="1.0.0",
        description="Verified proof of employment, tenure, and role from an employer.",
        fields=[
            SchemaFieldDefinition(name="employeeName", type="string", required=True, description="Full name of the employee"),
            SchemaFieldDefinition(name="organizationName", type="string", required=True, description="Employer organization"),
            SchemaFieldDefinition(name="jobTitle", type="string", required=True, description="Official job title or designation"),
            SchemaFieldDefinition(name="department", type="string", required=False, description="Functional department"),
            SchemaFieldDefinition(name="startDate", type="string", required=True, description="Employment start date"),
            SchemaFieldDefinition(name="endDate", type="string", required=False, description="End date, or omitted if actively employed"),
            SchemaFieldDefinition(name="employmentType", type="string", required=True, description="Full-time, Part-time, Contract, Internship"),
        ],
    ),
}

class CredentialSchemaRegistry:
    @staticmethod
    def get_schema(schema_type: str) -> Optional[CredentialSchemaDefinition]:
        return SCHEMAS.get(schema_type)

    @staticmethod
    def list_schemas() -> List[CredentialSchemaDefinition]:
        return list(SCHEMAS.values())

    @staticmethod
    def validate_claims(schema_type: str, claims: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates claim keys and types against the schema definition.
        Returns (is_valid, list_of_error_messages).
        """
        schema = SCHEMAS.get(schema_type)
        if not schema:
            return False, [f"Unknown credential schema type: '{schema_type}'"]

        errors = []
        for field in schema.fields:
            if field.required and field.name not in claims:
                errors.append(f"Missing required field: '{field.name}' ({field.description})")
            elif field.name in claims:
                val = claims[field.name]
                if field.type == "string" and not isinstance(val, str):
                    errors.append(f"Field '{field.name}' must be a string, got {type(val).__name__}")
                elif field.type == "number" and not isinstance(val, (int, float)):
                    errors.append(f"Field '{field.name}' must be a number, got {type(val).__name__}")
                elif field.type == "array" and not isinstance(val, list):
                    errors.append(f"Field '{field.name}' must be a list/array, got {type(val).__name__}")
                elif field.type == "boolean" and not isinstance(val, bool):
                    errors.append(f"Field '{field.name}' must be a boolean, got {type(val).__name__}")

        return len(errors) == 0, errors
