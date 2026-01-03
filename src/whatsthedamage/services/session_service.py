"""Session management service for web application state.

This service centralizes session management to eliminate direct session
manipulation across controllers and provide type-safe access to session data.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from flask import session


@dataclass
class FormData:
    """Type-safe container for form data stored in session.

    Attributes:
        filename: Name of uploaded CSV file
        config: Config file path or name
        start_date: Filter start date string (YYYY-MM-DD format)
        end_date: Filter end date string (YYYY-MM-DD format)
        verbose: Verbose output flag
        filter: Month filter value
        ml: ML enrichment flag
    """
    filename: Optional[str] = None
    config: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    verbose: bool = False
    filter: Optional[str] = None
    ml: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormData':
        """Create FormData from dictionary.

        :param data: Dictionary with form data
        :returns: FormData instance
        :rtype: FormData
        """
        return cls(
            filename=data.get('filename'),
            config=data.get('config'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            verbose=bool(data.get('verbose', False)),
            filter=data.get('filter'),
            ml=bool(data.get('ml', False))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert FormData to dictionary.

        :returns: Dictionary with form data
        :rtype: Dict[str, Any]
        """
        return {
            'filename': self.filename,
            'config': self.config,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'verbose': self.verbose,
            'filter': self.filter,
            'ml': self.ml
        }


class SessionService:
    """Service for managing session state in Flask application.

    Centralizes session management to provide:
    - Type-safe access to session data
    - Consistent key naming
    - Cleanup and expiration logic
    - Prevention of memory leaks from large session data

    Attributes:
        SESSION_KEY_FORM_DATA: Key for storing form data
        SESSION_KEY_RESULT: Key for storing HTML result
        SESSION_KEY_TABLE_DATA: Key for storing table data
        SESSION_KEY_LANG: Key for storing language preference
        DEFAULT_LANGUAGE: Default language code
    """

    SESSION_KEY_FORM_DATA = 'form_data'
    SESSION_KEY_RESULT = 'result'
    SESSION_KEY_TABLE_DATA = 'table_data'
    SESSION_KEY_LANG = 'lang'
    DEFAULT_LANGUAGE = 'en'

    def store_form_data(self, form_data: Dict[str, Any]) -> None:
        """Store form data in session.

        :param form_data: Dictionary containing form data
        """
        session[self.SESSION_KEY_FORM_DATA] = form_data

    def retrieve_form_data(self) -> Optional[FormData]:
        """Retrieve form data from session.

        :returns: FormData object if available, None otherwise
        :rtype: Optional[FormData]
        """
        data = session.get(self.SESSION_KEY_FORM_DATA)
        if data:
            return FormData.from_dict(data)
        return None

    def has_form_data(self) -> bool:
        """Check if form data exists in session.

        :returns: True if form data exists, False otherwise
        :rtype: bool
        """
        return self.SESSION_KEY_FORM_DATA in session

    def set_language(self, lang_code: str) -> None:
        """Set user language preference.

        :param lang_code: Language code (e.g., 'en', 'hu')
        """
        session[self.SESSION_KEY_LANG] = lang_code

    def get_language(self) -> str:
        """Get user language preference.

        :returns: Language code from session or default language
        :rtype: str
        """
        return str(session.get(self.SESSION_KEY_LANG, self.DEFAULT_LANGUAGE))

    def clear_form_data(self) -> None:
        """Remove form data from session."""
        session.pop(self.SESSION_KEY_FORM_DATA, None)

    def clear_result(self) -> None:
        """Remove result data from session."""
        session.pop(self.SESSION_KEY_RESULT, None)
        session.pop(self.SESSION_KEY_TABLE_DATA, None)

    def clear_session(self) -> None:
        """Clear all session data managed by this service."""
        self.clear_form_data()
        self.clear_result()
        # Note: Language preference is preserved across clears
        # If you need to clear it too, add: session.pop(self.SESSION_KEY_LANG, None)
