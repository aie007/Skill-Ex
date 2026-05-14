import re
import spacy
from typing import List

class PIIMasker:
    """Responsibility: Identify and redact PII (Names, Emails, Phone) using NLP (spaCy)."""
    
    # Load spaCy model (ensure en_core_web_sm is installed)
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        # Fallback to empty nlp if model missing (should not happen in this env)
        nlp = None

    # Regex for obvious patterns that NLP might miss or to supplement it
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
    LINK_PATTERN = re.compile(r'\b(?:github\.com|linkedin\.com/in)/[^\s]+\b', re.IGNORECASE)

    @classmethod
    def mask(cls, text: str) -> str:
        if not text:
            return ""
        
        # 1. Regex masking for deterministic patterns
        text = cls.EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
        text = cls.PHONE_PATTERN.sub("[PHONE REDACTED]", text)
        text = cls.LINK_PATTERN.sub("[LINK REDACTED]", text)

        # 2. NLP-based masking for Names and Locations
        if cls.nlp:
            doc = cls.nlp(text)
            # Create a list of spans to redact
            spans_to_redact = []
            for ent in doc.ents:
                # PERSON: People, including fictional.
                # GPE: Countries, cities, states.
                # ORG: Companies, agencies, institutions, etc. (Optional, can be aggressive)
                if ent.label_ in ("PERSON", "GPE"):
                    spans_to_redact.append((ent.start_char, ent.end_char, ent.label_))
            
            # Replace spans from back to front to avoid index shifting
            masked_text = list(text)
            for start, end, label in sorted(spans_to_redact, reverse=True):
                masked_text[start:end] = f"[{label} REDACTED]"
            
            return "".join(masked_text)
        
        return text
