import re
import unicodedata

def clean_text(text: str) -> str:

    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Hyphenation correction
    # Example:
    # intelli-
    # gence -> intelligence
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Removing page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Extra spaces/tabs removal
    text = re.sub(r"[ \t]+", " ", text)

    # Excessive new lines removal
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Removing
    # Remove OCR spacing artifacts
    text = re.sub(r"[^\S\r\n]+", " ", text)

    # Strip leading/trailing spaces
    text = text.strip()

    return text