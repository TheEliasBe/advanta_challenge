# ADV Airbnb analytics

Analysis of the European Airbnb dataset for the ADV challenge: data exploration, correlations,
price modelling, weekend-pricing sizing and the client deck. The project uses uv for the Python
environment and marimo for notebooks. Marimo notebooks are plain `.py` files, so Git tracks the
code without Jupyter output metadata, and editing a cell reruns the cells that depend on it.

## Start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12 (uv can
install Python for you). From the project directory:

```bash
uv sync
uv run marimo edit notebooks/
```

Start with `01_data_exploration.py`. To open it directly:

```bash
uv run marimo edit notebooks/01_data_exploration.py
```

The project package installs in editable mode, so notebooks import the shared code without
`sys.path` changes. Launch marimo with `uv run` so it uses the project environment. To reproduce
the exact environment from the lockfile, run `uv sync --locked`.

After changing dependencies, run `uv sync` (it needs network access) to update the environment
and lockfile, then `make check` and `make export` to confirm the notebooks still run.

The [marimo extension for VS Code](https://marketplace.visualstudio.com/items?itemName=marimo-team.vscode-marimo)
makes the notebooks easier to read and run inside the editor.

## Structure

```text
data/
  raw/                    Original CSV and Excel catalogue, kept unchanged
  processed/              Derived datasets
notebooks/
  01_data_exploration.py   Data quality and interactive Altair price exploration
  02_correlations.py       Price relationships, city comparisons and pair diagnostics
  03_predictive_modelling.py  Price prediction and similar-listing explorer
  04_weekend_pricing.py    Weekend/weekday price pairs and revenue sizing of a weekend premium
src/airbnb_analytics/      Reusable loaders, profiling, modelling and weekend-pricing code
deck/                      Scripts that build the client PowerPoint deck
docs/analysis_plan.md      Scope, source questions and analytical workflow
outputs/
  figures/                Slide-ready charts
  tables/                 Exported analysis tables
  models/                 Trained price model and its metadata
  reports/                Notebook HTML exports
  slides/                 Client PowerPoint deck
pyproject.toml            Dependencies and tooling
uv.lock                   Locked dependency versions
```

Git ignores the raw data and the generated charts, tables and reports; the two decks and the
saved model are committed. Keep the supplied files in `data/raw/`.
The loader resolves paths relative to the project, so the current directory doesn't matter.
It keeps source rows, duplicates, column names and outliers as supplied. The catalogue is read
with an extra mapping from catalogue field names to CSV column names, and its descriptions are
kept as written.

## Workflow

1. Review data definitions and quality in notebook 01.
2. Explore correlations in notebook 02 and record interpretations in `docs/analysis_plan.md`.
3. Run the price experiment and similar-listing explorer in notebook 03, then save its results.
4. Size the weekend-pricing lever in notebook 04.
5. Build the client deck with `make deck`.

Notebook 01 uses `mo.ui.altair_chart` for city price histograms, city percentile ranges, a
median-price heatmap by room type, and a price-versus-distance scatterplot linked to a selection
table. All views follow the city filter. Distribution summaries use all valid prices. Only the
scatterplot is sampled, with a fixed seed and a cap of 5,000 rows.

Notebook 02 compares Pearson and Spearman price correlations and shows within-city results next
to the pooled ones. A faceted chart with a shared scale compares each city's three strongest
positive and negative price correlations. You can pick any pair of attributes for a scatterplot
with outlier sensitivity statistics, and city and room-type controls narrow the segment. A
feature-redundancy view lists strongly correlated attribute pairs separately from the price
relationships; the full matrix sits in a collapsed reference panel. The all-city comparison
follows the room-type and method controls but ignores the city selector. Scatterplots are
sampled; correlation statistics use all finite pairs in the segment. Latitude and longitude are
left out of every correlation view and pair selector. The attraction and restaurant indices
appear only as `attr_index_norm` and `rest_index_norm`, without their raw versions.

Notebooks 01 and 02 export their charts automatically to `outputs/figures/01_exploration/` and
`outputs/figures/02_correlations/`. Single Altair charts use a fixed 1200 × 675 canvas and are
saved with `scale_factor=3` as 3600 × 2025 PNGs and as SVGs. The exported copies have larger
labels and a white background; the charts in the notebooks keep their responsive layout.
Faceted overviews use a fixed size per panel. Notebook 02 also exports a 16:9 chart for each
city under `02_correlations/cities/`, and the full reference matrix at 300 dpi and as SVG.
Rerunning a chart cell overwrites its exports with the current filter values. All output paths
are relative to the project directory.

`save_presentation_chart` in `airbnb_analytics.charts` takes a chart and a name relative to
`outputs/figures/`:

```python
from airbnb_analytics.charts import save_presentation_chart

save_presentation_chart(city_corr_chart, "02_correlations/city_corr_chart")
```

Notebook 03 compares a global median, a city/room median, ridge regression on log price and
gradient boosting on log price. Rows are split about 60/20/20 into train, validation and test,
and all rows with the same city and coordinates stay in the same split. Validation MAE picks the
model, which is then refitted on train + validation and scored once on test. Diagnostics cover
segment errors, prediction plots and permutation importance on validation data. The
similar-listing explorer compares a held-out row with reference accommodations of the same city,
room type and weekday flag; price plays no part in the ranking. The save button writes scores,
test predictions, split assignments and input/version metadata to `outputs/tables/03_modelling/`,
and the trained model with a JSON metadata file to `outputs/models/`.

Notebook 03 also cross-fits the selected model over five location-group folds to flag listings
for price review across the whole snapshot. Its scenario controls set the minimum gap to the
benchmark, the share of the gap applied to the price, and the assumed booking volume retained.
The baseline counts one equal-size sale per observation and keeps all other prices and volumes
fixed. The resulting price sums are hypothetical gross values, not earnings or annual revenue,
and repeated observations aren't treated as confirmed unique listings. The save button also
writes the scenario tables and the review queue. A 16:9 sensitivity chart is saved as PNG and
SVG to `outputs/figures/03_modelling/price_gap_volume_sensitivity`.

Notebook 04 pairs the weekday and weekend observations at the same coordinates, measures how many
hosts charge the same price on both, and sizes the revenue from those hosts adopting the weekend
premium their neighbours charge. It reads `weekday == 0` as the weekend, which the catalogue
doesn't confirm. The Airbnb financials it uses are editable inputs. Tables go to
`outputs/tables/04_weekend_pricing/` and charts to `outputs/figures/04_weekend_pricing/`.

The source catalogue doesn't say whether `realSum` is a nightly or per-stay price, so the
notebooks keep the original field name. The data has no demand, booking or occupancy outcomes,
so the models evaluate price prediction and attribute similarity, and revenue figures are
static what-if calculations.

## Decks

`make deck` writes two presentations to `outputs/slides/`:

- `airbnb_initial_insights.pptx`, the client deck with the results and recommendations.
- `approach_and_methods.pptx`, the interviewer deck on approach, project setup, libraries and methods.

It first runs `deck/export_slide_data.py`, which collects every number on the slides into
`outputs/tables/deck/slide_data.json`. Then `deck/build_deck.js` and
`deck/build_approach_deck.js` build the decks with pptxgenjs; both share the theme and layouts
in `deck/common.js`. Run notebooks 03 and 04 (and save the results in 03) beforehand so the
tables exist. The build needs Node.js; install its dependencies once with
`cd deck && npm install`.

## Checks and exports

```bash
make check
make export
```

Pre-commit hooks run `ruff check --fix` and `ruff format` on staged Python files before each
commit, using the ruff version from `uv.lock`. Install them once per clone with
`uv run pre-commit install`, and run them by hand with `uv run pre-commit run --all-files`.
If a hook fixes or reformats a file, the commit stops; review the change, stage it and commit
again.

`make export` runs all four notebooks with their default controls and writes HTML reports. To
run a notebook as a script:

```bash
uv run python notebooks/01_data_exploration.py
```

The environment includes Altair, pandas, NumPy, SciPy, scikit-learn, matplotlib, seaborn,
PyArrow and openpyxl; Ruff handles linting and formatting. `uv sync --extra slides` adds
python-pptx for reading `.pptx` files from Python.

Add analysis dependencies with `uv add package-name` and development tools with
`uv add --dev package-name`. When the environment changes, commit `pyproject.toml`,
`.python-version` and `uv.lock` together. You don't need a `requirements.txt` or to activate
the environment.

References: [marimo installation](https://docs.marimo.io/getting_started/installation/),
[uv projects](https://docs.astral.sh/uv/guides/projects/).
