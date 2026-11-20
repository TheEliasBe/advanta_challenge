import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    from airbnb_analytics.charts import save_presentation_chart
    from airbnb_analytics.data import column_profile, load_dictionary, load_listings

    return alt, column_profile, load_dictionary, load_listings, mo, np, pd, save_presentation_chart


@app.cell
def _(mo):
    mo.md("""
    # 01 · Understand the data

    Start with the source catalogue, coverage and data quality before interpreting relationships.
    Source rows are retained as supplied. Price is labelled `realSum`; its stay duration is unconfirmed.
    """)
    return


@app.cell
def _(load_dictionary, load_listings):
    listings = load_listings()
    catalogue = load_dictionary()
    return catalogue, listings


@app.cell
def _(listings, mo):
    mo.md(f"""
    **{len(listings):,} rows** · **{listings.shape[1]} columns** ·
    **{listings["city"].nunique()} cities** · **{listings.duplicated().sum():,} exact duplicate rows**
    """)
    return


@app.cell
def _(catalogue, mo):
    mo.ui.table(catalogue, pagination=False)
    return


@app.cell
def _(column_profile, listings, mo):
    mo.ui.table(column_profile(listings), pagination=False)
    return


@app.cell
def _(listings, mo):
    city_filter = mo.ui.dropdown(
        options=["All cities", *sorted(listings["city"].unique())], value="All cities", label="City"
    )
    city_filter
    return (city_filter,)


@app.cell
def _(city_filter, listings):
    selected = (
        listings
        if city_filter.value == "All cities"
        else listings.loc[listings["city"].eq(city_filter.value)]
    )
    return (selected,)


@app.cell
def _(mo, selected):
    mo.ui.table(selected.head(100), pagination=True)
    return


@app.cell
def _(mo, selected):
    mo.ui.table(selected.describe(include="all").T.reset_index(), pagination=True)
    return


@app.cell
def _(mo, np, selected):
    price_data = selected.loc[np.isfinite(selected["realSum"]) & selected["realSum"].gt(0)]
    mo.md(f"""
    ## Compare price distributions

    Charts follow the city filter above. Price axes use a logarithmic scale to show the
    full range without trimming expensive accommodations. Prices are in USD according to
    the catalogue; the stay duration remains unconfirmed.

    **{len(price_data):,} rows plotted**; **{len(selected) - len(price_data):,} rows excluded**
    because price is missing, non-finite or non-positive. Source data is unchanged.
    """)
    return (price_data,)


@app.cell
def _(alt, mo, np, pd, price_data, save_presentation_chart):
    # Aggregate every valid price before sending data to the browser.
    # All cities share the same log-spaced bin boundaries.
    _edges = np.geomspace(price_data["realSum"].min(), price_data["realSum"].max(), 41)
    _bins = []
    for _city, _group in price_data.groupby("city", observed=True):
        _counts, _ = np.histogram(_group["realSum"], bins=_edges)
        _bins.append(
            pd.DataFrame(
                {
                    "city": _city,
                    "price_from": _edges[:-1],
                    "price_to": _edges[1:],
                    "rows": _counts,
                    "share": _counts / len(_group),
                }
            )
        )
    price_bins = pd.concat(_bins, ignore_index=True)
    distribution_chart = mo.ui.altair_chart(
        alt.Chart(price_bins)
        .mark_bar()
        .encode(
            x=alt.X(
                "price_from:Q",
                bin="binned",
                scale=alt.Scale(type="log"),
                title="realSum (USD, log scale)",
            ),
            x2="price_to:Q",
            y=alt.Y("share:Q", axis=alt.Axis(format=".0%"), title="Share of city rows"),
            color=alt.Color("city:N", legend=None),
            tooltip=[
                "city:N",
                alt.Tooltip("price_from:Q", format=",.0f"),
                alt.Tooltip("price_to:Q", format=",.0f"),
                "rows:Q",
                alt.Tooltip("share:Q", format=".1%"),
            ],
        )
        .properties(width=380, height=130)
        .facet(facet=alt.Facet("city:N", title=None), columns=2)
        .properties(title="Price distribution within each city"),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(
        distribution_chart, "01_exploration/price_distribution_each_city", width=440, height=190
    )
    distribution_chart
    return


@app.cell
def _(alt, mo, price_data, save_presentation_chart):
    city_prices = (
        price_data.groupby("city", observed=True)["realSum"]
        .agg(
            rows="size",
            p10=lambda s: s.quantile(0.1),
            q1=lambda s: s.quantile(0.25),
            median="median",
            q3=lambda s: s.quantile(0.75),
            p90=lambda s: s.quantile(0.9),
        )
        .reset_index()
    )
    _base = alt.Chart(city_prices).encode(
        y=alt.Y("city:N", sort=alt.SortField("median", order="descending"), title=None),
        tooltip=[
            "city:N",
            "rows:Q",
            *[alt.Tooltip(f"{q}:Q", format=",.0f") for q in ["p10", "q1", "median", "q3", "p90"]],
        ],
    )
    _range = _base.mark_rule(color="#94a3b8", strokeWidth=2).encode(
        x=alt.X("p10:Q", scale=alt.Scale(domainMin=30, nice=False), title="realSum"),
        x2="p90:Q",
    )
    _middle = _base.mark_bar(color="#38bdf8", size=16).encode(x="q1:Q", x2="q3:Q")
    _median = _base.mark_tick(color="#0f172a", thickness=3, size=22).encode(x="median:Q")
    city_price_chart = mo.ui.altair_chart(
        (_range + _middle + _median).properties(
            width="container",
            height=max(90, len(city_prices) * 32),
            title="City prices: 10th-90th percentile, middle 50% and median",
        ),
        chart_selection=False,
        legend_selection=False,
    )
    save_presentation_chart(city_price_chart, "01_exploration/city_price_chart")
    city_price_chart
    return


@app.cell
def _(alt, mo, price_data, save_presentation_chart):
    room_prices = (
        price_data.groupby(["city", "room_type"], observed=True)["realSum"]
        .agg(median_price="median", rows="size")
        .reset_index()
    )
    room_price_chart = mo.ui.altair_chart(
        alt.Chart(room_prices)
        .mark_rect()
        .encode(
            x=alt.X("room_type:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("city:N", title=None),
            color=alt.Color(
                "median_price:Q", title="Median realSum (USD)", scale=alt.Scale(scheme="blues")
            ),
            tooltip=[
                "city:N",
                "room_type:N",
                "rows:Q",
                alt.Tooltip("median_price:Q", format=",.2f"),
            ],
        )
        .properties(
            width="container",
            height=max(90, price_data["city"].nunique() * 32),
            title="Median price by city and room type",
        ),
        chart_selection="point",
        legend_selection=False,
    )
    save_presentation_chart(room_price_chart, "01_exploration/room_price_chart")
    mo.vstack(
        [
            room_price_chart,
            mo.md(
                "Hover for median prices and sample sizes. Missing combinations are left blank. City differences can also reflect differences in accommodation mix."
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Explore price and location

    Drag a rectangle over points to inspect the corresponding source rows below.
    Use the room-type legend to filter the plot; double-click to clear selections.
    This view shows associations, which may differ across cities and accommodation types.
    """)
    return


@app.cell
def _(alt, mo, np, price_data, save_presentation_chart):
    _eligible = price_data.loc[np.isfinite(price_data["dist"]) & price_data["dist"].ge(0)]
    scatter_data = _eligible.sample(n=min(5000, len(_eligible)), random_state=42).reset_index(
        names="source_row"
    )
    price_location_chart = mo.ui.altair_chart(
        alt.Chart(scatter_data)
        .mark_point(filled=True, opacity=0.45, size=35)
        .encode(
            x=alt.X("dist:Q", title="Distance to city centre (km)"),
            y=alt.Y("realSum:Q", scale=alt.Scale(type="log"), title="realSum (USD, log scale)"),
            color=alt.Color("room_type:N", title="Room type"),
            tooltip=[
                "source_row:Q",
                "city:N",
                "room_type:N",
                alt.Tooltip("realSum:Q", format=",.2f"),
                alt.Tooltip("dist:Q", format=".2f"),
                "bedrooms:Q",
                "person_capacity:Q",
            ],
        )
        .properties(width="container", height=350, title="Price versus distance to city centre"),
        chart_selection="interval",
        legend_selection=True,
    )
    save_presentation_chart(price_location_chart, "01_exploration/price_location_chart")
    mo.vstack(
        [
            price_location_chart,
            mo.md(
                f"Showing {len(scatter_data):,} of {len(_eligible):,} rows with valid price and non-negative, finite distance. The scatterplot uses a reproducible sample capped at 5,000 rows; distribution summaries above use all valid prices."
            ),
        ]
    )
    return (price_location_chart,)


@app.cell
def _(mo, price_location_chart):
    mo.ui.table(
        price_location_chart.value, pagination=True, label="Rows selected in the scatterplot"
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Investigation notes

    - Confirm observation grain, collection date, price duration and currency conversion.
    - Confirm the meanings of `weekday`, `biz` and `multi` before using them in recommendations.
    - Inspect duplicate rows, extreme prices and room-type indicator consistency before cleaning.
    - Record every exclusion and compare results before and after it.
    """)
    return


if __name__ == "__main__":
    app.run()
