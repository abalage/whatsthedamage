import re
from typing import List, Dict
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.config.config import EnricherPatternSets


class RowEnrichment:
    def __init__(self, rows: List[CsvRow], pattern_sets: EnricherPatternSets):
        """
        Initialize the RowEnrichment with a list of CsvRow objects.

        :param rows: List of CsvRow objects to categorize.
        :param pattern_sets: Dict of 'attribute names' -> 'category IDs' -> 'lists of regex patterns'.
        """
        self.rows = rows
        self.pattern_sets = pattern_sets
        self.categorized: Dict[str, List[CsvRow]] = {"other": []}

        # Convert the Pydantic model to a dictionary
        pattern_sets_dict = self.pattern_sets.model_dump()

        for attribute_name, category_patterns in pattern_sets_dict.items():
            # Skip empty pattern sets
            if not category_patterns:
                continue
            # Ensure all categories are present in the categorized dictionary
            for category_id in category_patterns.keys():
                if category_id not in self.categorized:
                    self.categorized[category_id] = []
            self.add_category_attribute(attribute_name, category_patterns)

    def add_category_attribute(self, attribute_name: str, category_patterns: Dict[str, List[str]]) -> None:
        """
        Add category attributes to CsvRow objects based on a specified attribute matching a set of patterns.

        :param attribute_name: The name of the attribute to check for categorization.
        :param category_patterns: Dict of 'category IDs' -> 'lists of regex patterns'.
        """
        compiled_patterns = self._compile_patterns(category_patterns)

        for row in self.rows:
            if self._is_category_set(row):
                continue

            attribute_value = getattr(row, attribute_name, None)
            if not attribute_value:
                if attribute_name == 'type':
                    row.type = 'card_reservation'
                row.category_id = "other"
                continue

            if not self._match_patterns(row, attribute_value, compiled_patterns):
                self._categorize_as_deposits(row)

    def _compile_patterns(self, category_patterns: Dict[str, List[str]]) -> Dict[str, List[re.Pattern[str]]]:
        """
        Compile regex patterns for each category.

        :param category_patterns: Dict of 'category IDs' -> 'lists of regex patterns'.
        :return: Dict of 'category IDs' -> 'lists of compiled regex patterns'.
        """
        return {
            category_id: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category_id, patterns in category_patterns.items()
        }

    def _is_category_set(self, row: CsvRow) -> bool:
        """
        Check if the category is already set and not 'other'.

        :param row: CsvRow object to check.
        :return: True if the category is set and not 'other', False otherwise.
        """
        current_category = getattr(row, 'category_id', None)
        return current_category not in (None, "", "other")

    def _set_category(self, row: CsvRow, category_id: str) -> None:
        """
        Set the category of a CsvRow object.

        :param row: CsvRow object to categorize.
        :param category_id: The category ID to set (e.g., 'grocery', 'other').
        """
        # Ensure category_id is stored in the categorized dict
        if category_id not in self.categorized:
            self.categorized[category_id] = []
        row.category_id = category_id

    def _match_patterns(
        self,
        row: 'CsvRow',
        attribute_value: str,
        compiled_patterns: dict[str, list[re.Pattern[str]]]
    ) -> bool:
        """
        Match the attribute value against compiled patterns and set the category if a match is found.

        :param row: CsvRow object to categorize.
        :param attribute_value: The value of the attribute to match.
        :param compiled_patterns: Compiled regex patterns for each category ID.
        :return: True if a match is found, False otherwise.
        """
        for category_id, patterns in compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(attribute_value):
                    self._set_category(row, category_id)
                    return True
        return False

    def _categorize_as_deposits(self, row: CsvRow) -> None:
        """
        Categorize a CsvRow object as 'deposit' if the 'amount' attribute is positive.

        :param row: CsvRow object to categorize.
        """
        amount_value = getattr(row, 'amount', None)
        if amount_value is not None and int(amount_value) > 0:
            self._set_category(row, "deposit")
        else:
            self._set_category(row, "other")

    def categorize_by_attribute(self, attribute_name: str) -> Dict[str, List[CsvRow]]:
        """
        Categorize CsvRow objects based on a specified attribute.

        :param attribute_name: The name of the attribute to categorize by (e.g., 'type').
        :return: A dictionary where keys are category IDs and values are lists of CsvRow objects.
        """
        # First, enrich rows with categories based on pattern matching
        for attribute_name_to_check, category_patterns in self.pattern_sets.model_dump().items():
            self.add_category_attribute(attribute_name_to_check, category_patterns)
        
        # Group already-categorized rows by category_id
        result: Dict[str, List[CsvRow]] = {}
        for row in self.rows:
            category_id = getattr(row, 'category_id', None)
            if category_id:
                if category_id not in result:
                    result[category_id] = []
                result[category_id].append(row)
        
        # Ensure all known categories are present, even if empty
        for category_id in self.categorized.keys():
            if category_id not in result:
                result[category_id] = []
        
        return result
