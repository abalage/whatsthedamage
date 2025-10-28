from html.parser import HTMLParser
from typing import List, Tuple, Optional

class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.reset_parser()

    def reset_parser(self) -> None:
        """Reset parser state for reuse"""
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self.current_row: List[str] = []
        self.current_text: str = ""
        self.in_header: bool = False
        self.in_cell: bool = False
        self.in_thead: bool = False
        self.in_tbody: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == 'thead':
            self.in_thead = True
        elif tag == 'tbody':
            self.in_tbody = True
        elif tag == 'th':
            if self.in_thead:
                self.in_header = True
            elif self.in_tbody:
                # Handle index column (Categories) which uses <th> in tbody
                self.in_cell = True
            self.current_text = ""
        elif tag == 'td' and self.in_tbody:
            self.in_cell = True
            self.current_text = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == 'thead':
            self.in_thead = False
        elif tag == 'tbody':
            self.in_tbody = False
        elif tag == 'th':
            if self.in_header:
                self.headers.append(self.current_text.strip())
                self.in_header = False
            elif self.in_cell and self.in_tbody:
                # Handle index column (Categories) values
                self.current_row.append(self.current_text.strip())
                self.in_cell = False
        elif tag == 'td' and self.in_cell:
            self.current_row.append(self.current_text.strip())
            self.in_cell = False
        elif tag == 'tr':
            if self.in_tbody and self.current_row:
                self.rows.append(self.current_row)
                self.current_row = []

    def handle_data(self, data: str) -> None:
        if self.in_header or self.in_cell:
            self.current_text += data

    def parse_table(self, html_content: str) -> Tuple[List[str], List[List[str]]]:
        """Parse HTML table content and return headers and rows"""
        self.reset_parser()  # Reset state before parsing
        self.feed(html_content)
        return self.headers, self.rows
