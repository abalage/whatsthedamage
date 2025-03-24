import tempfile
from typing import List, Dict
from whatsthedamage.models.csv_file_handler import CsvFileHandler
from whatsthedamage.models.csv_row import CsvRow


def create_sample_csv_from_fixture(csv_rows: List[CsvRow], mapping: Dict[str, str] = {}) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        sample_csv_path = temp_file.name
        writer = CsvFileHandler(sample_csv_path, mapping=mapping)
        writer.write(sample_csv_path, csv_rows)
    return sample_csv_path
