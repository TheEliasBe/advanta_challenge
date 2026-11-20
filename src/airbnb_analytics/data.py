"""Load the supplied sources without silently changing rows or column meanings."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PATH = RAW_DIR / "Case 1 - Airbnb Dataset.csv"
DICTIONARY_PATH = RAW_DIR / "Data Catalogue - Case 1 Airbnb Dataset.xlsx"

EXPECTED_COLUMNS = (
    "realSum",
    "room_type",
    "room_shared",
    "room_private",
    "person_capacity",
    "host_is_superhost",
    "multi",
    "biz",
    "cleanliness_rating",
    "guest_satisfaction_overall",
    "bedrooms",
    "dist",
    "metro_dist",
    "attr_index",
    "attr_index_norm",
    "rest_index",
    "rest_index_norm",
    "lng",
    "lat",
    "weekday",
    "city",
)

CATALOGUE_NAMES = {
    "hostissuperhost": "host_is_superhost",
    "guestsatisfactionoverall": "guest_satisfaction_overall",
    "attrindexnorm": "attr_index_norm",
    "restindexnorm": "rest_index_norm",
}


def load_listings(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Read the CSV as supplied; retain duplicates, missing values and outliers."""
    frame = pd.read_csv(path)
    missing = sorted(set(EXPECTED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing expected CSV columns: {missing}")
    return frame


def load_dictionary(path: str | Path = DICTIONARY_PATH) -> pd.DataFrame:
    """Add a CSV-name mapping while preserving the original catalogue fields."""
    catalogue = pd.read_excel(path, engine="openpyxl")
    catalogue["csv_column"] = catalogue["Field Name"].replace(CATALOGUE_NAMES)
    return catalogue


def column_profile(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a compact schema and completeness report."""
    return (
        pd.DataFrame(
            {
                "dtype": frame.dtypes.astype(str),
                "missing": frame.isna().sum(),
                "missing_pct": frame.isna().mean().mul(100),
                "unique": frame.nunique(dropna=True),
            }
        )
        .rename_axis("column")
        .reset_index()
    )
