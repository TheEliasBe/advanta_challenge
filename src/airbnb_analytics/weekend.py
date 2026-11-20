"""Weekend price differentiation: paired listings, reference premiums and revenue sizing.

Assumption carried throughout: ``weekday == 0`` is the weekend observation. The source
catalogue does not state this; it is inferred from flag-0 prices being higher in most pairs.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

LOCATION_KEY = ["city", "lng", "lat"]
WEEKEND_FLAG = 0
WEEKDAY_FLAG = 1
PATTERNS = ("Same price", "Weekend higher", "Weekday higher")


@dataclass(frozen=True)
class PairedListings:
    pairs: pd.DataFrame
    exclusions: pd.DataFrame


def pair_day_types(listings: pd.DataFrame, flat_tolerance: float = 0.005) -> PairedListings:
    """Match weekend and weekday observations at identical coordinates.

    A pair is kept when each flag has exactly one row at the location and both rows share
    room type and person capacity. Coordinates are a proxy for a listing, not an ID.
    """
    valid = listings.loc[np.isfinite(listings["realSum"]) & listings["realSum"].gt(0)].copy()
    valid["weekday"] = valid["weekday"].astype(int)
    counts = valid.groupby(LOCATION_KEY + ["weekday"]).size().unstack(fill_value=0)
    single_flag = counts.lt(1).any(axis=1)
    repeated = counts.gt(1).any(axis=1) & ~single_flag
    eligible = counts.index[counts.eq(1).all(axis=1)]

    rows = valid.set_index(LOCATION_KEY).loc[eligible].reset_index()
    weekend = rows.loc[rows["weekday"].eq(WEEKEND_FLAG)].set_index(LOCATION_KEY)
    weekday = rows.loc[rows["weekday"].eq(WEEKDAY_FLAG)].set_index(LOCATION_KEY)
    pairs = weekend[["room_type", "person_capacity", "realSum"]].join(
        weekday[["room_type", "person_capacity", "realSum"]], lsuffix="_weekend", rsuffix="_weekday"
    )
    consistent = pairs["room_type_weekend"].eq(pairs["room_type_weekday"]) & pairs[
        "person_capacity_weekend"
    ].eq(pairs["person_capacity_weekday"])

    pairs = (
        pairs.loc[consistent]
        .rename(
            columns={
                "room_type_weekend": "room_type",
                "person_capacity_weekend": "person_capacity",
                "realSum_weekend": "weekend_price",
                "realSum_weekday": "weekday_price",
            }
        )
        .drop(columns=["room_type_weekday", "person_capacity_weekday"])
        .reset_index()
    )
    pairs["weekend_premium"] = pairs["weekend_price"] / pairs["weekday_price"] - 1
    pairs["pattern"] = np.select(
        [
            pairs["weekend_premium"].abs().le(flat_tolerance),
            pairs["weekend_premium"].gt(0),
        ],
        PATTERNS[:2],
        PATTERNS[2],
    )

    exclusions = pd.DataFrame(
        [
            ("Location groups (city + coordinates)", len(counts)),
            ("Observed on one day type only", int(single_flag.sum())),
            ("Several rows for the same day type", int(repeated.sum())),
            ("Room type or capacity differs between days", int((~consistent).sum())),
            ("Clean weekend/weekday pairs", len(pairs)),
        ],
        columns=["step", "locations"],
    )
    return PairedListings(pairs=pairs, exclusions=exclusions)


def pattern_summary(pairs: pd.DataFrame, by: str | None = "city") -> pd.DataFrame:
    """Share of pairs per pricing pattern and the premium charged by differentiating hosts."""
    groups = pairs.groupby(by) if by else [("All cities", pairs)]
    records = []
    for name, group in groups:
        differentiators = group.loc[group["pattern"].eq("Weekend higher"), "weekend_premium"]
        flat = group["pattern"].eq("Same price")
        records.append(
            {
                by or "segment": name,
                "pairs": len(group),
                **{
                    f"share_{p.lower().replace(' ', '_')}": group["pattern"].eq(p).mean()
                    for p in PATTERNS
                },
                "flat_share_of_weekend_value": group.loc[flat, "weekend_price"].sum()
                / group["weekend_price"].sum(),
                "premium_p25": differentiators.quantile(0.25),
                "premium_median": differentiators.median(),
            }
        )
    return pd.DataFrame(records)


def reference_premiums(
    pairs: pd.DataFrame, quantile: float, min_references: int = 20
) -> pd.DataFrame:
    """Premium a flat-pricing host would adopt: a quantile of comparable differentiators.

    Comparables share city and room type. Segments with fewer than ``min_references``
    differentiating pairs fall back to the city-wide quantile.
    """
    differentiators = pairs.loc[pairs["pattern"].eq("Weekend higher")]
    segment = differentiators.groupby(["city", "room_type"])["weekend_premium"].agg(
        premium=lambda s: s.quantile(quantile), references="size"
    )
    city = differentiators.groupby("city")["weekend_premium"].quantile(quantile)
    segments = pairs[["city", "room_type"]].drop_duplicates().set_index(["city", "room_type"])
    reference = segments.join(segment)
    fallback = reference["references"].fillna(0).lt(min_references)
    city_values = reference.index.get_level_values("city").map(city)
    reference["premium"] = reference["premium"].where(~fallback, city_values)
    reference["references"] = reference["references"].fillna(0).astype(int)
    reference["source"] = np.where(fallback, "city fallback", "city × room type")
    return reference.reset_index()


def flat_host_uplift(pairs: pd.DataFrame, quantile: float) -> pd.DataFrame:
    """Weekend price uplift if same-price hosts adopted their reference premium.

    Returns one row per city plus an "All cities" row. ``effective_premium`` is weighted by
    weekend price, so it can be applied directly to weekend booking value.
    """
    reference = reference_premiums(pairs, quantile)
    flat = pairs.loc[pairs["pattern"].eq("Same price")].merge(
        reference[["city", "room_type", "premium"]], on=["city", "room_type"]
    )
    flat["weekend_uplift"] = flat["weekend_price"] * flat["premium"]

    def summarise(name, group, everything):
        return {
            "city": name,
            "flat_pairs": len(group),
            "flat_share_of_weekend_value": group["weekend_price"].sum()
            / everything["weekend_price"].sum(),
            "effective_premium": group["weekend_uplift"].sum() / group["weekend_price"].sum(),
            "weekend_value_uplift": group["weekend_uplift"].sum()
            / everything["weekend_price"].sum(),
        }

    rows = [summarise(c, g, pairs.loc[pairs["city"].eq(c)]) for c, g in flat.groupby("city")]
    rows.append(summarise("All cities", flat, pairs))
    return pd.DataFrame(rows)


def revenue_scenario(
    *,
    gbv: float,
    take_rate: float,
    weekend_share: float,
    flat_share: float,
    premium: float,
    adoption: float,
    volume_change: float = 0.0,
) -> dict[str, float]:
    """Size the weekend premium lever from booking value down to Airbnb revenue.

    Affected value = GBV × weekend share × flat-host share × adoption. Adopters charge
    (1 + premium) and keep (1 + volume_change) of those weekend bookings; everything else
    is unchanged. The result is a static what-if, not a demand forecast.
    """
    affected = gbv * weekend_share * flat_share * adoption
    after = affected * (1 + premium) * (1 + volume_change)
    extra_gbv = after - affected
    return {
        "affected_gbv": affected,
        "extra_gbv": extra_gbv,
        "extra_gbv_pct": extra_gbv / gbv,
        "extra_revenue": extra_gbv * take_rate,
        "break_even_volume_change": 1 / (1 + premium) - 1,
    }
