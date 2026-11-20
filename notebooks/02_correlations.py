import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    from airbnb_analytics.charts import FIGURE_DIR, save_presentation_chart
    from airbnb_analytics.data import load_listings

    return FIGURE_DIR, alt, load_listings, mo, np, pd, plt, save_presentation_chart, sns


@app.cell
def _(mo):
    mo.md("""
    # 02 · Investigate relationships

    Which attributes are associated with price, and does that relationship hold within
    cities and room types? Compare Pearson (linear) and Spearman (rank) correlations,
    inspect individual pairs, then check outliers and redundant attributes.

    Correlations are descriptive and do not establish causality. `realSum` is the source
    price field; its stay duration is unconfirmed. Coefficients use finite, pairwise complete observations.
    Latitude and longitude are excluded from all correlation analyses and pair selectors.
    Attraction and restaurant indices use only their normalized versions to avoid duplicate representations.
    """)
    return


@app.cell
def _(np):
    def pair_coefficient(frame, x, y, method):
        pair = frame[[x, y]].dropna()
        if len(pair) < 3 or pair.nunique().min() < 2:
            return np.nan
        return pair[x].corr(pair[y], method=method)

    return (pair_coefficient,)


@app.cell
def _(load_listings):
    listings = load_listings().drop(columns=["lat", "lng", "attr_index", "rest_index"])
    return (listings,)


@app.cell
def _(listings, mo):
    city_filter = mo.ui.dropdown(
        options=["All cities", *sorted(listings["city"].unique())], value="All cities", label="City"
    )
    method = mo.ui.dropdown(options=["pearson", "spearman"], value="spearman", label="Method")
    room_filter = mo.ui.dropdown(
        options=["All room types", *sorted(listings["room_type"].unique())],
        value="All room types",
        label="Room type",
    )
    mo.hstack([city_filter, room_filter, method])
    return city_filter, method, room_filter


@app.cell
def _(city_filter, listings, method, np, room_filter):
    room_scope = (
        listings
        if room_filter.value == "All room types"
        else listings.loc[listings["room_type"].eq(room_filter.value)]
    )
    selected = (
        room_scope
        if city_filter.value == "All cities"
        else room_scope.loc[room_scope["city"].eq(city_filter.value)]
    )
    numeric = (
        selected.select_dtypes(include=["number", "bool"])
        .astype(float)
        .replace([np.inf, -np.inf], np.nan)
    )
    corr = numeric.corr(method=method.value)
    features = [c for c in numeric.columns if c != "realSum"]
    return corr, features, numeric, room_scope, selected


@app.cell
def _(city_filter, mo, room_filter, selected):
    mo.md(f"""
    **Segment:** {city_filter.value} / {room_filter.value} · **{len(selected):,} rows**

    ## 1 · Which attributes are associated with price?

    A large difference between Pearson and Spearman is a reason to inspect skew,
    outliers and nonlinear patterns. Binary flags describe group differences and should
    be interpreted according to their category definitions.
    """)
    return


@app.cell
def _(
    alt,
    city_filter,
    features,
    mo,
    numeric,
    pair_coefficient,
    pd,
    room_filter,
    save_presentation_chart,
):
    price_relationships = pd.DataFrame(
        {
            "attribute": features,
            "Pearson": [pair_coefficient(numeric, c, "realSum", "pearson") for c in features],
            "Spearman": [pair_coefficient(numeric, c, "realSum", "spearman") for c in features],
            "paired_rows": [numeric[[c, "realSum"]].dropna().shape[0] for c in features],
        }
    )
    _order = price_relationships.sort_values("Spearman", key=abs, ascending=False)[
        "attribute"
    ].tolist()
    _long = price_relationships.melt(
        id_vars=["attribute", "paired_rows"],
        value_vars=["Pearson", "Spearman"],
        var_name="method",
        value_name="correlation",
    ).dropna(subset=["correlation"])
    price_rank_chart = mo.ui.altair_chart(
        alt.Chart(_long)
        .mark_point(filled=True, size=90)
        .encode(
            x=alt.X(
                "correlation:Q", scale=alt.Scale(domain=[-1, 1]), title="Correlation with realSum"
            ),
            y=alt.Y("attribute:N", sort=_order, title=None),
            color=alt.Color("method:N", title=None),
            shape="method:N",
            tooltip=[
                "attribute:N",
                "method:N",
                alt.Tooltip("correlation:Q", format=".3f"),
                "paired_rows:Q",
            ],
        )
        .properties(
            width="container",
            height=470,
            title="Price relationships, ranked by absolute Spearman correlation",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(
        price_rank_chart.properties(
            title=alt.TitleParams(
                text="Accommodation attributes associated with price",
                subtitle=f"{city_filter.value} | {room_filter.value} | Pearson and Spearman",
            )
        ),
        "02_correlations/price_relationships",
    )
    mo.vstack([price_rank_chart, mo.ui.table(price_relationships, pagination=True)])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 2 · Does pooling cities hide relationships?

    This panel compares **all cities**, regardless of the city selector. It follows the
    **room-type filter and method selector**. Compare each city with the `All cities`
    column before generalizing across Europe. Hover for coefficients and paired row counts.
    Blank cells indicate insufficient variation or observations.
    """)
    return


@app.cell
def _(features, method, np, pd, room_scope):
    _records = []
    for _city, _frame in [
        ("All cities", room_scope),
        *list(room_scope.groupby("city", observed=True)),
    ]:
        _numeric = (
            _frame.select_dtypes(include=["number", "bool"])
            .astype(float)
            .replace([np.inf, -np.inf], np.nan)
        )
        for _feature in features:
            _pair = _numeric[[_feature, "realSum"]].dropna()
            _coefficient = (
                _pair[_feature].corr(_pair["realSum"], method=method.value)
                if len(_pair) >= 3 and _pair.nunique().min() > 1
                else np.nan
            )
            _records.append(
                {
                    "city": _city,
                    "attribute": _feature,
                    "correlation": _coefficient,
                    "paired_rows": len(_pair),
                }
            )
    city_correlations = pd.DataFrame(_records)
    return (city_correlations,)


@app.cell
def _(alt, city_correlations, method, mo, pd, room_filter, save_presentation_chart):
    _within_city = city_correlations.loc[~city_correlations["city"].eq("All cities")].dropna(
        subset=["correlation"]
    )
    _ranked = []
    for _direction, _positive in [("Positive", True), ("Negative", False)]:
        _eligible = _within_city.loc[
            _within_city["correlation"].gt(0) if _positive else _within_city["correlation"].lt(0)
        ]
        _top = (
            _eligible.sort_values(
                ["city", "correlation", "attribute"], ascending=[True, not _positive, True]
            )
            .groupby("city", sort=False)
            .head(3)
            .copy()
        )
        _top["direction"] = _direction
        _top["rank"] = _top.groupby("city").cumcount() + 1
        _ranked.append(_top)
    top_city_correlations = pd.concat(_ranked, ignore_index=True)
    city_top_correlations_chart = mo.ui.altair_chart(
        alt.Chart(top_city_correlations)
        .mark_bar()
        .encode(
            x=alt.X(
                "correlation:Q",
                scale=alt.Scale(domain=[-1, 1]),
                title=f"{method.value.title()} correlation with realSum",
                axis=alt.Axis(values=[-1, -0.5, 0, 0.5, 1]),
            ),
            y=alt.Y(
                "attribute:N",
                title=None,
                sort=alt.SortField("correlation", order="descending"),
                axis=alt.Axis(labelLimit=300, labelFontSize=15),
            ),
            color=alt.Color(
                "direction:N",
                title=None,
                scale=alt.Scale(domain=["Positive", "Negative"], range=["#2563eb", "#ea580c"]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                "city:N",
                "attribute:N",
                "direction:N",
                "rank:Q",
                alt.Tooltip("correlation:Q", format=".3f"),
                "paired_rows:Q",
            ],
        )
        .properties(width=280, height=170)
        .facet(facet=alt.Facet("city:N", title=None), columns=2)
        .resolve_scale(y="independent")
        .properties(title="Each city's three strongest positive and negative price correlations"),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(
        city_top_correlations_chart.properties(
            title=alt.TitleParams(
                text="Strongest positive and negative price correlations by city",
                subtitle=f"{method.value.title()} | {room_filter.value} | Up to three of each sign",
            )
        ),
        "02_correlations/price_correlations_per_city",
        width=420,
        height=210,
    )
    for _city in sorted(top_city_correlations["city"].unique()):
        _single_city = city_top_correlations_chart.spec.copy(deep=True)
        _single_city.data = top_city_correlations.loc[top_city_correlations["city"].eq(_city)]
        _single_city = _single_city.properties(
            title=alt.TitleParams(
                text=f"{_city.title()}: strongest price correlations",
                subtitle=f"{method.value.title()} | {room_filter.value} | Up to three of each sign",
            )
        )
        save_presentation_chart(_single_city, f"02_correlations/cities/{_city}_price_correlations")
    mo.vstack(
        [
            mo.md(f"""
        ### Compare the strongest relationships in each city

        **Method:** {method.value.title()} · **Room type:** {room_filter.value}.
        All cities are shown together; the city selector does not restrict this chart.
        Each panel uses the same −1 to +1 scale and independently ranks its attributes.
        Blue bars are the three largest positive coefficients; orange bars are the three
        most negative. Hover for exact coefficients, sign-specific rank and paired row counts.

        Fewer bars appear when a city has fewer than three valid correlations of either sign.
        Zero and undefined coefficients are omitted. Only normalized attraction and restaurant
        indices are included. A top-three ranking does not imply a strong or significant relationship.
        """),
            city_top_correlations_chart,
        ]
    )
    return


@app.cell
def _(alt, city_correlations, method, mo, room_filter, room_scope, save_presentation_chart):
    _order = (
        city_correlations.loc[city_correlations["city"].eq("All cities")]
        .sort_values("correlation", key=abs, ascending=False)["attribute"]
        .tolist()
    )
    city_corr_chart = mo.ui.altair_chart(
        alt.Chart(city_correlations)
        .mark_rect()
        .encode(
            x=alt.X(
                "city:N",
                sort=["All cities", *sorted(room_scope["city"].unique())],
                title=None,
                axis=alt.Axis(labelAngle=-40),
            ),
            y=alt.Y("attribute:N", sort=_order, title=None),
            color=alt.Color(
                "correlation:Q",
                scale=alt.Scale(domain=[-1, 1], scheme="redblue", reverse=True),
                title="Correlation",
            ),
            tooltip=[
                "city:N",
                "attribute:N",
                alt.Tooltip("correlation:Q", format=".3f"),
                "paired_rows:Q",
            ],
        )
        .properties(
            width="container",
            height=440,
            title=f"{method.value.title()} correlation with price, within each city",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(
        city_corr_chart.properties(
            title=alt.TitleParams(
                text="Price correlations within each city",
                subtitle=f"{method.value.title()} | {room_filter.value}",
            )
        ),
        "02_correlations/city_corr_chart",
    )
    city_corr_chart
    return


@app.cell
def _(city_correlations, method, mo, room_filter):
    _messages = []
    for _feature, _label in [
        ("dist", "Distance to city centre"),
        ("person_capacity", "Person capacity"),
    ]:
        _values = city_correlations.loc[city_correlations["attribute"].eq(_feature)]
        _pooled = _values.loc[_values["city"].eq("All cities"), "correlation"].iloc[0]
        _cities = _values.loc[~_values["city"].eq("All cities")].dropna(subset=["correlation"])
        if len(_cities) and _pooled == _pooled:
            _messages.append(
                f"- **{_label}:** pooled {method.value} = **{_pooled:.2f}**; within-city range **{_cities['correlation'].min():.2f} to {_cities['correlation'].max():.2f}** across {len(_cities)} cities."
            )
    mo.md(f"""
    ### What changes after separating cities?

    Room-type scope: **{room_filter.value}**.

    {chr(10).join(_messages)}

    These comparisons do not adjust for all other attributes. Use the room-type filter
    to check another source of accommodation mix. A stronger within-city correlation
    supports local benchmarking; it does not quantify the effect of moving a listing
    or increasing its capacity.
    """)
    return


@app.cell
def _(mo, numeric):
    _help = mo.md("""
    ## 3 · Inspect a pair and check outlier sensitivity

    Both segment filters apply. Statistics use every eligible pair; only plotted points
    are sampled. The second statistics row trims both variables to their segment-specific
    1st–99th percentiles as a sensitivity check, not as an automatic cleaning rule.
    """)
    pair_x = mo.ui.dropdown(options=list(numeric.columns), value="dist", label="X attribute")
    pair_y = mo.ui.dropdown(options=list(numeric.columns), value="realSum", label="Y attribute")
    log_price_axis = mo.ui.checkbox(value=True, label="Log axis when plotting realSum")
    mo.vstack([_help, mo.hstack([pair_x, pair_y, log_price_axis])])
    return log_price_axis, pair_x, pair_y


@app.cell
def _(mo, np, pair_x, pair_y, pd, selected):
    mo.stop(
        pair_x.value == pair_y.value, mo.md("Choose two different attributes to inspect a pair.")
    )
    pair_data = (
        selected[[pair_x.value, pair_y.value]]
        .astype(float)
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    _trimmed = pair_data.loc[
        pair_data.ge(pair_data.quantile(0.01)).all(axis=1)
        & pair_data.le(pair_data.quantile(0.99)).all(axis=1)
    ]
    _stats = []
    for _name, _data in [
        ("All finite pairs", pair_data),
        ("Central 98% of each variable", _trimmed),
    ]:
        _valid = len(_data) >= 3 and _data.nunique().min() > 1
        _stats.append(
            {
                "scope": _name,
                "paired_rows": len(_data),
                "pearson": _data[pair_x.value].corr(_data[pair_y.value], method="pearson")
                if _valid
                else np.nan,
                "spearman": _data[pair_x.value].corr(_data[pair_y.value], method="spearman")
                if _valid
                else np.nan,
            }
        )
    pair_statistics = pd.DataFrame(_stats)
    mo.ui.table(pair_statistics, pagination=False)
    return (pair_data,)


@app.cell
def _(
    alt,
    city_filter,
    log_price_axis,
    mo,
    pair_data,
    pair_x,
    pair_y,
    room_filter,
    save_presentation_chart,
    selected,
):
    _plot_data = pair_data.join(selected[["city", "room_type"]])
    for _column in [pair_x.value, pair_y.value]:
        if log_price_axis.value and _column == "realSum":
            _plot_data = _plot_data.loc[_plot_data[_column].gt(0)]
    _sample = _plot_data.sample(n=min(5000, len(_plot_data)), random_state=42)
    pair_scatter = mo.ui.altair_chart(
        alt.Chart(_sample)
        .mark_point(filled=True, opacity=0.35, size=30)
        .encode(
            x=alt.X(
                f"{pair_x.value}:Q",
                scale=alt.Scale(
                    type="log" if log_price_axis.value and pair_x.value == "realSum" else "linear"
                ),
            ),
            y=alt.Y(
                f"{pair_y.value}:Q",
                scale=alt.Scale(
                    type="log" if log_price_axis.value and pair_y.value == "realSum" else "linear"
                ),
            ),
            color=alt.Color("city:N", title="City"),
            tooltip=[
                "city:N",
                "room_type:N",
                alt.Tooltip(f"{pair_x.value}:Q", format=".3f"),
                alt.Tooltip(f"{pair_y.value}:Q", format=".3f"),
            ],
        )
        .properties(width="container", height=340, title=f"{pair_y.value} versus {pair_x.value}"),
        chart_selection="interval",
        legend_selection=True,
    )
    save_presentation_chart(
        pair_scatter.properties(
            title=alt.TitleParams(
                text=f"{pair_y.value} versus {pair_x.value}",
                subtitle=f"{city_filter.value} | {room_filter.value} | {len(_sample):,} plotted rows",
            )
        ),
        "02_correlations/pair_scatter",
    )
    mo.vstack(
        [
            pair_scatter,
            mo.md(
                f"**{len(_sample):,} plotted / {len(_plot_data):,} eligible / {len(pair_data):,} finite pairs.** Points are sampled with a fixed seed, capped at 5,000. Log-price views omit non-positive prices from the plot only. Drag to select points. Pearson statistics use the original values even when the axis is logarithmic."
            ),
        ]
    )
    return (pair_scatter,)


@app.cell
def _(mo, pair_scatter):
    mo.ui.table(pair_scatter.value, pagination=True, label="Selected scatterplot rows")
    return


@app.cell
def _(mo):
    _help = mo.md("""
    ## 4 · Which attributes repeat similar information?

    Feature-to-feature correlations can reveal redundant encodings and unstable model
    coefficients. Only normalized attraction and restaurant indices are included;
    they can still share information with other location attributes. Room indicators are derived from room type.
    Review strong pairs before treating them as separate drivers.
    """)
    threshold = mo.ui.slider(
        start=0.0,
        stop=1.0,
        step=0.05,
        value=0.7,
        label="Minimum absolute feature correlation",
        show_value=True,
    )
    mo.vstack([_help, threshold])
    return (threshold,)


@app.cell
def _(
    alt, city_filter, corr, method, mo, np, numeric, room_filter, save_presentation_chart, threshold
):
    _feature_corr = corr.drop(index="realSum", columns="realSum")
    pairs = (
        _feature_corr.where(np.triu(np.ones(_feature_corr.shape, dtype=bool), k=1))
        .stack()
        .rename("correlation")
        .rename_axis(["attribute_1", "attribute_2"])
        .reset_index()
    )
    pairs["absolute_correlation"] = pairs["correlation"].abs()
    pairs["paired_rows"] = [
        numeric[[a, b]].dropna().shape[0]
        for a, b in zip(pairs["attribute_1"], pairs["attribute_2"], strict=True)
    ]
    strong_pairs = pairs.loc[pairs["absolute_correlation"].ge(threshold.value)].sort_values(
        "absolute_correlation", ascending=False
    )
    _top = strong_pairs.head(15).copy()
    _top["pair"] = _top["attribute_1"] + " / " + _top["attribute_2"]
    redundancy_chart = mo.ui.altair_chart(
        alt.Chart(_top)
        .mark_bar()
        .encode(
            x=alt.X(
                "correlation:Q",
                scale=alt.Scale(domain=[-1, 1]),
                title="Feature-to-feature correlation",
            ),
            y=alt.Y("pair:N", sort=_top["pair"].tolist(), title=None),
            color=alt.Color(
                "correlation:Q",
                scale=alt.Scale(domain=[-1, 1], scheme="redblue", reverse=True),
                legend=None,
            ),
            tooltip=[
                "attribute_1:N",
                "attribute_2:N",
                alt.Tooltip("correlation:Q", format=".3f"),
                "paired_rows:Q",
            ],
        )
        .properties(
            width="container",
            height=max(100, len(_top) * 28),
            title="Up to 15 strongest feature pairs above the threshold",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(
        redundancy_chart.properties(
            title=alt.TitleParams(
                text="Strongest feature-to-feature correlations",
                subtitle=f"{method.value.title()} | {city_filter.value} | {room_filter.value} | Minimum absolute correlation: {threshold.value:.2f}",
            )
        ),
        "02_correlations/redundancy_chart",
    )
    mo.vstack(
        [
            redundancy_chart,
            mo.ui.table(strong_pairs, pagination=True),
            mo.md(
                f"{len(strong_pairs)} pairs meet the threshold. An empty chart means no pair qualifies. The threshold is exploratory, not a significance test."
            ),
        ]
    )
    return


@app.cell
def _(FIGURE_DIR, city_filter, corr, method, mo, np, plt, room_filter, selected, sns):
    corr_fig, corr_ax = plt.subplots(figsize=(13, 11))
    sns.heatmap(
        corr,
        mask=np.triu(np.ones(corr.shape, dtype=bool), k=1),
        vmin=-1,
        vmax=1,
        center=0,
        cmap="vlag",
        square=True,
        ax=corr_ax,
    )
    corr_ax.set_title(
        f"{method.value.title()} correlation · {city_filter.value} · {room_filter.value} · {len(selected):,} rows"
    )
    corr_fig.tight_layout()
    _figure_path = FIGURE_DIR / "02_correlations" / "full_correlation_matrix"
    _figure_path.parent.mkdir(parents=True, exist_ok=True)
    corr_fig.savefig(
        _figure_path.with_suffix(".png"), dpi=300, bbox_inches="tight", facecolor="white"
    )
    corr_fig.savefig(_figure_path.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    mo.accordion({"Reference: full correlation matrix": corr_fig})
    return


@app.cell
def _(mo):
    mo.md("""
    ## Before choosing a slide message

    - Separate derived encodings (`room_type` and room indicators) from new information; raw index duplicates are already excluded.
    - Compare pooled correlations with each city's results to check for differences hidden by aggregation.
    - Inspect scatterplots and price outliers. A missing coefficient can mean a constant feature.
    - Correlations use pairwise complete observations. Check the paired row counts before comparing them.
    - Weak pairwise correlation can still hide nonlinear or conditional relationships.
    - Quantify uncertainty before client claims. Repeated observations may invalidate row-level confidence intervals; no explicit listing or host ID is supplied.
    - Test pricing recommendations with booking and conversion outcomes before claiming uplift.

    Charts are saved automatically as high-resolution PNG and vector SVG files under
    outputs/figures/02_correlations using the current filters. Single charts use a fixed
    1200 × 675 presentation canvas and scale_factor=3 (3600 × 2025 PNG pixels).
    The ten-city overview keeps its facet grid; individual city versions are exported to the cities subfolder.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
 
    """)
    return


if __name__ == "__main__":
    app.run()
