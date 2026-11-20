import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import hashlib
    import json

    import altair as alt
    import marimo as mo
    import pandas as pd
    import sklearn

    from airbnb_analytics.charts import save_presentation_chart
    from airbnb_analytics.data import DATA_PATH, PROJECT_ROOT, load_listings
    from airbnb_analytics.modelling import (
        FEATURES,
        SEED,
        SIMILARITY_FEATURES,
        cross_fitted_prices,
        prepare_listings,
        price_gap_scenario,
        run_price_experiment,
        save_price_model,
        similar_listings,
    )

    return (
        DATA_PATH,
        FEATURES,
        PROJECT_ROOT,
        SEED,
        SIMILARITY_FEATURES,
        alt,
        cross_fitted_prices,
        hashlib,
        json,
        load_listings,
        mo,
        pd,
        prepare_listings,
        price_gap_scenario,
        run_price_experiment,
        save_presentation_chart,
        save_price_model,
        similar_listings,
        sklearn,
    )


@app.cell
def _(mo):
    mo.md("""
    # 03 · Predict prices and find comparable accommodations

    Two analytical prototypes using the supplied data:

    1. **Price prediction:** estimate the observed price from accommodation characteristics.
    2. **Similar listings:** retrieve comparable accommodations using attributes, without using price to rank them.

    **There are no demand, booking or occupancy outcomes in this dataset.** We evaluate price
    prediction error, not revenue uplift. The target is the original realSum field (USD per
    catalogue); its stay duration is unconfirmed. The weekday flag is used as a category,
    not as an occupancy measure. Ratings are included for existing-listing benchmarking.
    """)
    return


@app.cell
def _(load_listings, prepare_listings):
    source_data = load_listings()
    modelling_data = prepare_listings(source_data)
    return modelling_data, source_data


@app.cell
def _(modelling_data, run_price_experiment):
    experiment = run_price_experiment(modelling_data)
    return (experiment,)


@app.cell
def _(FEATURES, experiment, mo, modelling_data, source_data):
    mo.vstack(
        [
            mo.md(f"""
        ## 1 · Evaluation design

        **{len(modelling_data):,} rows retained; {len(source_data) - len(modelling_data):,} non-positive/non-finite target rows excluded.** No price outliers are trimmed.

        Split approximately 60% / 20% / 20% by **city + exact coordinates**. A location group
        cannot appear in more than one partition. This reduces leakage from repeated
        accommodations, but coordinates are a proxy: different properties can share a point,
        and a property with changing coordinates can escape the grouping. No listing ID is supplied.

        Preprocessing is fitted on training data. Model choice uses validation MAE; the winner
        is refitted on train + validation and evaluated on the reserved test set. This is an
        initial fixed-parameter comparison, not an exhaustive search. It evaluates new location
        groups in the observed cities, not forecasting or transfer to unseen cities.

        **Features:** {", ".join(FEATURES)}.

        Room-type indicators and raw index duplicates are omitted. The ambiguous multi and
        biz fields are excluded pending confirmation of their definitions.
        """),
            mo.ui.table(experiment.split_summary, pagination=False),
        ]
    )
    return


@app.cell
def _(experiment, mo):
    _scores = experiment.test_scores.set_index("model")
    _mae = _scores.loc[experiment.winner, "MAE"]
    _baseline = _scores.loc["City/room median", "MAE"]
    mo.vstack(
        [
            mo.md(f"""
        ## 2 · Can a model improve on simple price benchmarks?

        **Selected on validation:** {experiment.winner}.
        **Test MAE:** {_mae:.2f} source price units; **{100 * (1 - _mae / _baseline):.1f}% lower MAE**
        than the city/room median baseline. This is a prediction-error comparison, not a revenue estimate.

        MAE measures typical error in source price units; RMSE highlights large misses.
        Median APE describes the median percentage error. Ridge and gradient boosting are
        trained on log(1 + price); all reported errors use predictions transformed back to original units.
        """),
            mo.md("**Validation: all candidates**"),
            mo.ui.table(experiment.validation_scores, pagination=False),
            mo.md("**Reserved test: selected model and reference baselines**"),
            mo.ui.table(experiment.test_scores, pagination=False),
        ]
    )
    return


@app.cell
def _(alt, experiment, mo):
    _plot = experiment.test_predictions.loc[experiment.test_predictions["predicted_price"].gt(0)]
    _sample = _plot.sample(n=min(3000, len(_plot)), random_state=42)
    _limits = [
        float(min(_plot["realSum"].min(), _plot["predicted_price"].min())),
        float(max(_plot["realSum"].max(), _plot["predicted_price"].max())),
    ]
    _points = (
        alt.Chart(_sample)
        .mark_point(opacity=0.35, size=28)
        .encode(
            x=alt.X("realSum:Q", scale=alt.Scale(type="log"), title="Observed realSum (log scale)"),
            y=alt.Y(
                "predicted_price:Q",
                scale=alt.Scale(type="log"),
                title="Predicted realSum (log scale)",
            ),
            color="city:N",
            tooltip=[
                "source_row:Q",
                "city:N",
                "room_type:N",
                alt.Tooltip("realSum:Q", format=".2f"),
                alt.Tooltip("predicted_price:Q", format=".2f"),
                alt.Tooltip("APE_pct:Q", format=".1f"),
            ],
        )
    )
    _line = (
        alt.Chart(alt.Data(values=[{"observed": v, "predicted": v} for v in _limits]))
        .mark_line(color="#475569", strokeDash=[5, 5])
        .encode(x="observed:Q", y="predicted:Q")
    )
    prediction_chart = mo.ui.altair_chart(
        (_points + _line).properties(
            width="container",
            height=380,
            title="Held-out predictions: the dashed line indicates a perfect prediction",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    mo.vstack(
        [
            prediction_chart,
            mo.md(
                f"Plot: {len(_sample):,} sampled test rows. Metrics use all test rows; {len(experiment.test_predictions) - len(_plot)} non-positive predictions are omitted from log axes only."
            ),
        ]
    )
    return (prediction_chart,)


@app.cell
def _(experiment, mo, pd):
    _errors = experiment.test_predictions
    segment_errors = pd.concat(
        [
            _errors.groupby(_column, observed=True)
            .agg(
                rows=("realSum", "size"),
                MAE=("absolute_error", "mean"),
                bias=("error", "mean"),
                median_APE_pct=("APE_pct", "median"),
            )
            .rename_axis("segment")
            .reset_index()
            .assign(dimension=_column)
            for _column in ["city", "room_type"]
        ],
        ignore_index=True,
    )
    mo.vstack(
        [
            mo.md("""
        ### Where does prediction work less well?

        Segment errors reveal where the overall average hides weaknesses. Positive bias means
        the model overpredicts on average. Large price deviations can also reflect unobserved amenities
        or model error; they do not prove that a listing should change its price.
        """),
            mo.ui.table(segment_errors, pagination=True),
            mo.md("**Largest absolute test errors: inspect before making recommendations**"),
            mo.ui.table(_errors.nlargest(20, "absolute_error"), pagination=True),
        ]
    )
    return (segment_errors,)


@app.cell
def _(alt, experiment, mo):
    importance_chart = mo.ui.altair_chart(
        alt.Chart(experiment.importance)
        .mark_bar()
        .encode(
            x=alt.X("MAE_increase:Q", title="Increase in validation MAE after shuffling"),
            y=alt.Y("attribute:N", sort=experiment.importance["attribute"].tolist(), title=None),
            tooltip=[
                "attribute:N",
                alt.Tooltip("MAE_increase:Q", format=".2f"),
                alt.Tooltip("repeat_std:Q", format=".2f"),
            ],
        )
        .properties(
            width="container",
            height=350,
            title="Permutation importance on a validation sample, before refitting",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    mo.vstack(
        [
            importance_chart,
            mo.md(
                "Three shuffles on up to 2,000 validation rows. Importance describes predictive reliance, not causal effects. Correlated attributes can share or mask importance; repeat standard deviations are not confidence intervals."
            ),
        ]
    )
    return (importance_chart,)


@app.cell
def _(experiment, mo):
    _help = mo.md("""
    ## 3 · Similar-listing explorer

    Choose a held-out source row. Comparables come from the reference train + validation
    rows, with the **same city, room type and weekday flag**. The query location is excluded;
    at most one result per reference location is shown. Source row numbers are zero-based CSV row indices, not listing IDs.
    """)
    query_city = mo.ui.dropdown(
        options=sorted(experiment.test["city"].unique()), value="london", label="Query city"
    )
    neighbour_count = mo.ui.slider(
        start=3, stop=15, step=1, value=5, label="Comparables", show_value=True
    )
    mo.vstack([_help, mo.hstack([query_city, neighbour_count])])
    return neighbour_count, query_city


@app.cell
def _(experiment, mo, query_city):
    _rows = experiment.test.loc[experiment.test["city"].eq(query_city.value), "source_row"].tolist()
    query_row = mo.ui.dropdown(options=_rows, value=_rows[0], label="Source row", searchable=True)
    query_row
    return (query_row,)


@app.cell
def _(FEATURES, experiment, mo, neighbour_count, query_row, similar_listings):
    query = experiment.test.loc[experiment.test["source_row"].eq(query_row.value)].iloc[0]
    neighbours = similar_listings(experiment.reference, query, k=neighbour_count.value)
    query_prediction = float(experiment.model.predict(query.to_frame().T[FEATURES])[0])
    mo.vstack(
        [
            mo.md(
                f"**Selected row:** {int(query['source_row'])} · **Observed price:** {query['realSum']:.2f} · **Predicted price:** {query_prediction:.2f}"
            ),
            mo.ui.table(
                query[
                    [
                        "city",
                        "room_type",
                        "weekday",
                        "realSum",
                        "person_capacity",
                        "bedrooms",
                        "dist",
                        "metro_dist",
                        "cleanliness_rating",
                        "guest_satisfaction_overall",
                    ]
                ]
                .to_frame("value")
                .reset_index(),
                pagination=False,
            ),
        ]
    )
    return neighbours, query, query_prediction


@app.cell
def _(SIMILARITY_FEATURES, alt, mo, neighbours, pd, query):
    mo.stop(neighbours.empty, mo.md("No eligible reference accommodations match this query."))
    _table_columns = [
        "source_row",
        "attribute_distance",
        "realSum",
        "person_capacity",
        "bedrooms",
        "dist",
        "metro_dist",
        "cleanliness_rating",
        "guest_satisfaction_overall",
    ]
    _comparison = pd.concat(
        [
            neighbours[["source_row", "realSum"]].assign(role="Comparable"),
            pd.DataFrame(
                [
                    {
                        "source_row": int(query["source_row"]),
                        "realSum": query["realSum"],
                        "role": "Query",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    comparable_chart = mo.ui.altair_chart(
        alt.Chart(_comparison)
        .mark_bar()
        .encode(
            x=alt.X("realSum:Q", title="Observed realSum (source price units)"),
            y=alt.Y("source_row:N", title="Source row"),
            color="role:N",
            tooltip=["source_row:N", "role:N", alt.Tooltip("realSum:Q", format=".2f")],
        )
        .properties(
            width="container",
            height=max(160, len(_comparison) * 26),
            title="Observed prices of the query and attribute-based comparables",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    mo.vstack(
        [
            mo.md(f"""
        **{len(neighbours)} comparables found.** Their median price is **{neighbours["realSum"].median():.2f}**;
        their middle 50% spans **{neighbours["realSum"].quantile(0.25):.2f}–{neighbours["realSum"].quantile(0.75):.2f}**.
        This is a descriptive comparable-price range, not a prediction interval.

        Attribute distance is the root-mean-square difference in reference-standardized attributes;
        lower means more similar. Equal standardized weights are an initial design choice.
        **Price is excluded from ranking.** Features: {", ".join(SIMILARITY_FEATURES)}.
        The ranking has not been evaluated against guest preferences or booking decisions.
        """),
            comparable_chart,
            mo.ui.table(neighbours[_table_columns], pagination=False),
        ]
    )
    return (comparable_chart,)


@app.cell
def _(cross_fitted_prices, experiment, modelling_data):
    pricing_gaps = cross_fitted_prices(modelling_data, experiment.model)
    return (pricing_gaps,)


@app.cell
def _(mo):
    _help = mo.md("""
    ## 4 · Quantify a price-gap scenario

    Use the model to identify review candidates, then ask what would happen **if** prices
    changed while booking volume followed an assumed scenario. The full snapshot is scored
    with five-fold location-group cross-fitting: each observation's location group is excluded
    from that fold's training data. The model specification was selected earlier, so this is
    an exploratory scenario, not a new independent accuracy evaluation.

    **Baseline assumption: one equal-size, like-for-like sale per snapshot observation.**
    Only selected below-benchmark prices increase; all other prices and volumes stay unchanged.
    A common proportional booking-volume change is applied to the selected cohort.
    This equal weighting is necessary because actual bookings are absent. The result is a
    hypothetical gross-value calculation, not host earnings, Airbnb revenue or an annual forecast.
    Observations can repeat properties; these counts are not counts of unique listings.
    """)
    gap_threshold = mo.ui.slider(
        start=0,
        stop=50,
        step=5,
        value=0,
        label="Minimum increase to reach benchmark (%)",
        show_value=True,
    )
    gap_move = mo.ui.slider(
        start=0,
        stop=100,
        step=25,
        value=100,
        label="Share of price gap applied (%)",
        show_value=True,
    )
    candidate_volume = mo.ui.slider(
        start=50,
        stop=110,
        step=5,
        value=100,
        label="Candidate booking volume retained (%)",
        show_value=True,
    )
    mo.vstack([_help, mo.hstack([gap_threshold, gap_move, candidate_volume])])
    return candidate_volume, gap_move, gap_threshold


@app.cell
def _(candidate_volume, gap_move, gap_threshold, mo, pd, price_gap_scenario, pricing_gaps):
    scenario = price_gap_scenario(
        pricing_gaps,
        minimum_gap_pct=gap_threshold.value,
        move_fraction=gap_move.value / 100,
        volume_retention=candidate_volume.value / 100,
    )
    scenario_summary = pd.DataFrame([scenario])
    _baseline = scenario["baseline_all"]
    _cohort = scenario["candidate_observations"]
    _break_even = scenario["break_even_volume_retention"]
    _break_even_text = f"{100 * _break_even:.1f}%" if pd.notna(_break_even) else "not applicable"
    mo.md(f"""
    ### Scenario result

    **{_cohort:,} of {len(pricing_gaps):,} observations** qualify for a potential increase review.
    At unchanged volume, the selected price adjustment adds **{scenario["change_at_constant_volume"]:,.0f} source price units**
    to the one-sale-per-observation scenario. For this cohort, the aggregate price increase is
    **{scenario["cohort_price_change_pct"]:.1f}%**.

    With the selected volume assumption, the overall scenario changes from **{_baseline:,.0f}**
    to **{scenario["scenario_all"]:,.0f}**, a change of **{scenario["scenario_change"]:,.0f} ({scenario["scenario_change_pct"]:+.2f}%)**.
    The candidate cohort breaks even at **{_break_even_text}** of baseline volume under these assumptions.

    Formula: scenario change = retained volume × (candidate baseline + applied price gap) − candidate baseline.

    **Interpretation:** this measures a conditional price gap. Even an unbiased, noisy model
    produces positive gaps when only observations below prediction are selected. Gaps can
    therefore reflect prediction error, omitted amenities or genuine price differences;
    the model's overall test median absolute percentage error is about 18%. A threshold
    filters the review queue; it is not a confidence interval or evidence of achievable uplift.
    """)
    return scenario, scenario_summary


@app.cell
def _(gap_move, gap_threshold, pd, price_gap_scenario, pricing_gaps):
    volume_sensitivity = pd.DataFrame(
        [
            {
                "booking_volume_change_pct": retained - 100,
                "price_gap_applied": f"{applied}% of price gap",
                **price_gap_scenario(
                    pricing_gaps,
                    minimum_gap_pct=gap_threshold.value,
                    move_fraction=applied / 100,
                    volume_retention=retained / 100,
                ),
            }
            for applied in [25, 50, 100]
            for retained in range(50, 111, 5)
        ]
    )
    city_price_scenarios = pd.DataFrame(
        [
            {
                "city": city,
                **price_gap_scenario(
                    group,
                    minimum_gap_pct=gap_threshold.value,
                    move_fraction=gap_move.value / 100,
                ),
            }
            for city, group in pricing_gaps.groupby("city", observed=True)
        ]
    )
    return city_price_scenarios, volume_sensitivity


@app.cell
def _(
    alt,
    candidate_volume,
    gap_threshold,
    mo,
    pd,
    save_presentation_chart,
    scenario,
    volume_sensitivity,
):
    _lines = (
        alt.Chart(volume_sensitivity)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "booking_volume_change_pct:Q",
                title="Assumed change in candidate booking volume (%)",
                axis=alt.Axis(values=[-50, -40, -30, -20, -10, 0, 10]),
            ),
            y=alt.Y("scenario_change_pct:Q", title="Change in overall scenario gross value (%)"),
            color=alt.Color(
                "price_gap_applied:N",
                title="Price adjustment",
                sort=["25% of price gap", "50% of price gap", "100% of price gap"],
            ),
            tooltip=[
                "price_gap_applied:N",
                "booking_volume_change_pct:Q",
                alt.Tooltip("scenario_change_pct:Q", format="+.2f"),
                alt.Tooltip("scenario_change:Q", format=",.0f"),
            ],
        )
    )
    _zero = (
        alt.Chart(alt.Data(values=[{"zero": 0}]))
        .mark_rule(color="#64748b", strokeDash=[5, 5])
        .encode(y="zero:Q")
    )
    _selected = (
        alt.Chart(
            pd.DataFrame(
                [
                    {
                        "booking_volume_change_pct": candidate_volume.value - 100,
                        "scenario_change_pct": scenario["scenario_change_pct"],
                    }
                ]
            )
        )
        .mark_point(color="black", filled=True, size=140)
        .encode(
            x="booking_volume_change_pct:Q",
            y="scenario_change_pct:Q",
        )
    )
    price_sensitivity_chart = mo.ui.altair_chart(
        (_lines + _zero + _selected).properties(
            width="container",
            height=400,
            title=alt.TitleParams(
                text="How sensitive is the price-gap scenario to booking volume?",
                subtitle=[
                    "One equal-size sale per observation at baseline; all other observations unchanged",
                    f"Candidate price gap > {gap_threshold.value}%; booking-volume changes are assumptions, not predictions",
                ],
            ),
        ),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(price_sensitivity_chart, "03_modelling/price_gap_volume_sensitivity")
    mo.vstack(
        [
            price_sensitivity_chart,
            mo.md(
                "The black point shows the current controls. The model does not estimate any of these booking-volume responses."
            ),
        ]
    )
    return (price_sensitivity_chart,)


@app.cell
def _(city_price_scenarios, gap_threshold, mo, pricing_gaps):
    pricing_review = pricing_gaps.copy()
    pricing_review["review_category"] = pricing_review["price_gap_pct"].map(
        lambda gap: (
            "Below benchmark: increase review"
            if gap > gap_threshold.value
            else "Above benchmark: premium/utilization review"
            if gap < -gap_threshold.value
            else "Within review threshold"
        )
    )
    mo.vstack(
        [
            mo.md("""
        ### Turn gaps into a review process

        - **Below benchmark:** if utilization is already high, test a gradual increase. If utilization is low, investigate demand and listing quality before raising prices.
        - **Above benchmark:** if utilization is low, test a reduction. If utilization is high, the premium may be justified.
        - **Current limitation:** utilization is unavailable here, so these are conditional actions, not assigned utilization labels. A 10% price cut would need 11.1% more booked volume to preserve gross value, before considering costs.

        **City scenarios below assume unchanged booking volume.** Sample coverage influences the absolute totals.
        """),
            mo.ui.table(
                city_price_scenarios[
                    [
                        "city",
                        "observations",
                        "candidate_observations",
                        "baseline_all",
                        "change_at_constant_volume",
                        "scenario_change_pct",
                    ]
                ],
                pagination=False,
            ),
            mo.md(
                "**Review queue: largest absolute benchmark gaps, not confirmed pricing errors**"
            ),
            mo.ui.table(
                pricing_review.loc[pricing_review["review_category"].ne("Within review threshold")]
                .assign(_absolute_gap=lambda x: x["price_gap"].abs())
                .nlargest(20, "_absolute_gap")
                .drop(columns="_absolute_gap"),
                pagination=True,
            ),
        ]
    )
    return (pricing_review,)


@app.cell
def _(mo):
    save_results = mo.ui.run_button(label="Save results, split audit and trained model to outputs/")
    save_results
    return (save_results,)


@app.cell
def _(
    DATA_PATH,
    FEATURES,
    PROJECT_ROOT,
    SEED,
    experiment,
    city_price_scenarios,
    hashlib,
    json,
    mo,
    pricing_gaps,
    pricing_review,
    save_price_model,
    save_results,
    segment_errors,
    scenario,
    scenario_summary,
    sklearn,
    volume_sensitivity,
):
    mo.stop(not save_results.value)
    _output = PROJECT_ROOT / "outputs" / "tables" / "03_modelling"
    _output.mkdir(parents=True, exist_ok=True)
    for _name, _table in {
        "validation_scores": experiment.validation_scores,
        "test_scores": experiment.test_scores,
        "test_predictions": experiment.test_predictions,
        "segment_errors": segment_errors,
        "permutation_importance": experiment.importance,
        "split_summary": experiment.split_summary,
        "split_assignments": experiment.split_assignments,
        "cross_fitted_prices": pricing_gaps,
        "pricing_review": pricing_review,
        "price_gap_scenario": scenario_summary,
        "city_price_scenarios": city_price_scenarios,
        "volume_sensitivity": volume_sensitivity,
    }.items():
        _table.to_csv(_output / f"{_name}.csv", index=False)
    (_output / "experiment.json").write_text(
        json.dumps(
            {
                "input_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
                "seed": SEED,
                "sklearn_version": sklearn.__version__,
                "features": FEATURES,
                "selected_model": experiment.winner,
                "model_specification": repr(experiment.model),
                "grouping": ["city", "lng", "lat"],
                "selection_metric": "validation MAE",
                "price_scenario": {
                    "cross_fit_folds": 5,
                    "basis": "One equal-size sale per snapshot observation; non-candidate prices and volumes unchanged",
                    "is_revenue_forecast": False,
                    "minimum_gap_pct": scenario["minimum_gap_pct"],
                    "move_fraction": scenario["move_fraction"],
                    "volume_retention": scenario["volume_retention"],
                },
            },
            indent=2,
        )
        + "\n"
    )
    _model_path = save_price_model(experiment, PROJECT_ROOT / "outputs" / "models", DATA_PATH)
    mo.md(
        f"Saved metrics, predictions and split audit to {_output} and the trained model to {_model_path}."
    )
    return


if __name__ == "__main__":
    app.run()
