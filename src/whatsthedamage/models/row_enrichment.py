import re
from typing import List, Dict
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.config import EnricherPatternSets, get_category_name


class RowEnrichment:
    def __init__(self, rows: List[CsvRow], pattern_sets: EnricherPatternSets):
        """
        Initialize the RowEnrichment with a list of CsvRow objects.

        :param rows: List of CsvRow objects to categorize.
        :param pattern_sets: Dict of 'attribute names' -> 'category names' -> 'lists of regex patterns'.
        """
        self.rows = rows
        self.pattern_sets = pattern_sets
        self.categorized: Dict[str, List[CsvRow]] = {get_category_name('other'): []}

    def initialize(self) -> None:
        """
        Initialize the categorization process by calling add_category_attribute for each attribute.
        """
        # Convert the Pydantic model to a dictionary
        pattern_sets_dict = self.pattern_sets.model_dump()

        for attribute_name, category_patterns in pattern_sets_dict.items():
            # Ensure all categories are present in the categorized dictionary
            for category in category_patterns.keys():
                localized_category = get_category_name(category)
                if localized_category not in self.categorized:
                    self.categorized[localized_category] = []
            self.add_category_attribute(attribute_name, category_patterns)

    def add_category_attribute(self, attribute_name: str, category_patterns: Dict[str, List[str]]) -> None:
        """
        Add category attributes to CsvRow objects based on a specified attribute matching a set of patterns.

        :param attribute_name: The name of the attribute to check for categorization.
        :param category_patterns: Dict of 'category names' -> 'lists of regex patterns'.
        """
        compiled_patterns = self._compile_patterns(category_patterns)

        for row in self.rows:
            if self._is_category_set(row):
                continue

            attribute_value = getattr(row, attribute_name, None)
            if not attribute_value:
                self._set_category(row, get_category_name('other'))
                continue

            if not self._match_patterns(row, attribute_value, compiled_patterns):
                self._categorize_as_deposits(row)

    def _compile_patterns(self, category_patterns: Dict[str, List[str]]) -> Dict[str, List[re.Pattern[str]]]:
        """
        Compile regex patterns for each category.

        :param category_patterns: Dict of 'category names' -> 'lists of regex patterns'.
        :return: Dict of 'category names' -> 'lists of compiled regex patterns'.
        """
        return {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in category_patterns.items()
        }

    def _is_category_set(self, row: CsvRow) -> bool:
        """
        Check if the category is already set and not 'other'.

        :param row: CsvRow object to check.
        :return: True if the category is set and not 'other', False otherwise.
        """
        current_category = getattr(row, 'category', None)
        return current_category is not None and current_category != get_category_name('other')

    def _set_category(self, row: CsvRow, category: str) -> None:
        """
        Set the category of a CsvRow object.

        :param row: CsvRow object to categorize.
        :param category: The category to set.
        """
        # Only localize if not already localized
        if category not in self.categorized:
            localized_name = get_category_name(category)
        else:
            localized_name = category
        setattr(row, 'category', localized_name)

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
        :param compiled_patterns: Compiled regex patterns for each category.
        :return: True if a match is found, False otherwise.
        """
        for category, patterns in compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(attribute_value):
                    self._set_category(row, category)
                    return True
        return False

    def _categorize_as_deposits(self, row: CsvRow) -> None:
        """
        Categorize a CsvRow object as 'deposit' if the 'amount' attribute is positive.

        :param row: CsvRow object to categorize.
        """
        amount_value = getattr(row, 'amount', None)
        if amount_value is not None and int(amount_value) > 0:
            self._set_category(row, get_category_name('deposit'))
        else:
            self._set_category(row, get_category_name('other'))

    def categorize_by_attribute(self, attribute_name: str) -> Dict[str, List[CsvRow]]:
        """
        Categorize CsvRow objects based on a specified attribute.

        :param attribute_name: The name of the attribute to categorize by.
        :return: A dictionary where keys are attribute values and values are lists of CsvRow objects.
        """
        for row in self.rows:
            attribute_value = getattr(row, attribute_name, None)
            if attribute_value is not None:
                if attribute_value not in self.categorized:
                    self.categorized[attribute_value] = []
                self.categorized[attribute_value].append(row)
        return self.categorized
