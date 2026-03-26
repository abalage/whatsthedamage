# src/whatsthedamage/config/ml_config.py
from typing import List, Union, Optional
from pydantic import BaseModel
import os

class MLConfig(BaseModel):
    hungarian_type_stop_words: List[str] = [
        "ft", "forint", "bol"
    ]
    hungarian_partner_stop_words: List[str] = [
        "es", "bt", "kft", "zrt", "rt", "nyrt", "ev", "korlatolt", "felelossegu",
        "tarsasag", "alapitvany", "kisker", "szolgaltato", "kereskedelmi",
        "kereskedes", "sz", "u.", "utca", "ut", "&", "huf", "otpmobl", "paypal",
        "crv", "sumup", "www", "toltoall"
    ]
    classifier_short_name: str = "rf"
    classifier_imbalance_threshold: float = 0.2
    random_state: int = 42
    min_samples_split: int = 10
    n_estimators: int = 200
    max_depth: Union[int, None] = None
    n_jobs: int = 1 # Number of jobs for parallel processing (-1 = use all cores)
    test_size: float = 0.2
    model_version: str = "v6alpha_en"
    feature_columns: List[str] = ["type", "partner", "amount"]
    # Confidence calibration settings
    enable_calibration: bool = True
    calibration_method: str = "sigmoid"  # Options: 'sigmoid', 'isotonic'
    calibration_cv: int = 3  # Number of folds for calibration cross-validation
    # SMOTE settings for synthetic data generation
    enable_smote: bool = False
    smote_random_state: int = 42
    smote_k_neighbors: int = 5
    smote_oversampling_factor: int = 3
    smote_majority_size_limit: float = 0.8
    smote_target_categories: Optional[List[str]] = None  # Specific categories to oversample
    smote_min_samples_threshold: int = 150  # Categories with fewer samples get SMOTE
    # Confidence threshold for ML categorization
    ml_confidence_threshold: float = 0.65  # Default threshold for categorization confidence

    @property
    def model_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "..", "static")
        return os.path.abspath(
            os.path.join(
                static_dir,
                f"model-{self.classifier_short_name}-{self.model_version}.joblib"
            )
        )

    @property
    def manifest_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "..", "static")
        return os.path.abspath(
            os.path.join(
                static_dir,
                f"model-{self.classifier_short_name}-{self.model_version}.manifest.json"
            )
        )

    @property
    def test_data_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(base_dir, "..", "static")
        return os.path.abspath(
            os.path.join(
                static_dir,
                f"model-{self.classifier_short_name}-{self.model_version}.testdata.json"
            )
        )
