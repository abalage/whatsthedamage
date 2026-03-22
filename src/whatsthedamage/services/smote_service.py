# src/whatsthedamage/services/smote_service.py
"""SMOTE Service for handling synthetic data generation and oversampling operations."""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer

from whatsthedamage.config.ml_config import MLConfig
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)


class SmoteService:
    """Service class for SMOTE operations following service layer pattern.

    This service handles all SMOTE-related business logic, including parameter calculation,
    safety checks, and synthetic data generation, following the separation of concerns principle.
    """

    def __init__(self, config: MLConfig):
        """Initialize SMOTE service with configuration.

        Args:
            config: ML configuration containing SMOTE parameters
        """
        self._config = config

    def calculate_parameters(self, y: pd.Series, rare_categories: List[str]) -> Tuple[int, Dict[str, int]]:
        """Calculate SMOTE parameters based on class distribution.

        This is a pure calculation method with no side effects, following the
        separation of concerns principle.

        Args:
            y: Target labels
            rare_categories: Categories identified as rare

        Returns:
            Tuple of (effective_k, sampling_strategy)
        """
        class_counts = y.value_counts()
        min_class_size = min(class_counts[cat] for cat in rare_categories if cat in class_counts.index)

        # Calculate effective k_neighbors
        effective_k = min(self._config.smote_k_neighbors, max(1, min_class_size - 1))

        # Calculate sampling strategy
        sampling_strategy = {}
        majority_size = class_counts.max()

        for cat in rare_categories:
            original_count = class_counts[cat]
            target_size = min(
                original_count * self._config.smote_oversampling_factor,
                majority_size * self._config.smote_majority_size_limit
            )
            if target_size > original_count:
                sampling_strategy[cat] = int(target_size)

        return effective_k, sampling_strategy

    def should_apply_smote(self, X: pd.DataFrame, y: pd.Series, rare_categories: List[str],
                          effective_k: int, sampling_strategy: Dict[str, int]) -> bool:
        """Determine if SMOTE should be applied based on all conditions.

        Centralizes all decision logic in one place following DRY principle.

        Args:
            X: Feature DataFrame
            y: Target labels
            rare_categories: Rare categories identified
            effective_k: Calculated k_neighbors value
            sampling_strategy: Calculated sampling strategy

        Returns:
            True if SMOTE should be applied, False otherwise
        """
        # Check if we have rare categories to process
        if not rare_categories:
            logger.info("No rare categories found for SMOTE oversampling")
            return False

        # Check if k_neighbors is valid
        if effective_k < 1:
            class_counts = y.value_counts()
            min_class_size = min(class_counts[cat] for cat in rare_categories if cat in class_counts.index)
            logger.warning(f"Cannot apply SMOTE: smallest class has only {min_class_size} samples, need at least 2")
            return False

        # Check if we need oversampling
        if not sampling_strategy:
            logger.info("No oversampling needed - rare categories have sufficient samples")
            return False

        return self._apply_safety_checks(X, y, rare_categories)

    def _apply_safety_checks(self, X: pd.DataFrame, y: pd.Series, rare_categories: List[str]) -> bool:
        """Check if SMOTE should be applied based on safety conditions.

        Separates validation logic as a distinct concern.

        Args:
            X: Feature DataFrame
            y: Target labels
            rare_categories: Rare categories identified

        Returns:
            True if safe to apply SMOTE, False otherwise
        """
        if len(X) < 10:
            logger.warning(f"Skipping SMOTE: only {len(X)} training samples - too few for meaningful synthesis")
            return False

        if len(rare_categories) == len(y.unique()):
            logger.warning("Skipping SMOTE: all categories are rare - high overfitting risk")
            return False

        return True

    def create_synthetic_samples(self, X: pd.DataFrame, X_resampled: np.ndarray) -> pd.DataFrame:
        """Create synthetic DataFrame from SMOTE results with variations.

        Separates the data transformation concern from business logic.

        Args:
            X: Original feature DataFrame
            X_resampled: SMOTE-processed feature array

        Returns:
            Combined DataFrame with original and synthetic samples
        """
        original_indices = X.index.tolist()
        num_original = len(X)
        num_synthetic = X_resampled.shape[0] - num_original

        synthetic_data = []
        for i in range(num_synthetic):
            original_idx = original_indices[i % num_original]
            original_row = X.loc[original_idx]

            synthetic_row = {
                'type': f"{original_row['type']}_syn{i}",  # Unique identifier
                'partner': f"{original_row['partner']}_v{i % 3}",  # Limited variation
                'amount': original_row['amount'] * (1 + (i % 7) * 0.02 - 0.06)  # Small random variation
            }
            synthetic_data.append(synthetic_row)

        synthetic_df = pd.DataFrame(synthetic_data, index=range(num_original, num_original + num_synthetic))
        return pd.concat([X, synthetic_df])

    def apply_smote(self, X: pd.DataFrame, y: pd.Series, preprocessor: ColumnTransformer,
                   rare_categories: List[str]) -> Tuple[pd.DataFrame, pd.Series]:
        """Apply SMOTE with full workflow.

        Orchestrates the complete SMOTE process by delegating to specialized methods.

        Args:
            X: Feature DataFrame
            y: Target labels
            preprocessor: ColumnTransformer for feature preprocessing
            rare_categories: Categories identified as rare

        Returns:
            Tuple of (processed_features, resampled_labels)
        """
        from imblearn.over_sampling import SMOTE

        # Calculate parameters
        effective_k, sampling_strategy = self.calculate_parameters(y, rare_categories)

        # Determine if SMOTE should be applied
        if not self.should_apply_smote(X, y, rare_categories, effective_k, sampling_strategy):
            return X, y

        logger.info(f"Applying SMOTE to rare categories: {rare_categories}")
        logger.info(f"Using k_neighbors={effective_k} for SMOTE")
        logger.info(f"SMOTE sampling strategy: {sampling_strategy}")

        # Preprocess features
        preprocessed_X = preprocessor.fit_transform(X)

        # Apply SMOTE
        smote = SMOTE(
            random_state=self._config.smote_random_state,
            k_neighbors=effective_k,
            sampling_strategy=sampling_strategy
        )
        X_resampled, y_resampled = smote.fit_resample(preprocessed_X, y)

        logger.info(f"SMOTE generated {X_resampled.shape[0] - preprocessed_X.shape[0]} synthetic samples")
        logger.info(f"Class distribution after SMOTE: {dict(pd.Series(y_resampled).value_counts())}")

        # Create synthetic DataFrame
        X_resampled_df = self.create_synthetic_samples(X, X_resampled)

        return X_resampled_df, y_resampled