import re
from typing import Dict, Tuple
from src.models import PIIEntity, PIIType

class Pseudonymizer:
    """Manages consistent mappings and generates synthetic PII replacements.

    Maintains mappings per instance to support deterministic runs.
    """

    def __init__(self) -> None:
        self.mapping: Dict[Tuple[str, PIIType], str] = {}

        # Counters for deterministic sequential generation
        self.person_counter = 0
        self.email_counter = 0
        self.phone_counter = 0
        self.org_counter = 0
        self.address_counter = 0
        self.ssn_counter = 0
        self.cc_counter = 0
        self.dob_counter = 0
        self.ip_counter = 0

        # Predefined pool of deterministic synthetic values for PERSON and ORG
        self.first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana", "Emma", "Frank"]
        self.last_names = ["Doe", "Smith", "Johnson", "Miller", "Brown", "Davis", "Wilson", "Thomas"]

        self.org_names = [
            "Example Technologies", "Acme Corporation", "Globex Industries",
            "Initech LLC", "Umbrella Corp", "Weyland-Yutani", "Cyberdyne Systems"
        ]

    def get_or_create_mapping(self, entity: PIIEntity) -> str:
        """Returns the synthetic replacement for a PIIEntity, creating it if new.

        Args:
            entity: The accepted PIIEntity candidate.

        Returns:
            The synthetic replacement string.
        """
        key = (entity.text, entity.entity_type)
        if key in self.mapping:
            return self.mapping[key]

        # Generate new replacement
        replacement = self._generate_replacement(entity)
        self.mapping[key] = replacement
        return replacement

    def pseudonymize(self, entity: PIIEntity) -> str:
        """Alias for get_or_create_mapping to support alternative API styles.

        Args:
            entity: The accepted PIIEntity candidate.

        Returns:
            The synthetic replacement string.
        """
        return self.get_or_create_mapping(entity)

    def _generate_replacement(self, entity: PIIEntity) -> str:
        """Dispatcher that selects the appropriate synthetic generator based on PIIType."""
        t = entity.entity_type
        if t == PIIType.PERSON:
            return self._generate_person()
        elif t == PIIType.EMAIL:
            return self._generate_email(entity.text)
        elif t == PIIType.PHONE:
            return self._generate_phone(entity.text)
        elif t == PIIType.ORGANIZATION:
            return self._generate_organization()
        elif t == PIIType.ADDRESS:
            return self._generate_address()
        elif t == PIIType.SSN:
            return self._generate_ssn(entity.text)
        elif t == PIIType.CREDIT_CARD:
            return self._generate_credit_card(entity.text)
        elif t == PIIType.DOB:
            return self._generate_dob(entity.text)
        elif t == PIIType.IP_ADDRESS:
            return self._generate_ip_address()
        else:
            # Fallback for any unsupported/custom PII types
            return f"[REDACTED_{t.name}]"

    def _generate_person(self) -> str:
        fn = self.first_names[self.person_counter % len(self.first_names)]
        ln = self.last_names[self.person_counter % len(self.last_names)]

        # If we loop around the pool, append the counter to ensure uniqueness
        loop_suffix = f" {self.person_counter // len(self.first_names)}" if self.person_counter >= len(self.first_names) else ""
        self.person_counter += 1
        return f"{fn} {ln}{loop_suffix}"

    def _generate_email(self, original: str) -> str:
        self.email_counter += 1
        return f"user{self.email_counter}@example.com"

    def _generate_phone(self, original: str) -> str:
        # Preserve prefix (like +91 or +1) if present in original
        prefix = ""
        if original.startswith("+"):
            match = re.match(r"^\+\d{1,3}", original)
            if match:
                prefix = match.group(0) + " "

        self.phone_counter += 1
        return f"{prefix}555-01{self.phone_counter:02d}"

    def _generate_organization(self) -> str:
        org = self.org_names[self.org_counter % len(self.org_names)]
        loop_suffix = f" {self.org_counter // len(self.org_names)}" if self.org_counter >= len(self.org_names) else ""
        self.org_counter += 1
        return f"{org}{loop_suffix}"

    def _generate_address(self) -> str:
        self.address_counter += 1
        return f"{100 + self.address_counter} Example Street, Suite {self.address_counter}"

    def _generate_ssn(self, original: str) -> str:
        self.ssn_counter += 1
        # Area number 999 is reserved and never assigned for US SSNs, making it safe and synthetic
        return f"999-00-{self.ssn_counter:04d}"

    def _generate_credit_card(self, original: str) -> str:
        self.cc_counter += 1
        index = self.cc_counter
        base = f"411122223333{index:03d}"  # 15 digits

        # Calculate Luhn checksum digit
        total = 0
        for idx, char in enumerate(reversed(base)):
            num = int(char)
            if idx % 2 == 0:
                num *= 2
                if num > 9:
                    num -= 9
            total += num
        checksum = (10 - (total % 10)) % 10
        digits = base + str(checksum)

        # Restore separators if present in original
        if "-" in original:
            return f"{digits[0:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:16]}"
        elif " " in original:
            return f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"
        else:
            return digits

    def _generate_dob(self, original: str) -> str:
        self.dob_counter += 1
        # Generate clearly synthetic dates but retain original separators
        day = f"{10 + (self.dob_counter % 15):02d}"
        month = f"{self.dob_counter % 12 + 1:02d}"
        year = "1990"

        # Retain original separator
        separator = "-"
        if "/" in original:
            separator = "/"
        elif "." in original:
            separator = "."

        return f"{day}{separator}{month}{separator}{year}"

    def _generate_ip_address(self) -> str:
        self.ip_counter += 1
        # 192.0.2.x is reserved for documentation and examples (RFC 5737)
        return f"192.0.2.{self.ip_counter % 255}"
