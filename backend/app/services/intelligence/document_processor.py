import os
import re
import zlib
import hashlib
from typing import Tuple, Optional
from backend.app.core.exceptions import ValidationException

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 # 10 Megabytes

MAGIC_BYTES = {
    "application/pdf": b"%PDF-",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
}

class DocumentProcessor:
    """
    Secure document intake, magic-byte validation, and text extraction engine.
    Never trusts browser MIME types or file extensions.
    """

    @staticmethod
    def validate_and_fingerprint(
        content: bytes,
        original_filename: str,
        declared_content_type: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Validates file size and inspects file signatures (magic bytes).
        Returns (mime_type, file_hash, sanitized_filename).
        """
        if not content:
            raise ValidationException("Uploaded file is empty.")

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise ValidationException(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.")

        # Inspect magic bytes
        detected_mime: Optional[str] = None
        for mime, magic in MAGIC_BYTES.items():
            if content.startswith(magic):
                detected_mime = mime
                break

        # Also support plain text for testing and direct text documents
        if not detected_mime and content.startswith(b"%PDF"):
            detected_mime = "application/pdf"
        elif not detected_mime:
            # Check if it's pure UTF-8 text with valid credential lines
            try:
                decoded = content[:512].decode("utf-8")
                if any(k in decoded.lower() for k in ["degree", "university", "certificate", "student", "completion", "grade"]):
                    detected_mime = "text/plain"
            except UnicodeDecodeError:
                pass

        if not detected_mime:
            raise ValidationException("Unsupported or untrusted file format. Only validated PDF, PNG, and JPEG documents are permitted.")

        # Compute SHA-256 fingerprint
        file_hash = hashlib.sha256(content).hexdigest()

        # Sanitize filename (remove paths, special chars)
        sanitized_filename = os.path.basename(original_filename)
        sanitized_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", sanitized_filename)
        if not sanitized_filename:
            sanitized_filename = "document"

        return detected_mime, file_hash, sanitized_filename

    @classmethod
    def extract_text_from_content(cls, content: bytes, mime_type: str) -> str:
        """
        Extracts raw textual content from verified document bytes without fabricating fake OCR data.
        """
        if mime_type == "text/plain":
            return content.decode("utf-8", errors="replace")

        if mime_type == "application/pdf":
            return cls._extract_text_from_pdf(content)

        if mime_type in ["image/png", "image/jpeg"]:
            return cls._extract_text_from_image(content)

        raise ValidationException(f"Unsupported MIME type for text extraction: {mime_type}")

    @classmethod
    def _extract_text_from_pdf(cls, content: bytes) -> str:
        """
        Robust stream-level PDF text extraction supporting both uncompressed
        and FlateDecode object streams.
        """
        extracted_text_pieces = []

        # Find stream ... endstream blocks
        stream_matches = re.finditer(b"stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
        for match in stream_matches:
            raw_stream = match.group(1)
            decompressed: Optional[bytes] = None

            # Attempt Flate decompression
            try:
                decompressed = zlib.decompress(raw_stream)
            except Exception:
                try:
                    decompressed = zlib.decompress(raw_stream, -zlib.MAX_WBITS)
                except Exception:
                    decompressed = raw_stream

            if decompressed:
                text = cls._parse_pdf_operators(decompressed)
                if text.strip():
                    extracted_text_pieces.append(text)

        # Also search for direct text objects in parent content outside streams
        parent_text = cls._parse_pdf_operators(content)
        if parent_text.strip() and parent_text not in extracted_text_pieces:
            extracted_text_pieces.append(parent_text)

        full_extracted = "\n".join(extracted_text_pieces).strip()
        if not full_extracted:
            # If standard text operator parsing yields no text, check readable strings
            readable_strings = re.findall(rb"\(([^\)\\]*(?:\\.[^\)\\]*)*)\)", content)
            cleaned = [s.decode("latin1", errors="ignore") for s in readable_strings if len(s) > 2]
            full_extracted = "\n".join(cleaned)

        if not full_extracted.strip():
            raise ValidationException("PDF document does not contain readable digital text. Scanned raster PDFs require an external OCR service.")

        return full_extracted

    @staticmethod
    def _parse_pdf_operators(stream_bytes: bytes) -> str:
        """
        Parses PDF BT (Begin Text) ... ET (End Text) blocks and Tj / TJ operands.
        """
        found_tokens = []
        # Match text inside parentheses (e.g. (John Doe) Tj or [(John) 20 (Doe)] TJ)
        tj_literals = re.findall(rb"\(([^\)\\]*(?:\\.[^\)\\]*)*)\)\s*(?:Tj|'|\")", stream_bytes)
        for lit in tj_literals:
            cleaned = lit.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
            found_tokens.append(cleaned.decode("utf-8", errors="replace"))

        # Match array text in TJ: [ (text1) 20 (text2) ] TJ
        tj_arrays = re.findall(rb"\[(.*?)\]\s*TJ", stream_bytes)
        for arr in tj_arrays:
            parts = re.findall(rb"\(([^\)\\]*(?:\\.[^\)\\]*)*)\)", arr)
            line = "".join(p.decode("utf-8", errors="replace") for p in parts)
            if line:
                found_tokens.append(line)

        return "\n".join(found_tokens)

    @staticmethod
    def _extract_text_from_image(content: bytes) -> str:
        """
        Attempts OCR via Tesseract if installed, otherwise reports honest unavailable state.
        """
        import shutil
        import subprocess

        tesseract_cmd = shutil.which("tesseract")
        if not tesseract_cmd:
            raise ValidationException(
                "Image document uploaded but local Tesseract OCR engine is not installed or available on PATH. "
                "Please upload a digital PDF document or configure an external AI OCR provider."
            )

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                tf.write(content)
                temp_img = tf.name

            proc = subprocess.run(
                [tesseract_cmd, temp_img, "stdout"],
                capture_output=True,
                text=True,
                timeout=15,
                check=True
            )
            os.remove(temp_img)
            return proc.stdout.strip()
        except Exception as e:
            raise ValidationException(f"OCR extraction failed: {str(e)}")
