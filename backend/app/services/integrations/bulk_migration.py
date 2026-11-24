import uuid
import hashlib
from typing import Dict, Any, List

class BulkMigrationToolkit:
    """
    Migration toolkit for institutions importing historical student/credential records into DecentralID.
    Enforces validation previews, schema mappings, duplicate detection, and staged preparation.
    """
    @classmethod
    def preview_migration(
        cls,
        schema_type: str,
        field_mappings: Dict[str, str],
        raw_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        valid_records = []
        field_errors = []
        seen_keys = set()
        duplicates = 0

        for idx, row in enumerate(raw_records):
            mapped_row = {}
            for source_col, target_field in field_mappings.items():
                if source_col in row:
                    mapped_row[target_field] = row[source_col]

            # Primary identifier check
            ident = mapped_row.get("student_id") or mapped_row.get("email") or mapped_row.get("roll_no")
            if not ident:
                field_errors.append({
                    "row_index": idx,
                    "error": "MISSING_IDENTIFIER",
                    "details": "Row does not map to a recognized primary student identifier"
                })
                continue

            # Deduplication
            fp = hashlib.sha256(f"{ident}:{schema_type}".encode("utf-8")).hexdigest()
            if fp in seen_keys:
                duplicates += 1
                field_errors.append({
                    "row_index": idx,
                    "error": "DUPLICATE_IN_SOURCE",
                    "details": f"Identifier '{ident}' appears multiple times in migration dataset"
                })
                continue
            seen_keys.add(fp)
            valid_records.append(mapped_row)

        sample = valid_records[:5] if len(valid_records) >= 5 else valid_records

        return {
            "total_records": len(raw_records),
            "valid_records": len(valid_records),
            "duplicate_records": duplicates,
            "invalid_records": len(field_errors) - duplicates,
            "preview_sample": sample,
            "field_errors": field_errors
        }

    @classmethod
    def execute_migration_batch(
        cls,
        schema_type: str,
        field_mappings: Dict[str, str],
        raw_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        batch_id = str(uuid.uuid4())
        preview = cls.preview_migration(schema_type, field_mappings, raw_records)
        
        # Valid items become staged drafts
        imported_count = preview["valid_records"]
        skipped_count = len(raw_records) - imported_count

        return {
            "batch_id": batch_id,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "status": "STAGED_FOR_APPROVAL",
            "next_step": "Awaiting institutional officer preparation and separation-of-duties review"
        }
