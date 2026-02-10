"""Statistical Analysis Service for detecting outliers and applying Pareto analysis.

This service uses the Strategy Pattern to apply various statistical algorithms
to transaction data, providing highlight metadata for visualization.
"""
from typing import Dict, List, Tuple, Optional
from enum import Enum
from whatsthedamage.models.dt_models import CellHighlight, StatisticalMetadata, DataTablesResponse, AggregatedRow, SummaryData
from whatsthedamage.services.exclusion_service import ExclusionService
from whatsthedamage.models.statistical_algorithms import (
    StatisticalAlgorithm,
    IQROutlierDetection,
    ParetoAnalysis
)

class AnalysisDirection(Enum):
    """Direction for statistical analysis.

    COLUMNS: Analyze inner keys within each outer key (e.g., categories within months)
    ROWS: Analyze outer keys within each inner key (e.g., months within categories)
    """
    COLUMNS = "columns"
    ROWS = "rows"

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
            'iqr': IQROutlierDetection(),  # type: ignore[no-untyped-call]
            'pareto': ParetoAnalysis(),  # type: ignore[no-untyped-call]
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

    def _is_cell_excluded(self, month_display: str, category: str, dt_response: DataTablesResponse, month_map: Optional[Dict[str, List[AggregatedRow]]] = None) -> bool:
        """Check if a specific cell (month, category) should be excluded.

        A cell is excluded if:
        - The row is a calculated row (e.g., Balance, Total)
        - The category is in the exclusion list

        Args:
            month_display: The month display string
            category: The category name
            dt_response: DataTablesResponse containing all rows
            month_map: Optional pre-built month to rows mapping for performance optimization

        Returns:
            True if the cell should be excluded, False otherwise
        """
        # Get excluded categories if exclusion service is available
        excluded_categories = set()
        if self._exclusion_service:
            excluded_categories = set(self._exclusion_service.get_exclusions())

        # Build or use provided month to rows mapping for quick lookup
        if month_map is None:
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
        summary: SummaryData,
        direction: AnalysisDirection
    ) -> List[Tuple[str, Dict[str, float]]]:
        """Transform summary data based on analysis direction.

        :param summary: SummaryData object containing nested dictionary structure Dict[outer_key, Dict[inner_key, amount]]
        :param direction: Analysis direction (COLUMNS or ROWS)
        :return: List of (key, data_dict) tuples for analysis
        """
        if direction == AnalysisDirection.COLUMNS:
            # Analyze inner keys within each outer key (e.g., categories within months)
            return [(outer_key, inner_data) for outer_key, inner_data in summary.summary.items()]
        else:  # ROWS
            # Analyze outer keys within each inner key (e.g., months within categories)
            # Transpose the data structure
            transposed_data: Dict[str, Dict[str, float]] = {}
            for outer_key, inner_data in summary.summary.items():
                for inner_key, amount in inner_data.items():
                    if inner_key not in transposed_data:
                        transposed_data[inner_key] = {}
                    transposed_data[inner_key][outer_key] = amount
            return [(inner_key, outer_data) for inner_key, outer_data in transposed_data.items()]


    def _build_highlight(self, row_id: str, highlight_type: str) -> CellHighlight:
        """Build a CellHighlight object based on row UUID.

        Args:
            row_id: The UUID of the row to highlight
            highlight_type: The type of highlight (e.g., 'outlier', 'pareto')

        Returns:
            CellHighlight object with row_id reference
        """
        return CellHighlight(
            row_id=row_id,
            highlight_types=[highlight_type]
        )

    def _create_highlight_for_algorithm(
        self,
        algo: StatisticalAlgorithm,
        algo_direction: AnalysisDirection,
        algo_transformed_data: List[Tuple[str, Dict[str, float]]],
        dt_response: DataTablesResponse
    ) -> List[CellHighlight]:
        """Create highlights for a single algorithm using direct row matching.

        Args:
            algo: The algorithm instance
            algo_direction: The direction to use for analysis
            algo_transformed_data: Transformed data for analysis
            dt_response: DataTablesResponse containing the actual rows with UUIDs

        Returns:
            List of CellHighlight objects with direct UUID references
        """
        highlights: List[CellHighlight] = []

        for outer_key, inner_data in algo_transformed_data:
            algo_highlights = algo.analyze(inner_data)

            for inner_key, highlight_type in algo_highlights.items():
                # Directly find the matching row in dt_response by comparing actual field values
                for agg_row in dt_response.data:
                    if algo_direction == AnalysisDirection.COLUMNS:
                        # For COLUMNS: outer_key=month, inner_key=category
                        if (agg_row.date.display == outer_key and
                            agg_row.category == inner_key):
                            highlight = self._build_highlight(agg_row.row_id, highlight_type)
                            highlights.append(highlight)
                            break
                    else:
                        # For ROWS: outer_key=category, inner_key=month
                        if (agg_row.category == outer_key and
                            agg_row.date.display == inner_key):
                            highlight = self._build_highlight(agg_row.row_id, highlight_type)
                            highlights.append(highlight)
                            break

        return highlights

    def get_highlights(
        self,
        summary: SummaryData,
        direction: AnalysisDirection = AnalysisDirection.COLUMNS,
        algorithms: List[str] | None = None,
        use_default_directions: bool = False,
        dt_response: Optional[DataTablesResponse] = None
    ) -> List[CellHighlight]:
        """Get highlights for the summary data with flexible analysis direction.

        :param summary: SummaryData object containing nested dictionary structure
                      For COLUMNS: Dict[month, Dict[category, amount]]
                      For ROWS: Dict[month, Dict[category, amount]] (will be transposed)
        :param direction: Analysis direction (COLUMNS or ROWS), default COLUMNS
        :param algorithms: Optional list of algorithm names to use (overrides enabled_algorithms)
        :param use_default_directions: If True, use each algorithm's default direction instead of the provided direction
        :param dt_response: DataTablesResponse needed for UUID lookup
        :return: List of CellHighlight
        """
        highlights: List[CellHighlight] = []
        algos_to_use = algorithms if algorithms is not None else self.enabled_algorithms

        for algo_name in algos_to_use:
            if algo_name in self.algorithms:
                algo = self.algorithms[algo_name]
                # Since algorithms no longer have preferred directions, always use the provided direction
                # Transform data for this algorithm
                algo_transformed_data = self._transform_data_for_analysis(summary, direction)
                # Create highlights for this algorithm
                if dt_response:
                    algo_highlights = self._create_highlight_for_algorithm(algo, direction, algo_transformed_data, dt_response)
                    highlights.extend(algo_highlights)

        return highlights

    def _get_excluded_cell_highlights(self, dt_response: DataTablesResponse) -> List[CellHighlight]:
        """Get highlights for cells that should be excluded from statistical analysis.

        Identifies cells that are either calculated rows or belong to excluded categories.
        Uses caching mechanism for better performance by building month map once.

        Args:
            dt_response: Original DataTablesResponse with all rows

        Returns:
            List of CellHighlight objects with type 'excluded'
        """
        excluded_highlights: List[CellHighlight] = []

        # Build month map once and reuse it for all exclusion checks
        month_map = self._build_month_to_rows_map(dt_response)

        # Iterate through all rows directly instead of extracting summary
        for agg_row in dt_response.data:
            month_display = agg_row.date.display
            category = agg_row.category

            # Check if this cell should be excluded, using pre-built month map
            if self._is_cell_excluded(month_display, category, dt_response, month_map):
                excluded_highlights.append(CellHighlight(
                    row_id=agg_row.row_id,
                    highlight_types=['excluded']
                ))

        return excluded_highlights


    def _filter_data_for_analysis(self, dt_response: DataTablesResponse) -> DataTablesResponse:
        """Filter DataTablesResponse for statistical analysis in a single pass.

        Applies all filtering criteria (calculated rows, excluded categories, expenses)
        in one iteration to improve performance and reduce object creation overhead.

        Args:
            dt_response: Original DataTablesResponse with all rows

        Returns:
            DataTablesResponse with filtered rows ready for analysis
        """
        # Pre-compute exclusions if exclusion service is available
        excluded_categories = set()
        if self._exclusion_service:
            excluded_categories = set(self._exclusion_service.get_exclusions())

        filtered_rows = []
        for row in dt_response.data:
            # Skip calculated rows
            if row.is_calculated:
                continue

            # Skip excluded categories
            if row.category in excluded_categories:
                continue

            # Skip non-expenses if filter is enabled
            if self.filter_expenses_only and float(row.total.raw) >= 0:
                continue

            filtered_rows.append(row)

        return DataTablesResponse(
            data=filtered_rows,
            account=dt_response.account,
            currency=dt_response.currency
        )

    def _extract_summary_from_response(
        self,
        dt_response: DataTablesResponse
    ) -> SummaryData:
        """Extract summary data from DataTablesResponse for statistical analysis.

        Uses the canonical SummaryData.from_datatable_response method to extract
        summary data, ensuring consistency across the codebase.

        Args:
            dt_response: DataTablesResponse containing aggregated transaction data

        Returns:
            SummaryData object containing the nested summary for analysis

        Example:
            >>> summary = service._extract_summary_from_response(dt_response)
            >>> summary.summary['January 2024']['Grocery']  # 1234.56
        """
        return SummaryData.from_datatable_response(
            dt_response=dt_response,
            include_calculated=True  # Always include calculated rows for statistical analysis
        )

    def compute_statistical_metadata(
        self,
        datatables_responses: Dict[str, DataTablesResponse],
        algorithms: List[str] | None = None,
        direction: AnalysisDirection | None = None,
        use_default_directions: bool = False
    ) -> StatisticalMetadata:
        """Compute statistical metadata including highlights for the given responses.

        Args:
            datatables_responses: Dictionary mapping account IDs to DataTablesResponse objects
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
            # Apply all filters in a single pass for better performance
            filtered_response = self._filter_data_for_analysis(dt_response)

            # Extract summary from filtered data only
            summary: SummaryData = self._extract_summary_from_response(filtered_response)

            # Get highlights with custom parameters
            table_highlights = self.get_highlights(
                summary,
                algorithms=algorithms,
                direction=analysis_direction,
                use_default_directions=use_default_directions,
                dt_response=dt_response
            )
            highlights.extend(table_highlights)

            # Add highlights for excluded cells (calculated rows and excluded categories)
            excluded_highlights = self._get_excluded_cell_highlights(dt_response)
            highlights.extend(excluded_highlights)

        return StatisticalMetadata(highlights=highlights)