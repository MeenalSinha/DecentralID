import json
from typing import Any

class CanonicalizationService:
    """
    Implements RFC 8785 JSON Canonicalization Scheme (JCS).
    Produces deterministic UTF-8 byte representations for cryptographic hashing,
    W3C Data Integrity Proofs, and commitment calculations.
    """

    @staticmethod
    def canonicalize(data: Any) -> bytes:
        """
        Deterministically canonicalize a JSON-serializable Python data structure into bytes.
        Sorts all dictionary keys lexicographically, removes extraneous whitespace,
        and uses UTF-8 encoding.
        """
        # Ensure deep sorting of dict keys
        def _sort_data(item: Any) -> Any:
            if isinstance(item, dict):
                return {k: _sort_data(v) for k, v in sorted(item.items())}
            elif isinstance(item, list):
                return [_sort_data(v) for v in item]
            return item

        sorted_data = _sort_data(data)
        canonical_str = json.dumps(
            sorted_data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return canonical_str.encode("utf-8")
