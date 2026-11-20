import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd

    from airbnb_analytics.charts import save_presentation_chart
    from airbnb_analytics.data import PROJECT_ROOT, load_listings
    from airbnb_analytics.weekend import (
        PATTERNS,
        flat_host_uplift,
        pair_day_types,
        pattern_summary,
        reference_premiums,
        revenue_scenario,
    )

    return (
        PATTERNS,
        PROJECT_ROOT,
        alt,
        flat_host_uplift,
        load_listings,
        mo,
        pair_day_types,
        pattern_summary,
        pd,
        reference_premiums,
        revenue_scenario,
        save_presentation_chart,
    )


@app.cell
def _(mo):
    mo.md("""
    # 04 · Weekend pricing: how much value do flat-priced listings leave unpriced?

    Many accommodations appear twice in the snapshot, once per `weekday` flag at identical
    coordinates. Comparing the two prices shows which hosts charge more at the weekend and which
    charge the same every day. We then size a single lever: **same-price hosts adopt the weekend
    premium that comparable hosts in their city and room type already charge.**

    **Assumptions to confirm with the client**

    - `weekday == 0` is the weekend observation. The catalogue does not state this; it is
      inferred because flag-0 prices are higher in most differentiated pairs.
    - Identical city + coordinates are treated as one listing. There is no listing ID.
    - The snapshot has no dates, seasonality or bookings. The revenue figures are a static
      what-if built on reported Airbnb financials, not a demand forecast.
    """)
    return


@app.cell
def _(mo):
    flat_tolerance = mo.ui.slider(
        0.0,
        2.0,
        step=0.25,
        value=0.5,
        label="Count as 'same price' when the weekend/weekday difference is within (%)",
        show_value=True,
    )
    flat_tolerance
    return (flat_tolerance,)


@app.cell
def _(flat_tolerance, load_listings, pair_day_types):
    source_data = load_listings()
    paired = pair_day_types(source_data, flat_tolerance=flat_tolerance.value / 100)
    pairs = paired.pairs
    return paired, pairs


@app.cell
def _(mo, paired):
    mo.vstack(
        [
            mo.md("## 1 · Build weekend/weekday pairs"),
            mo.ui.table(paired.exclusions, selection=None, pagination=False),
        ]
    )
    return


@app.cell
def _(pairs, pattern_summary, pd):
    city_patterns = pd.concat(
        [pattern_summary(pairs, None).rename(columns={"segment": "city"}), pattern_summary(pairs)],
        ignore_index=True,
    )
    city_patterns["city"] = city_patterns["city"].str.title()
    return (city_patterns,)


@app.cell
def _(PATTERNS, alt, city_patterns, mo, save_presentation_chart):
    _long = city_patterns.melt(
        id_vars=["city", "pairs"],
        value_vars=[f"share_{p.lower().replace(' ', '_')}" for p in PATTERNS],
        var_name="pattern",
        value_name="share",
    )
    _long["pattern"] = _long["pattern"].map(
        {f"share_{p.lower().replace(' ', '_')}": p for p in PATTERNS}
    )
    _long["order"] = _long["pattern"].map({p: i for i, p in enumerate(PATTERNS)})
    _cities = city_patterns.loc[city_patterns["city"].ne("All Cities")]
    _city_order = ["All Cities"] + _cities.sort_values("share_same_price", ascending=False)[
        "city"
    ].tolist()

    pattern_chart = (
        alt.Chart(_long)
        .mark_bar()
        .encode(
            y=alt.Y("city:N", sort=_city_order, title=None),
            x=alt.X(
                "share:Q", stack="normalize", axis=alt.Axis(format="%"), title="Share of listings"
            ),
            color=alt.Color(
                "pattern:N",
                scale=alt.Scale(domain=list(PATTERNS), range=["#E04F5F", "#9AA5B1", "#D3D8DE"]),
                legend=alt.Legend(orient="top", title=None),
            ),
            order=alt.Order("order:Q"),
            tooltip=[
                "city",
                "pattern",
                alt.Tooltip("share:Q", format=".1%"),
                alt.Tooltip("pairs:Q", format=","),
            ],
        )
        .properties(
            title=alt.Title(
                "Most hosts charge the same price on weekdays and weekends",
                subtitle="Paired listings observed on both day types; 'All Cities' pools every pair",
            ),
            width="container",
            height=380,
        )
    )
    save_presentation_chart(pattern_chart, "04_weekend_pricing/pricing_patterns_by_city")

    mo.vstack([mo.md("## 2 · Who prices weekends differently?"), pattern_chart])
    return


@app.cell
def _(city_patterns, mo):
    _table = city_patterns.assign(
        **{
            c: city_patterns[c].mul(100).round(1)
            for c in city_patterns.columns
            if c.startswith(("share", "premium", "flat"))
        }
    ).rename(
        columns={
            "share_same_price": "same price %",
            "share_weekend_higher": "weekend higher %",
            "share_weekday_higher": "weekday higher %",
            "flat_share_of_weekend_value": "same-price share of weekend value %",
            "premium_p25": "premium P25 %",
            "premium_median": "premium median %",
        }
    )
    mo.vstack(
        [
            mo.md("Premiums are measured only among hosts who already charge more at the weekend."),
            mo.ui.table(_table, selection=None, pagination=False),
        ]
    )
    return


@app.cell
def _(mo):
    premium_quantile = mo.ui.dropdown(
        options={"Conservative (25th percentile)": 0.25, "Typical (median)": 0.5},
        value="Typical (median)",
        label="Premium adopted by same-price hosts",
    )
    revenue_total = mo.ui.number(
        start=0, stop=100, step=0.1, value=12.2, label="Airbnb FY2025 revenue ($B)"
    )
    gbv_total = mo.ui.number(
        start=1, stop=500, step=0.1, value=91.3, label="Airbnb FY2025 gross booking value ($B)"
    )
    revenue_emea = mo.ui.number(
        start=0, stop=100, step=0.01, value=4.73, label="EMEA FY2025 revenue ($B)"
    )
    weekend_share = mo.ui.slider(
        0.1, 0.6, step=0.01, value=0.29, label="Weekend share of nights", show_value=True
    )
    adoption = mo.ui.slider(
        0, 100, step=5, value=50, label="Same-price hosts who adopt (%)", show_value=True
    )
    volume_change = mo.ui.slider(
        -30,
        10,
        step=1,
        value=0,
        label="Change in adopters' weekend bookings (%)",
        show_value=True,
    )
    mo.vstack(
        [
            mo.md("## 3 · From weekend premium to Airbnb revenue"),
            mo.hstack([premium_quantile, adoption, volume_change], justify="start", gap=2),
            mo.hstack(
                [revenue_total, gbv_total, revenue_emea, weekend_share], justify="start", gap=2
            ),
            mo.md(
                "Defaults: [Airbnb Q4 2025 shareholder letter](https://s26.q4cdn.com/656283129/files/doc_financials/2025/q4/Airbnb_Q4-2025-Shareholder-Letter-Final.pdf) "
                "for total revenue and GBV. EMEA revenue is from third-party summaries of the 10-K "
                "([opencapital](https://www.opencapital.sh/stocks/abnb/metrics/abnb_segment_europe_the_middle_east_and_africa_revenue)); "
                "verify against the filing. Airbnb does not report EMEA GBV, so it is derived "
                "as EMEA revenue ÷ group take rate. Weekend share 2/7 ≈ 0.29 (Friday and Saturday nights)."
            ),
        ]
    )
    return (
        adoption,
        gbv_total,
        premium_quantile,
        revenue_emea,
        revenue_total,
        volume_change,
        weekend_share,
    )


@app.cell
def _(flat_host_uplift, gbv_total, pairs, revenue_emea, revenue_total):
    take_rate = revenue_total.value / gbv_total.value
    emea_gbv = revenue_emea.value / take_rate
    uplift_by_quantile = {q: flat_host_uplift(pairs, q) for q in (0.25, 0.5)}
    return emea_gbv, take_rate, uplift_by_quantile


@app.cell
def _(
    adoption,
    emea_gbv,
    premium_quantile,
    revenue_scenario,
    take_rate,
    uplift_by_quantile,
    volume_change,
    weekend_share,
):
    _pooled = uplift_by_quantile[premium_quantile.value].set_index("city").loc["All cities"]
    scenario_inputs = {
        "gbv": emea_gbv,
        "take_rate": take_rate,
        "weekend_share": weekend_share.value,
        "flat_share": float(_pooled["flat_share_of_weekend_value"]),
        "premium": float(_pooled["effective_premium"]),
    }
    scenario = revenue_scenario(
        **scenario_inputs,
        adoption=adoption.value / 100,
        volume_change=volume_change.value / 100,
    )
    return scenario, scenario_inputs


@app.cell
def _(adoption, mo, scenario, scenario_inputs, volume_change):
    _i = scenario_inputs
    _headline_kind = "gain" if scenario["extra_revenue"] >= 0 else "loss"
    mo.md(f"""
    | Step | Value |
    |---|---|
    | Airbnb take rate (revenue ÷ GBV) | **{_i["take_rate"]:.1%}** |
    | EMEA gross booking value (derived) | **${_i["gbv"]:,.1f}B** |
    | × weekend share of nights | {_i["weekend_share"]:.0%} |
    | × same-price hosts' share of weekend value | {_i["flat_share"]:.1%} |
    | × adoption | {adoption.value}% |
    | = weekend booking value affected | **${scenario["affected_gbv"] * 1000:,.0f}M** |
    | × weekend premium adopted (price-weighted) | +{_i["premium"]:.1%} |
    | with booking change for adopters | {volume_change.value:+d}% |
    | = extra gross booking value | **${scenario["extra_gbv"] * 1000:,.0f}M** ({scenario["extra_gbv_pct"]:+.2%} of EMEA GBV) |
    | × take rate = **extra Airbnb revenue** | **${scenario["extra_revenue"] * 1000:,.0f}M per year** |

    Under these assumptions the lever is a **{_headline_kind} of ≈ ${abs(scenario["extra_revenue"]) * 1000:,.0f}M**
    in annual Airbnb revenue. It stays positive as long as adopters lose fewer than
    **{-scenario["break_even_volume_change"]:.1%}** of their weekend bookings.
    """)
    return


@app.cell
def _(emea_gbv, pd, revenue_scenario, take_rate, uplift_by_quantile, weekend_share):
    _labels = {0.25: "Conservative (25th pct)", 0.5: "Typical (median)"}
    _rows = []
    for _q, _uplift in uplift_by_quantile.items():
        _pooled = _uplift.set_index("city").loc["All cities"]
        for _adoption in (0.25, 0.5, 1.0):
            _result = revenue_scenario(
                gbv=emea_gbv,
                take_rate=take_rate,
                weekend_share=weekend_share.value,
                flat_share=float(_pooled["flat_share_of_weekend_value"]),
                premium=float(_pooled["effective_premium"]),
                adoption=_adoption,
            )
            _rows.append(
                {
                    "premium": _labels[_q],
                    "premium_pct": round(_pooled["effective_premium"] * 100, 1),
                    "adoption_pct": int(_adoption * 100),
                    "extra_gbv_musd": round(_result["extra_gbv"] * 1000),
                    "extra_revenue_musd": round(_result["extra_revenue"] * 1000),
                    "break_even_booking_change_pct": round(
                        _result["break_even_volume_change"] * 100, 1
                    ),
                }
            )
    scenario_grid = pd.DataFrame(_rows)
    return (scenario_grid,)


@app.cell
def _(mo, scenario_grid):
    mo.vstack(
        [
            mo.md("### Slide table: unchanged weekend bookings"),
            mo.ui.table(scenario_grid, selection=None, pagination=False),
        ]
    )
    return


@app.cell
def _(
    adoption,
    alt,
    emea_gbv,
    mo,
    pd,
    premium_quantile,
    revenue_scenario,
    save_presentation_chart,
    scenario,
    scenario_inputs,
    volume_change,
):
    _rows = [
        {
            "booking_change_pct": _v,
            "adoption": f"{int(_a * 100)}% adoption",
            "extra_revenue_musd": revenue_scenario(
                **scenario_inputs, adoption=_a, volume_change=_v / 100
            )["extra_revenue"]
            * 1000,
        }
        for _a in (0.25, 0.5, 1.0)
        for _v in range(-20, 6)
    ]
    _data = pd.DataFrame(_rows)
    _selected = pd.DataFrame(
        [
            {
                "booking_change_pct": volume_change.value,
                "extra_revenue_musd": scenario["extra_revenue"] * 1000,
            }
        ]
    )
    _label = next(k for k, v in premium_quantile.options.items() if v == premium_quantile.value)
    _lines = (
        alt.Chart(_data)
        .mark_line(strokeWidth=3)
        .encode(
            x=alt.X(
                "booking_change_pct:Q",
                title="Assumed change in adopters' weekend bookings (%)",
                scale=alt.Scale(domain=[-20, 5], nice=False),
                axis=alt.Axis(values=list(range(-20, 6, 5))),
            ),
            y=alt.Y("extra_revenue_musd:Q", title="Extra Airbnb revenue, EMEA ($M per year)"),
            color=alt.Color(
                "adoption:N",
                sort=["25% adoption", "50% adoption", "100% adoption"],
                scale=alt.Scale(range=["#F2A7AE", "#E9707C", "#C0283A"]),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                "adoption",
                "booking_change_pct",
                alt.Tooltip("extra_revenue_musd:Q", format=",.0f"),
            ],
        )
    )
    _zero = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(strokeDash=[4, 4], color="#59636E")
        .encode(y="y:Q")
    )
    _point = (
        alt.Chart(_selected)
        .mark_point(size=220, filled=True, color="#1F2328")
        .encode(x="booking_change_pct:Q", y="extra_revenue_musd:Q")
    )
    revenue_chart = (_zero + _lines + _point).properties(
        title=alt.Title(
            "Weekend pricing could add tens of millions in EMEA revenue if bookings hold",
            subtitle=(
                f"{_label} premium (+{scenario_inputs['premium']:.1%}); EMEA GBV ≈ ${emea_gbv:,.0f}B; "
                f"dot = selected scenario ({adoption.value}% adoption)"
            ),
        ),
        width="container",
        height=420,
    )
    save_presentation_chart(revenue_chart, "04_weekend_pricing/revenue_sensitivity")
    mo.vstack([mo.md("### Sensitivity to booking response"), revenue_chart])
    return


@app.cell
def _(
    PROJECT_ROOT, city_patterns, mo, pairs, reference_premiums, scenario_grid, uplift_by_quantile
):
    _out = PROJECT_ROOT / "outputs" / "tables" / "04_weekend_pricing"
    _out.mkdir(parents=True, exist_ok=True)
    city_patterns.to_csv(_out / "pricing_patterns_by_city.csv", index=False)
    scenario_grid.to_csv(_out / "revenue_scenarios.csv", index=False)
    for _q, _uplift in uplift_by_quantile.items():
        _uplift.to_csv(_out / f"flat_host_uplift_q{int(_q * 100)}.csv", index=False)
        reference_premiums(pairs, _q).to_csv(
            _out / f"reference_premiums_q{int(_q * 100)}.csv", index=False
        )
    mo.md(f"""
    ## 4 · Caveats for the slide

    - **Bookings may fall.** The dataset has no demand. Hosts who already charge a premium may
      sit in stronger weekend markets, so the right next step is a controlled test on Airbnb's
      booking data. The chart shows how much booking loss each scenario absorbs.
    - **Extrapolation.** Behaviour from 10 large European cities is applied to all of EMEA GBV,
      which also covers the Middle East and Africa. Treat the result as an order of magnitude.
    - **Unconfirmed definitions.** Weekend = flag 0, and coordinates = listing, both need client confirmation.
    - **Hosts charging more on weekdays** (≈7% of pairs) are left unchanged; they may be
      business-travel locations and are a separate, smaller lever.

    Tables written to `{_out.relative_to(PROJECT_ROOT)}/`; charts to `outputs/figures/04_weekend_pricing/`.
    """)
    return


if __name__ == "__main__":
    app.run()
