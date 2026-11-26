import re
from typing import Dict, Tuple


class PIIShield:
    """
    Core regex detection and masking utilities for Personally Identifiable Information (PII).
    """

    _PHONE_REGEX = re.compile(
        r"(?:\+?91[\s.-]?)?(?:\b[6-9]\d{9}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]\d{4})"
    )

    _EMAIL_REGEX = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    )

    _CARD_REGEX = re.compile(
        r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{15,16}\b"
    )

    @classmethod
    def mask_phone(cls, text: str) -> str:
        """Partially mask phone number to 98******10."""
        if not text:
            return text

        def _repl(match: re.Match) -> str:
            raw = re.sub(r"\D", "", match.group(0))
            if len(raw) >= 10:
                return f"{raw[:2]}******{raw[-2:]}"
            return "[REDACTED_PHONE]"

        return cls._PHONE_REGEX.sub(_repl, text)

    @classmethod
    def mask_email(cls, text: str) -> str:
        """Partially mask email to j***e@domain.com."""
        if not text:
            return text

        def _repl(match: re.Match) -> str:
            email = match.group(0)
            parts = email.split("@")
            if len(parts) == 2:
                local, domain = parts
                if len(local) <= 2:
                    return f"{local[0]}***@{domain}"
                return f"{local[0]}***{local[-1]}@{domain}"
            return "[REDACTED_EMAIL]"

        return cls._EMAIL_REGEX.sub(_repl, text)

    @classmethod
    def mask_credit_card(cls, text: str) -> str:
        """Mask credit card digits to ****-****-****-1234."""
        if not text:
            return text

        def _repl(match: re.Match) -> str:
            raw = re.sub(r"\D", "", match.group(0))
            if len(raw) >= 12:
                return f"****-****-****-{raw[-4:]}"
            return "[REDACTED_CARD]"

        return cls._CARD_REGEX.sub(_repl, text)

    @classmethod
    def redact_credit_card(cls, text: str) -> str:
        """Completely redact credit card numbers."""
        if not text:
            return text
        return cls._CARD_REGEX.sub("[REDACTED_CARD]", text)

    @classmethod
    def sanitize_for_logging(cls, text: str) -> str:
        """Masks phone numbers, emails, and cards for application logs."""
        if not text:
            return text
        masked = cls.mask_credit_card(text)
        masked = cls.mask_phone(masked)
        masked = cls.mask_email(masked)
        return masked


class PIIVault:
    """
    Session-level PII Tokenization Vault:
      - Tokenizes real phone/email into anonymous tags (<PII_PHONE_1>) before sending to LLM.
      - Detokenizes tokens back to real values before saving to database.
      - Rehydrates tokens into masked format for output to user.
    """

    def __init__(self, initial_vault: Dict[str, str] = None):
        self._vault: Dict[str, str] = dict(initial_vault or {})
        self._counter = len(self._vault)

    @property
    def vault_data(self) -> Dict[str, str]:
        return self._vault

    def tokenize(self, text: str) -> str:
        """Tokenize phone and email, redact cards."""
        if not text:
            return text

        # Step 1: Immediately redact credit cards (never allowed in chat/db)
        tokenized = PIIShield.redact_credit_card(text)

        # Step 2: Tokenize phone numbers
        def _phone_repl(match: re.Match) -> str:
            val = match.group(0).strip()
            # If already tokenized, reuse existing token
            for k, v in self._vault.items():
                if v == val:
                    return k
            self._counter += 1
            token = f"<PII_PHONE_{self._counter}>"
            self._vault[token] = val
            return token

        tokenized = PIIShield._PHONE_REGEX.sub(_phone_repl, tokenized)

        # Step 3: Tokenize email addresses
        def _email_repl(match: re.Match) -> str:
            val = match.group(0).strip()
            for k, v in self._vault.items():
                if v == val:
                    return k
            self._counter += 1
            token = f"<PII_EMAIL_{self._counter}>"
            self._vault[token] = val
            return token

        tokenized = PIIShield._EMAIL_REGEX.sub(_email_repl, tokenized)
        return tokenized

    def detokenize_to_real(self, text: str) -> str:
        """Replace tokens with REAL values for database persistence."""
        if not text:
            return text
        detokenized = text
        for token, real_val in self._vault.items():
            detokenized = detokenized.replace(token, real_val)
        return detokenized

    def detokenize_to_masked(self, text: str) -> str:
        """Replace tokens with MASKED values for user output."""
        if not text:
            return text
        output = text
        for token, real_val in self._vault.items():
            if "PHONE" in token:
                masked = PIIShield.mask_phone(real_val)
            elif "EMAIL" in token:
                masked = PIIShield.mask_email(real_val)
            else:
                masked = real_val
            output = output.replace(token, masked)
        return output


# Global session registry to resolve tokens in tool executions
_GLOBAL_VAULT = PIIVault()


def get_global_pii_vault() -> PIIVault:
    return _GLOBAL_VAULT
