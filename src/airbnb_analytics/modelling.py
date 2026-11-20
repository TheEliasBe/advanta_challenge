"""Price prediction and attribute-based comparables for the supplied snapshot."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
NUMERIC_FEATURES = [
    "person_capacity",
    "bedrooms",
    "dist",
    "metro_dist",
    "attr_index_norm",
    "rest_index_norm",
    "lng",
    "lat",
    "cleanliness_rating",
    "guest_satisfaction_overall",
    "host_is_superhost",
]
CATEGORICAL_FEATURES = ["city", "room_type", "weekday"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
SIMILARITY_FEATURES = [
    "person_capacity",
    "bedrooms",
    "dist",
    "metro_dist",
    "attr_index_norm",
    "rest_index_norm",
    "lng",
    "lat",
    "cleanliness_rating",
    "guest_satisfaction_overall",
]


def prepare_listings(listings: pd.DataFrame) -> pd.DataFrame:
    """Keep positive finite targets and attach conservative location grouping keys."""
    frame = listings.loc[np.isfinite(listings["realSum"]) & listings["realSum"].gt(0)].copy()
    frame.index.name = "source_row"
    frame = frame.reset_index()
    frame[NUMERIC_FEATURES] = (
        frame[NUMERIC_FEATURES].astype(float).replace([np.inf, -np.inf], np.nan)
    )
    frame["location_group"] = pd.util.hash_pandas_object(
        frame[["city", "lng", "lat"]], index=False
    ).astype(str)
    return frame


class CityRoomMedian(RegressorMixin, BaseEstimator):
    """A training-only city/room median, with a global median fallback."""

    def fit(self, X, y):
        self.global_median_ = float(np.median(y))
        self.medians_ = (
            X[["city", "room_type"]]
            .assign(price=np.asarray(y))
            .groupby(["city", "room_type"], observed=True)["price"]
            .median()
        )
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        keys = pd.MultiIndex.from_frame(X[["city", "room_type"]])
        return self.medians_.reindex(keys).fillna(self.global_median_).to_numpy()


def score_prices(y, predicted) -> dict:
    return {
        "MAE": mean_absolute_error(y, predicted),
        "RMSE": root_mean_squared_error(y, predicted),
        "R2": r2_score(y, predicted),
        "median_APE_pct": float(np.median(np.abs(np.asarray(y) - predicted) / y) * 100),
    }


@dataclass
class PriceExperiment:
    winner: str
    model: object
    validation_scores: pd.DataFrame
    test_scores: pd.DataFrame
    test_predictions: pd.DataFrame
    importance: pd.DataFrame
    split_summary: pd.DataFrame
    split_assignments: pd.DataFrame
    reference: pd.DataFrame
    test: pd.DataFrame


def run_price_experiment(frame: pd.DataFrame) -> PriceExperiment:
    """Select on validation MAE, refit, then evaluate once on a disjoint test set."""
    train_val_idx, test_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(
            frame, groups=frame["location_group"]
        )
    )
    train_val = frame.iloc[train_val_idx]
    train_idx, val_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED + 1).split(
            train_val, groups=train_val["location_group"]
        )
    )
    train, validation, test = (
        train_val.iloc[train_idx],
        train_val.iloc[val_idx],
        frame.iloc[test_idx],
    )
    parts = {"train": train, "validation": validation, "test": test}
    split_assignments = pd.concat(
        [part[["source_row", "location_group"]].assign(split=name) for name, part in parts.items()],
        ignore_index=True,
    )
    if split_assignments.groupby("location_group")["split"].nunique().max() > 1:
        raise ValueError("A location group appears in multiple splits")

    preprocessing = ColumnTransformer(
        [
            (
                "numeric",
                make_pipeline(SimpleImputer(strategy="median"), StandardScaler()),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                make_pipeline(
                    SimpleImputer(strategy="most_frequent"),
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    models = {
        "Global median": DummyRegressor(strategy="median"),
        "City/room median": CityRoomMedian(),
        "Ridge (log price)": TransformedTargetRegressor(
            regressor=make_pipeline(clone(preprocessing), Ridge(alpha=10)),
            func=np.log1p,
            inverse_func=np.expm1,
        ),
        "Gradient boosting (log price)": TransformedTargetRegressor(
            regressor=make_pipeline(
                clone(preprocessing),
                HistGradientBoostingRegressor(
                    max_iter=160,
                    max_leaf_nodes=15,
                    min_samples_leaf=30,
                    l2_regularization=1,
                    learning_rate=0.08,
                    early_stopping=False,
                    random_state=SEED,
                ),
            ),
            func=np.log1p,
            inverse_func=np.expm1,
        ),
    }
    validation_scores = []
    for name, model in models.items():
        model.fit(train[FEATURES], train["realSum"])
        prediction = model.predict(validation[FEATURES])
        validation_scores.append({"model": name, **score_prices(validation["realSum"], prediction)})
    validation_scores = pd.DataFrame(validation_scores).sort_values("MAE").reset_index(drop=True)
    winner = validation_scores.iloc[0]["model"]

    # Use validation observations before refitting; the final test is not used for selection.
    importance_sample = validation.sample(n=min(2000, len(validation)), random_state=SEED)
    permuted = permutation_importance(
        models[winner],
        importance_sample[FEATURES],
        importance_sample["realSum"],
        scoring="neg_mean_absolute_error",
        n_repeats=3,
        random_state=SEED,
    )
    importance = pd.DataFrame(
        {
            "attribute": FEATURES,
            "MAE_increase": permuted.importances_mean,
            "repeat_std": permuted.importances_std,
        }
    ).sort_values("MAE_increase", ascending=False)
    final_model = clone(models[winner]).fit(train_val[FEATURES], train_val["realSum"])
    predictions = final_model.predict(test[FEATURES])
    test_scores = [{"model": winner, **score_prices(test["realSum"], predictions)}]
    for name in ["Global median", "City/room median"]:
        if name != winner:
            baseline = clone(models[name]).fit(train_val[FEATURES], train_val["realSum"])
            test_scores.append(
                {"model": name, **score_prices(test["realSum"], baseline.predict(test[FEATURES]))}
            )
    test_predictions = test[["source_row", "city", "room_type", "realSum"]].copy()
    test_predictions["predicted_price"] = predictions
    test_predictions["error"] = predictions - test["realSum"]
    test_predictions["absolute_error"] = np.abs(test_predictions["error"])
    test_predictions["APE_pct"] = test_predictions["absolute_error"] / test["realSum"] * 100
    split_summary = pd.DataFrame(
        [
            {"split": name, "rows": len(part), "location_groups": part["location_group"].nunique()}
            for name, part in parts.items()
        ]
    )
    return PriceExperiment(
        winner,
        final_model,
        validation_scores,
        pd.DataFrame(test_scores),
        test_predictions,
        importance,
        split_summary,
        split_assignments,
        train_val.copy(),
        test.copy(),
    )


def similar_listings(reference: pd.DataFrame, query: pd.Series, k: int = 5) -> pd.DataFrame:
    """Rank distinct reference locations without using price in the distance calculation."""
    if k < 1:
        raise ValueError("k must be positive")
    candidates = reference.loc[
        reference["city"].eq(query["city"])
        & reference["room_type"].eq(query["room_type"])
        & reference["weekday"].eq(query["weekday"])
        & ~reference["location_group"].eq(query["location_group"])
    ].copy()
    if candidates.empty:
        return candidates.assign(attribute_distance=pd.Series(dtype=float))
    transform = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
    # Reference-only scaling prevents the chosen query from changing the feature scales.
    transformed = transform.fit_transform(candidates[SIMILARITY_FEATURES])
    query_frame = pd.DataFrame([query[SIMILARITY_FEATURES].to_dict()])
    query_point = transform.transform(query_frame)
    candidates["attribute_distance"] = np.sqrt(np.mean((transformed - query_point) ** 2, axis=1))
    return (
        candidates.sort_values(["attribute_distance", "source_row"])
        .drop_duplicates("location_group")
        .head(k)
        .reset_index(drop=True)
    )


def cross_fitted_prices(frame: pd.DataFrame, model) -> pd.DataFrame:
    """Explore the full snapshot with each location group excluded from its model fit.

    The model specification was already selected in the original experiment. This
    exploratory cross-fit does not replace that experiment's reserved test scores.
    """
    predictions = frame[["source_row", "location_group", "city", "room_type", "realSum"]].copy()
    predictions["predicted_price"] = np.nan
    predictions["fold"] = 0
    cv = GroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    for fold, (train_idx, held_out_idx) in enumerate(
        cv.split(frame, groups=frame["location_group"]), start=1
    ):
        fitted = clone(model).fit(frame.iloc[train_idx][FEATURES], frame.iloc[train_idx]["realSum"])
        index = frame.index[held_out_idx]
        predictions.loc[index, "predicted_price"] = fitted.predict(
            frame.iloc[held_out_idx][FEATURES]
        )
        predictions.loc[index, "fold"] = fold
    predictions["price_gap"] = predictions["predicted_price"] - predictions["realSum"]
    predictions["price_gap_pct"] = predictions["price_gap"] / predictions["realSum"] * 100
    return predictions


def price_gap_scenario(
    predictions: pd.DataFrame,
    *,
    minimum_gap_pct: float = 0,
    move_fraction: float = 1,
    volume_retention: float = 1,
) -> dict:
    """An equally weighted one-sale-per-observation scenario, not forecast revenue.

    Raise only prices below their benchmark. All other prices/volumes stay fixed.
    Apply the same proportional volume change to the selected observations.
    """
    if minimum_gap_pct < 0 or not 0 <= move_fraction <= 1 or volume_retention < 0:
        raise ValueError("Require non-negative gap/volume and move_fraction between zero and one")
    candidates = predictions.loc[predictions["price_gap_pct"].gt(minimum_gap_pct)]
    baseline_all = float(predictions["realSum"].sum())
    baseline_cohort = float(candidates["realSum"].sum())
    gap_sum = float(candidates["price_gap"].sum())
    scenario_cohort = baseline_cohort + move_fraction * gap_sum
    cohort_change = volume_retention * scenario_cohort - baseline_cohort
    return {
        "observations": len(predictions),
        "candidate_observations": len(candidates),
        "minimum_gap_pct": minimum_gap_pct,
        "move_fraction": move_fraction,
        "volume_retention": volume_retention,
        "baseline_all": baseline_all,
        "baseline_cohort": baseline_cohort,
        "cohort_price_sum_after_change": scenario_cohort,
        "price_gap_at_full_move": gap_sum,
        "change_at_constant_volume": move_fraction * gap_sum,
        "cohort_price_change_pct": (scenario_cohort / baseline_cohort - 1) * 100
        if baseline_cohort
        else 0,
        "scenario_all": baseline_all + cohort_change,
        "scenario_change": cohort_change,
        "scenario_change_pct": cohort_change / baseline_all * 100 if baseline_all else 0,
        "break_even_volume_retention": baseline_cohort / scenario_cohort
        if scenario_cohort
        else np.nan,
    }


def save_price_model(experiment: PriceExperiment, directory: Path, data_path: Path) -> Path:
    """Persist the selected, test-evaluated model with a metadata card beside it.

    The model is the one refitted on train + validation and scored once on the test set,
    so the saved metrics describe exactly this artifact. Loading requires the same
    scikit-learn version and this package installed (``joblib.load``).
    """
    import sklearn

    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "price_model.joblib"
    joblib.dump(experiment.model, model_path)
    winner_scores = experiment.test_scores.set_index("model").loc[experiment.winner]
    card = {
        "model_file": model_path.name,
        "selected_model": experiment.winner,
        "target": "realSum (observed price; USD per catalogue, stay basis unconfirmed)",
        "features": FEATURES,
        "trained_on": "train + validation location groups (~80% of rows)",
        "test_metrics": {k: round(float(v), 4) for k, v in winner_scores.items()},
        "input_sha256": hashlib.sha256(Path(data_path).read_bytes()).hexdigest(),
        "seed": SEED,
        "sklearn_version": sklearn.__version__,
        "usage": "joblib.load(path).predict(frame[FEATURES]) with the same columns as the CSV",
        "limitations": (
            "Benchmarks existing listings (uses ratings); not a demand or revenue model; "
            "a gap to the prediction is not evidence of underpricing on its own."
        ),
    }
    (directory / "price_model.json").write_text(json.dumps(card, indent=2) + "\n")
    return model_path
