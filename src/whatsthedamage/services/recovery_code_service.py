"""Recovery code service for generating and managing recovery codes.

Provides generation of unique, user-friendly recovery codes that can be
used for account recovery when passwords are forgotten.
"""

import secrets
from typing import Optional


# Characters for recovery codes - excluding similar-looking characters
# (e.g., 0/O, 1/l/I, etc.)
RECOVERY_CODE_CHARACTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


class RecoveryCodeService:
    """Service for generating and managing recovery codes.

    Recovery codes are alphanumeric strings that are easy for users to
    write down and store securely. They are generated once during
    registration and displayed only once.

    Attributes:
        code_length: Length of recovery codes (default 16).
        characters: Character set for recovery codes.
    """

    def __init__(
        self,
        code_length: int = 16,
        characters: str = RECOVERY_CODE_CHARACTERS
    ):
        """Initialize RecoveryCodeService.

        Args:
            code_length: Length of recovery codes (default 16).
            characters: Character set for recovery codes (default excludes
                similar-looking characters).
        """
        self.code_length = code_length
        self.characters = characters

    def generate_code(self) -> str:
        """Generate a cryptographically secure recovery code.

        Uses secrets module for secure random selection from the
        character set.

        Returns:
            Alphanumeric recovery code string.
        """
        return ''.join(
            secrets.choice(self.characters)
            for _ in range(self.code_length)
        )

    def format_code(self, code: str) -> str:
        """Format a recovery code for display.

        Splits the code into groups of 4 characters for easier reading.

        Args:
            code: Recovery code to format.

        Returns:
            Formatted recovery code (e.g., "ABCD-EFGH-IJKL-MNOP").
        """
        return '-'.join(
            code[i:i+4] for i in range(0, len(code), 4)
        )

    def generate_and_format(self) -> str:
        """Generate and format a recovery code for display.

        Returns:
            Formatted recovery code string.
        """
        code = self.generate_code()
        return self.format_code(code)

    def parse_code(self, formatted_code: str) -> str:
        """Parse a formatted recovery code back to raw format.

        Removes any non-characterSet characters (like hyphens).

        Args:
            formatted_code: Formatted recovery code.

        Returns:
            Raw recovery code with formatting removed.
        """
        return ''.join(
            c for c in formatted_code.upper()
            if c in self.characters
        )
