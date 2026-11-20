"""Collect every number the client deck shows into one JSON file.

Run after notebooks 03 and 04 have written their tables:
    uv run python deck/export_slide_data.py
"""

import json

import pandas as pd

from airbnb_analytics.data import PROJECT_ROOT, load_listings
from airbnb_analytics.weekend import pair_day_types, pattern_summary

TABLES = PROJECT_ROOT / "outputs" / "tables"
OUTPUT = TABLES / "deck" / "slide_data.json"

CORRELATION_FEATURES = {
    "person_capacity": "Guest capacity",
    "bedrooms": "Bedrooms",
    "attr_index_norm": "Attraction index",
    "rest_index_norm": "Restaurant index",
    "guest_satisfaction_overall": "Guest satisfaction",
    "cleanliness_rating": "Cleanliness rating",
    "host_is_superhost": "Superhost",
    "metro_dist": "Distance to metro",
    "dist": "Distance to centre",
    "room_private": "Private room (vs. other)",
}

IMPORTANCE_LABELS = {
    "lng": "Longitude",
    "room_type": "Room type",
    "attr_index_norm": "Attraction index",
    "lat": "Latitude",
    "person_capacity": "Guest capacity",
    "bedrooms": "Bedrooms",
    "city": "City",
    "dist": "Distance to centre",
    "guest_satisfaction_overall": "Guest satisfaction",
    "cleanliness_rating": "Cleanliness rating",
    "rest_index_norm": "Restaurant index",
    "metro_dist": "Distance to metro",
    "weekday": "Weekday flag",
    "host_is_superhost": "Superhost",
}


def correlations(listings: pd.DataFrame) -> dict:
    frame = listings.assign(
        room_private=listings["room_private"].astype(int),
        host_is_superhost=listings["host_is_superhost"].astype(int),
    )
    columns = list(CORRELATION_FEATURES) + ["realSum"]
    pooled = frame[columns].corr("spearman")["realSum"].drop("realSum")
    within = pd.DataFrame(
        {
            city: group[columns].corr("spearman")["realSum"].drop("realSum")
            for city, group in frame.groupby("city")
        }
    )
    pairs = {
        "Bedrooms ~ capacity": ("bedrooms", "person_capacity"),
        "Cleanliness ~ satisfaction": ("cleanliness_rating", "guest_satisfaction_overall"),
        "Attraction ~ restaurant index": ("attr_index_norm", "rest_index_norm"),
    }
    return {
        "labels": CORRELATION_FEATURES,
        "pooled": pooled.round(2).to_dict(),
        "within_median": within.median(axis=1).round(2).to_dict(),
        "by_city": within.round(2).to_dict(),
        "redundant_pairs": {
            name: round(float(frame[[a, b]].corr("spearman").iloc[0, 1]), 2)
            for name, (a, b) in pairs.items()
        },
    }


def approach_numbers(listings: pd.DataFrame, paired) -> dict:
    """Method facts for the interviewer deck: data audit, model selection, first pricing idea."""
    modelling = TABLES / "03_modelling"
    segments = pd.read_csv(modelling / "segment_errors.csv")
    city_bias = segments.loc[segments["dimension"].eq("city"), "bias"]
    gap = pd.read_csv(modelling / "price_gap_scenario.csv").iloc[0]
    return {
        "columns": listings.shape[1],
        "duplicate_rows": int(listings.duplicated().sum()),
        "max_price": round(float(listings["realSum"].max())),
        "p99_price": round(float(listings["realSum"].quantile(0.99))),
        "validation_scores": pd.read_csv(modelling / "validation_scores.csv")
        .round(2)
        .to_dict(orient="records"),
        "split_summary": pd.read_csv(modelling / "split_summary.csv").to_dict(orient="records"),
        "city_bias_range": [round(float(city_bias.min()), 1), round(float(city_bias.max()), 1)],
        "cities_with_negative_bias": int(city_bias.lt(0).sum()),
        "first_idea": {
            "observations": int(gap["observations"]),
            "candidates": int(gap["candidate_observations"]),
            "uplift_pct": round(float(gap["scenario_change_pct"]), 2),
        },
        "pairing_steps": paired.exclusions.to_dict(orient="records"),
    }


def main() -> None:
    listings = load_listings()
    city = listings.groupby("city")["realSum"].agg(observations="size", median="median")
    test_scores = pd.read_csv(TABLES / "03_modelling" / "test_scores.csv")
    importance = pd.read_csv(TABLES / "03_modelling" / "permutation_importance.csv")
    paired = pair_day_types(listings)
    pairs = paired.pairs
    patterns = pattern_summary(pairs)
    pooled_patterns = pattern_summary(pairs, None).iloc[0]
    scenarios = pd.read_csv(TABLES / "04_weekend_pricing" / "revenue_scenarios.csv")
    uplift = pd.read_csv(TABLES / "04_weekend_pricing" / "flat_host_uplift_q50.csv")

    data = {
        "overview": {
            "observations": len(listings),
            "cities": int(listings["city"].nunique()),
            "missing_values": int(listings.isna().sum().sum()),
            "median_price": float(listings["realSum"].median()),
            "city_median_price": city["median"].round(0).to_dict(),
            "city_observations": city["observations"].to_dict(),
        },
        "correlations": correlations(listings),
        "model": {
            "test_scores": test_scores.round(2).to_dict(orient="records"),
            "importance": [
                {"attribute": IMPORTANCE_LABELS.get(a, a), "mae_increase": round(v, 1)}
                for a, v in zip(importance["attribute"], importance["MAE_increase"], strict=True)
            ],
        },
        "weekend": {
            "pairs": len(pairs),
            "share_same_price": float(pooled_patterns["share_same_price"]),
            "share_weekend_higher": float(pooled_patterns["share_weekend_higher"]),
            "share_weekday_higher": float(pooled_patterns["share_weekday_higher"]),
            "flat_share_of_weekend_value": float(pooled_patterns["flat_share_of_weekend_value"]),
            "premium_median_differentiators": float(pooled_patterns["premium_median"]),
            "by_city": patterns.round(4).to_dict(orient="records"),
            "effective_premium_typical": float(
                uplift.set_index("city").loc["All cities", "effective_premium"]
            ),
            "scenarios": scenarios.to_dict(orient="records"),
        },
        "approach": approach_numbers(listings, paired),
        "financials": {
            "revenue_bn": 12.2,
            "gbv_bn": 91.3,
            "emea_revenue_bn": 4.73,
            "weekend_share": 0.29,
            "sources": [
                "Airbnb Q4 2025 shareholder letter (FY2025 revenue and gross booking value)",
                "EMEA revenue: third-party summaries of Airbnb's FY2025 10-K; verify in filing",
            ],
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2))
    print(f"Wrote {OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
