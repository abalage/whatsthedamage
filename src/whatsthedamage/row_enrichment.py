import re
from whatsthedamage.csv_row import CsvRow


class RowEnrichment:
    def __init__(self, rows: list['CsvRow'], pattern_sets: dict[str, dict[str, list[str]]]):
        """
        Initialize the RowEnrichment with a list of CsvRow objects.

        :param rows: list of CsvRow objects to categorize.
        :param pattern_sets: dict: dictionaries of 'attribute names' -> 'category names' -> 'lists of regex patterns'.
        """
        self.rows = rows
        self.pattern_sets = pattern_sets
        self.categorized: dict[str, list['CsvRow']] = {"other": []}

    def initialize(self) -> None:
        """
        Init method to call add_category_attribute with the given attribute name and category patterns.
        """
        for attribute_name, category_patterns in self.pattern_sets.items():
            # Fill up categorized with empty lists for each category
            # to make sure that all categories are present in the dictionary
            for category in category_patterns.keys():
                if category not in self.categorized:
                    self.categorized[category] = []
            self.add_category_attribute(attribute_name, category_patterns)

    def add_category_attribute(self, attribute_name: str, category_patterns: dict[str, list[str]]) -> None:
        """
        Add category attributes to CsvRow objects based on a specified attribute matching a set of patterns.

        :param attribute_name: str: The name of the attribute to check for categorization.
        :param category_patterns: dict[str, list[str]]: 'category names' -> 'lists of regex patterns'.
        """
        for row in self.rows:
            # Check if the category is not set or is 'other'
            current_category = getattr(row, 'category', None)
            if current_category is not None and current_category != 'other':
                continue

            attribute_value = getattr(row, attribute_name, None)
            if not attribute_value:
                setattr(row, 'category', 'other')  # Default to 'other' if no match
                continue

            matched = False
            compiled_patterns = {
                category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
                for category, patterns in category_patterns.items()
            }
            for category, patterns in compiled_patterns.items():
                for pattern in patterns:
                    if pattern.search(attribute_value):
                        setattr(row, 'category', category)  # Add attribute with category name
                        matched = True
                        break
                if matched:
                    break

            if not matched:
                # catch any not matched possible deposits
                amount_value = getattr(row, 'amount', None)
                if amount_value is not None and int(amount_value) > 0:
                    setattr(row, 'category', 'deposits')
                    continue
                setattr(row, 'category', 'other')  # Default to 'other' if no match

    def categorize_by_attribute(self, attribute_name: str) -> dict[str, list['CsvRow']]:
        """
        Categorize CsvRow objects based on a specified attribute.

        :param attribute_name: The name of the attribute to categorize by.
        :return: A dictionary where keys are attribute values and values are lists of CsvRow objects.
        """
        for row in self.rows:
            # Get the value of the specified attribute
            attribute_value = getattr(row, attribute_name, None)
            if attribute_value is not None:
                if attribute_value not in self.categorized:
                    self.categorized[attribute_value] = []
                self.categorized[attribute_value].append(row)
        return self.categorized
