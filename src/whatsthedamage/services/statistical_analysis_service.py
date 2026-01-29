"""Statistical Analysis Service for detecting outliers and applying Pareto analysis.

This service uses the Strategy Pattern to apply various statistical algorithms
to transaction data, providing highlight metadata for visualization.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats
from whatsthedamage.config.dt_models import CellHighlight, StatisticalMetadata, DataTablesResponse, AggregatedRow
from whatsthedamage.services.exclusion_service import ExclusionService

class AnalysisDirection(Enum):
    """Direction for statistical analysis.

    COLUMNS: Analyze inner keys within each outer key (e.g., categories within months)
    ROWS: Analyze outer keys within each inner key (e.g., months within categories)
    """
    COLUMNS = "columns"
    ROWS = "rows"

class StatisticalAlgorithm(ABC):
    """Abstract base class for statistical algorithms."""

    def __init__(self, direction: AnalysisDirection | None = None):
        """Initialize algorithm with optional preferred direction.

        :param direction: Preferred analysis direction (None for no preference)
        """
        self.direction = direction

    @abstractmethod
    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        """Analyze the data and return highlight metadata.

        :param data: Dictionary with keys as identifiers and values as amounts.
        :return: Dictionary with keys as identifiers and values as highlight types (e.g., 'outlier', 'pareto').
        """
        pass

class IQROutlierDetection(StatisticalAlgorithm):
    """IQR-based outlier detection algorithm."""

    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        highlights: Dict[str, str] = {}
        amounts = list(data.values())
        keys = list(data.keys())

        if not amounts:
            return highlights

        # Calculate Q1, Q3, IQR using scipy
        q1 = np.percentile(amounts, 25)
        q3 = np.percentile(amounts, 75)
        iqr = stats.iqr(amounts)  # Use scipy.stats.iqr
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for key, amount in zip(keys, amounts):
            if amount < lower_bound or amount > upper_bound:
                highlights[key] = 'outlier'

        return highlights

class ParetoAnalysis(StatisticalAlgorithm):
    """Pareto analysis for identifying top contributors."""

    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        highlights: Dict[str, str] = {}
        # Convert to list of (key, amount) tuples
        items = [(key, abs(amount)) for key, amount in data.items()]

        if not items:
            return highlights

        # Sort by amount descending
        items.sort(key=lambda x: x[1], reverse=True)

        total = sum(amount for _, amount in items)
        cumulative: float = 0.0
        for key, amount in items:
            cumulative += amount
            if cumulative < 0.8 * total:  # 80% rule - use < instead of <=
                highlights[key] = 'pareto'
            else:
                # Include the item that pushes us over 80%
                highlights[key] = 'pareto'
                break

        return highlights

class StatisticalAnalysisService:
    """Service for applying statistical algorithms to data.

    Uses Strategy Pattern for extensible algorithm selection.
    Decoupled from AppConfig - only depends on algorithm names.
    """

    def __init__(self, enabled_algorithms: List[str] | None = None, exclusion_service: Optional[ExclusionService] = None, filter_expenses_only: bool = True):
        """Initialize statistical analysis service.

        :param enabled_algorithms: List of algorithm names to enable (e.g., ['iqr', 'pareto'])
                                   If None, all algorithms are enabled.
        :param exclusion_service: Service for managing category exclusions (optional)
        :param filter_expenses_only: If True (default), only negative values (expenses) are passed to algorithms.
                                     If False, all values are passed (original behavior).
        """
        self.algorithms: Dict[str, StatisticalAlgorithm] = {
            'iqr': IQROutlierDetection(direction=AnalysisDirection.COLUMNS),
            'pareto': ParetoAnalysis(direction=AnalysisDirection.ROWS),
        }
        self.enabled_algorithms = enabled_algorithms if enabled_algorithms is not None else list(self.algorithms.keys())
        self._exclusion_service = exclusion_service
        self.filter_expenses_only = filter_expenses_only

    def _build_month_to_rows_map(self, dt_response: DataTablesResponse) -> Dict[str, List[AggregatedRow]]:
        """Build a mapping of month displays to their corresponding rows.

        Args:
            dt_response: DataTablesResponse containing aggregated rows

        Returns:
            Dictionary mapping month_display to list of AggregatedRow objects
        """
        month_map: Dict[str, List[AggregatedRow]] = {}

        for agg_row in dt_response.data:
            date_field = agg_row.date
            display = date_field.display

            if display not in month_map:
                month_map[display] = []

            month_map[display].append(agg_row)

        return month_map

    def _is_cell_excluded(self, month_display: str, category: str, dt_response: DataTablesResponse) -> bool:
        """Check if a specific cell (month, category) should be excluded.

        A cell is excluded if:
        - The row is a calculated row (e.g., Balance, Total)
        - The category is in the exclusion list

        Args:
            month_display: The month display string
            category: The category name
            dt_response: DataTablesResponse containing all rows

        Returns:
            True if the cell should be excluded, False otherwise
        """
        # Get excluded categories if exclusion service is available
        excluded_categories = set()
        if self._exclusion_service:
            excluded_categories = set(self._exclusion_service.get_exclusions())

        # Build month to rows mapping for quick lookup
        month_map = self._build_month_to_rows_map(dt_response)

        # Check if this month exists in the map
        if month_display not in month_map:
            return False

        # Find the row with matching category
        for agg_row in month_map[month_display]:
            if agg_row.category == category:
                # Cell is excluded if it's a calculated row or belongs to excluded category
                return agg_row.is_calculated or category in excluded_categories

        return False

    def _transform_data_for_analysis(
        self,
        summary: Dict[str, Dict[str, float]],
        direction: AnalysisDirection
    ) -> List[Tuple[str, Dict[str, float]]]:
        """Transform summary data based on analysis direction.

        :param summary: Nested dictionary structure Dict[outer_key, Dict[inner_key, amount]]
        :param direction: Analysis direction (COLUMNS or ROWS)
        :return: List of (key, data_dict) tuples for analysis
        """
        if direction == AnalysisDirection.COLUMNS:
            # Analyze inner keys within each outer key (e.g., categories within months)
            return [(outer_key, inner_data) for outer_key, inner_data in summary.items()]
        else:  # ROWS
            # Analyze outer keys within each inner key (e.g., months within categories)
            # Transpose the data structure
            transposed_data: Dict[str, Dict[str, float]] = {}
            for outer_key, inner_data in summary.items():
                for inner_key, amount in inner_data.items():
                    if inner_key not in transposed_data:
                        transposed_data[inner_key] = {}
                    transposed_data[inner_key][outer_key] = amount
            return [(inner_key, outer_data) for inner_key, outer_data in transposed_data.items()]

    def _get_algorithm_direction(self, algo: StatisticalAlgorithm, direction: AnalysisDirection, use_default_directions: bool) -> AnalysisDirection:
        """Determine which direction to use for an algorithm.

        Args:
            algo: The algorithm to check
            direction: The default direction parameter
            use_default_directions: Whether to use algorithm's preferred direction

        Returns:
            The direction to use for this algorithm
        """
        if algo.direction is not None and use_default_directions:
            return algo.direction
        return direction

    def _build_highlight(self, algo_direction: AnalysisDirection, outer_key: str, inner_key: str, highlight_type: str) -> CellHighlight:
        """Build a CellHighlight object based on analysis direction.

        Args:
            algo_direction: The analysis direction
            outer_key: The outer key from transformed data
            inner_key: The inner key from transformed data
            highlight_type: The type of highlight (e.g., 'outlier', 'pareto')

        Returns:
            CellHighlight object with appropriate row and column assignment
        """
        if algo_direction == AnalysisDirection.COLUMNS:
            # COLUMNS: row=inner_key, column=outer_key (e.g., row=category, column=month)
            return CellHighlight(
                row=inner_key,
                column=outer_key,
                highlight_type=highlight_type
            )
        else:  # ROWS
            # ROWS: row=outer_key, column=inner_key (e.g., row=month, column=category)
            return CellHighlight(
                row=outer_key,
                column=inner_key,
                highlight_type=highlight_type
            )

    def _create_highlight_for_algorithm(
        self,
        algo: StatisticalAlgorithm,
        algo_direction: AnalysisDirection,
        algo_transformed_data: List[Tuple[str, Dict[str, float]]]
    ) -> List[CellHighlight]:
        """Create highlights for a single algorithm.

        Args:
            algo_name: Name of the algorithm
            algo: The algorithm instance
            algo_direction: The direction to use for analysis
            algo_transformed_data: Transformed data for analysis

        Returns:
            List of CellHighlight objects
        """
        highlights: List[CellHighlight] = []

        for outer_key, inner_data in algo_transformed_data:
            algo_highlights = algo.analyze(inner_data)

            for inner_key, highlight_type in algo_highlights.items():
                highlight = self._build_highlight(algo_direction, outer_key, inner_key, highlight_type)
                highlights.append(highlight)

        return highlights

    def get_highlights(
        self,
        summary: Dict[str, Dict[str, float]],
        direction: AnalysisDirection = AnalysisDirection.COLUMNS,
        algorithms: List[str] | None = None,
        use_default_directions: bool = False
    ) -> List[CellHighlight]:
        """Get highlights for the summary data with flexible analysis direction.

        :param summary: Dict[outer_key, Dict[inner_key, amount]]
                      For COLUMNS: Dict[month, Dict[category, amount]]
                      For ROWS: Dict[month, Dict[category, amount]] (will be transposed)
        :param direction: Analysis direction (COLUMNS or ROWS), default COLUMNS
        :param algorithms: Optional list of algorithm names to use (overrides enabled_algorithms)
        :param use_default_directions: If True, use each algorithm's default direction instead of the provided direction
        :return: List of CellHighlight
        """
        highlights: List[CellHighlight] = []
        algos_to_use = algorithms if algorithms is not None else self.enabled_algorithms

        for algo_name in algos_to_use:
            if algo_name in self.algorithms:
                algo = self.algorithms[algo_name]
                # Determine direction to use for this algorithm
                algo_direction = self._get_algorithm_direction(algo, direction, use_default_directions)
                # Transform data for this algorithm
                algo_transformed_data = self._transform_data_for_analysis(summary, algo_direction)
                # Create highlights for this algorithm
                algo_highlights = self._create_highlight_for_algorithm(algo, algo_direction, algo_transformed_data)
                highlights.extend(algo_highlights)

        return highlights

    def _get_excluded_cell_highlights(self, dt_response: DataTablesResponse) -> List[CellHighlight]:
        """Get highlights for cells that should be excluded from statistical analysis.

        Identifies cells that are either calculated rows or belong to excluded categories.

        Args:
            dt_response: Original DataTablesResponse with all rows

        Returns:
            List of CellHighlight objects with type 'excluded'
        """
        excluded_highlights: List[CellHighlight] = []

        # Extract summary from original data (including calculated rows and excluded categories)
        full_summary = self._extract_summary_from_response(dt_response)

        for month_display, categories in full_summary.items():
            for category, amount in categories.items():
                # Check if this cell should be excluded
                if self._is_cell_excluded(month_display, category, dt_response):
                    excluded_highlights.append(CellHighlight(
                        row=category,
                        column=month_display,
                        highlight_type='excluded'
                    ))

        return excluded_highlights

    def _filter_calculated_rows(self, dt_response: DataTablesResponse) -> DataTablesResponse:
        """Filter out calculated rows from DataTablesResponse for statistical analysis.

        Args:
            dt_response: Original DataTablesResponse with all rows

        Returns:
            DataTablesResponse with only non-calculated rows
        """
        filtered_rows = [
            row for row in dt_response.data
            if not row.is_calculated
        ]
        return DataTablesResponse(
            data=filtered_rows,
            account=dt_response.account,
            currency=dt_response.currency
        )

    def _filter_excluded_categories(self, dt_response: DataTablesResponse) -> DataTablesResponse:
        """Filter out excluded categories from DataTablesResponse for statistical analysis.

        Args:
            dt_response: Original DataTablesResponse with all rows

        Returns:
            DataTablesResponse with excluded categories removed
        """
        if not self._exclusion_service:
            return dt_response

        # Get all exclusions (union of all algorithm exclusions)
        exclusions = self._exclusion_service.get_exclusions()

        filtered_rows = [
            row for row in dt_response.data
            if row.category not in exclusions
        ]
        return DataTablesResponse(
            data=filtered_rows,
            account=dt_response.account,
            currency=dt_response.currency
        )

    def _filter_expenses_only(self, dt_response: DataTablesResponse) -> DataTablesResponse:
        """Filter DataTablesResponse to only include expense transactions (negative amounts).

        Args:
            dt_response: Original DataTablesResponse with all rows

        Returns:
            DataTablesResponse with only expense rows (where total.raw < 0)
        """
        if not self.filter_expenses_only:
            return dt_response

        filtered_rows = [
            row for row in dt_response.data
            if float(row.total.raw) < 0
        ]
        return DataTablesResponse(
            data=filtered_rows,
            account=dt_response.account,
            currency=dt_response.currency
        )

    def _extract_summary_from_response(
        self,
        dt_response: DataTablesResponse
    ) -> Dict[str, Dict[str, float]]:
        """Extract summary data from DataTablesResponse for statistical analysis.

        Aggregates transaction data by month and category, creating a nested dictionary
        suitable for statistical analysis.

        Args:
            dt_response: DataTablesResponse containing aggregated transaction data

        Returns:
            Dict[month_display, Dict[category, amount]] - Nested summary for analysis

        Example:
            >>> summary = service._extract_summary_from_response(dt_response)
            >>> summary['January 2024']['Grocery']  # 1234.56
        """
        # Aggregate by canonical timestamp first to keep year information unambiguous
        month_map: Dict[int, Dict[str, Any]] = {}

        for agg_row in dt_response.data:
            date_field = agg_row.date

            ts = date_field.timestamp
            display = date_field.display

            if ts not in month_map:
                month_map[ts] = {'display': display, 'categories': {}}

            cats = month_map[ts]['categories']
            cats[agg_row.category] = cats.get(agg_row.category, 0.0) + float(agg_row.total.raw)

        # Handle duplicate month displays (e.g., 'January' across different years)
        # by appending timestamp if needed
        display_counts: Dict[str, int] = {}
        for v in month_map.values():
            display_counts[v['display']] = display_counts.get(v['display'], 0) + 1

        summary: Dict[str, Dict[str, float]] = {}
        # Iterate months in descending timestamp order (most recent first)
        for ts in sorted(month_map.keys(), reverse=True):
            display = month_map[ts]['display']
            key = display if display_counts.get(display, 0) == 1 else f"{display} ({ts})"
            summary[key] = month_map[ts]['categories']

        return summary

    def compute_statistical_metadata(
        self,
        datatables_responses: Dict[str, Any],
        algorithms: List[str] | None = None,
        direction: AnalysisDirection | None = None,
        use_default_directions: bool = False
    ) -> StatisticalMetadata:
        """Compute statistical metadata including highlights for the given responses.

        Args:
            datatables_responses: Dictionary of table responses
            algorithms: Optional list of algorithm names to use (if None, use enabled_algorithms)
            direction: Optional analysis direction (if None, use default behavior)
            use_default_directions: If True, use each algorithm's default direction

        Returns:
            StatisticalMetadata with highlights
        """
        highlights: List[CellHighlight] = []

        # Determine direction to use
        analysis_direction = direction if direction is not None else AnalysisDirection.COLUMNS

        for table_name, dt_response in datatables_responses.items():
            # Filter out calculated rows before analysis
            filtered_response = self._filter_calculated_rows(dt_response)

            # Apply category exclusions if exclusion service is available
            if self._exclusion_service:
                filtered_response = self._filter_excluded_categories(filtered_response)

            # Apply expense filtering if enabled
            filtered_response = self._filter_expenses_only(filtered_response)

            # Extract summary from filtered data only
            summary = self._extract_summary_from_response(filtered_response)

            # Get highlights with custom parameters
            table_highlights = self.get_highlights(
                summary,
                algorithms=algorithms,
                direction=analysis_direction,
                use_default_directions=use_default_directions
            )
            for h in table_highlights:
                highlights.append(CellHighlight(row=h.row, column=h.column, highlight_type=h.highlight_type))

            # Add highlights for excluded cells (calculated rows and excluded categories)
            excluded_highlights = self._get_excluded_cell_highlights(dt_response)
            highlights.extend(excluded_highlights)

        return StatisticalMetadata(highlights=highlights)