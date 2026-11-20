# Airbnb analytics working plan

## Scope

The project covers the challenge's exploration, correlation and predictive modelling work.
Notebook 03 has two prototypes: a model of the observed accommodation price and a search for
similar accommodations. Notebook 04 sizes a weekend-pricing lever from listings observed on
both day types. The supplied data has no demand, booking, occupancy or revenue outcomes, so
the price model learns observed prices and cannot identify a revenue-maximizing price. The
client deck is built from these results with `make deck`.

## Source questions

- Confirm what one row represents and whether accommodations repeat across `weekday` values.
- Confirm the collection period, sampling design, price duration, fees and currency conversion.
- The catalogue labels `realSum` as USD but does not define a nightly or stay basis.
- Confirm `weekday` (catalogue: weekday availability), `biz` (catalogue: business facilities)
  and `multi` (catalogue: multiple listings). Do not infer different meanings from their names.
- Catalogue spellings differ from CSV names for four fields. `load_dictionary()` adds an
  explicit mapping and preserves the original descriptions.
- There is no explicit listing ID, host ID, booking outcome or collection timestamp in the CSV header.

## Analysis sequence

1. Audit schema, completeness, duplicates, validity ranges and sample coverage.
2. Compare Pearson and Spearman relationships across all rows and within cities.
3. Investigate strong correlations, redundant encodings and outlier sensitivity.
4. Predict `realSum` for existing listings with known accommodation attributes and ratings.
5. Compare baselines, ridge regression and gradient boosting using grouped validation.
6. Inspect held-out errors and compare selected listings with attribute-based neighbours.

## Price experiment

- Retain all positive finite target rows; do not trim expensive accommodations.
- Group observations by city and exact longitude/latitude. This conservative location
  proxy reduces repeated-property leakage but can combine different accommodations and
  cannot identify repeats whose coordinates change. No explicit listing ID is supplied.
- Use approximately 60/20/20 train/validation/test groups, with seeds 42 and 43.
  The initial split is not a temporal forecast or an unseen-city evaluation.
- Fit imputers, numerical scaling and categorical encoding inside training pipelines.
- Compare global median, city/room median, log-price ridge regression and log-price
  histogram gradient boosting. Use validation MAE for selection, then refit the winner
  on train + validation and evaluate it and refitted baselines on the reserved test set.
- Report MAE, RMSE, R-squared and median absolute percentage error in original price
  units. Show errors by city and room type and inspect extreme misses.
- Calculate permutation importance on a fixed validation sample before refitting;
  importance is predictive and does not establish a causal price effect.
- Use room type instead of its duplicate indicator columns and normalized indices instead
  of both index versions. Exclude `biz` and `multi` until their definitions are confirmed.
  Treat `weekday` as a raw category, without interpreting it as demand or occupancy.
- Features include current ratings, so this version benchmarks existing listings.
  A new-listing model would require a separate experiment without unavailable ratings.

## Similar accommodations

- Use train + validation rows as the reference catalogue and choose queries from the test set.
- Require the same city, room type and weekday flag; exclude the query's location group.
- Rank by root-mean-square differences in reference-standardized accommodation, location
  and rating attributes. Equal standardized feature weights are a prototype choice.
- Exclude price from matching and retain at most one result per reference location group.
  Coordinates and source-row numbers are proxies, not confirmed listing identifiers.
- Show observed comparable prices and their interquartile range as descriptive context.
  These are not prediction intervals or estimates of an optimal price.
- Similarity has structural checks but no booking/preference labels for relevance evaluation.

## Price-gap scenarios

- Obtain predictions for every retained observation through five-fold grouped cross-fitting.
  Each location group is absent from that fold's model fit. The specification was selected
  earlier, so this is exploratory full-snapshot scoring, not a nested accuracy evaluation.
  Preserve the original reserved test metrics as the model-performance estimate.
- Select positive benchmark gaps, optionally above a user-defined percentage threshold.
  Apply all or part of the gap; keep non-candidate prices and volume unchanged.
- Assume one equal-size, like-for-like sale per snapshot observation at baseline and a
  uniform proportional change in candidate sales volume. Actual booking counts are absent.
- Scenario change = volume retained × (candidate baseline + applied price gap) − candidate baseline.
  Divide by the full-snapshot baseline price sum for the overall percentage change.
- Break-even candidate volume retention = candidate baseline / candidate adjusted price sum.
- Report changes by city and stress-test booking-volume declines. A threshold is a review
  rule, not a confidence interval. Positive residuals exist even for an unbiased noisy model;
  their sum does not establish underpricing or realizable revenue.
- Counts are observations, not confirmed distinct properties. Do not annualize the scenario,
  extrapolate it to all Airbnb inventory, or label it host earnings or platform revenue.
- For above-benchmark observations, inspect utilization before testing reductions. For
  below-benchmark observations, high utilization could justify a controlled increase test;
  weak utilization may signal other issues. This dataset cannot assign those utilization labels.

## Evidence to retain

Record input hashes, row exclusions, split definitions, feature sets, random seeds,
metrics, segment errors and figure generation code with each final experiment.
Store tables, figures and reports in the corresponding `outputs/` directories.
Only turn a hypothesis into a slide headline after checking the evidence and limitations.
