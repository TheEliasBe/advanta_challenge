// Build the interviewer deck (approach, project setup, methods) from slide_data.json.
//   uv run python deck/export_slide_data.py && node deck/build_approach_deck.js
const fs = require("fs");
const path = require("path");
const { HEX, MUTED, W, M, CW, BODY_TOP, pct, sgn, chartBase, createDeck } = require("./common.js");

const ROOT = path.resolve(__dirname, "..");
const DATA = JSON.parse(
  fs.readFileSync(path.join(ROOT, "outputs/tables/deck/slide_data.json"), "utf8"),
);
const OUT = path.join(ROOT, "outputs/slides/approach_and_methods.pptx");

const { pres, C, content, numberBadge, card, write } = createDeck({
  title: "Approach and methods behind the European listing analysis",
  footer: "ADV  ·  European listing analytics  ·  Approach and methods",
});

const A = DATA.approach;
const corr = DATA.correlations;
const wk = DATA.weekend;
const n = (v) => v.toLocaleString("en-US");
const testScores = Object.fromEntries(DATA.model.test_scores.map((s) => [s.model, s]));
const MONO = "Courier New";

function textBlock(slide, runs, opts) {
  slide.addText(runs, { margin: 0, valign: "top", isTextBox: true, fontSize: 14, color: C.text1, ...opts });
}

function arrow(slide, x, y, color = C.accent2) {
  slide.addShape(pres.shapes.RIGHT_ARROW, { x, y, w: 0.2, h: 0.3, fill: { color }, line: { color }, objectName: "arrow" });
}

// ---------- 1 · title ----------
pres.addSection({ title: "Approach" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Approach" });
s.addText("How the analysis was built", { placeholder: "title" });
s.addText("Approach, project setup, key libraries and methods behind the client results", { placeholder: "subtitle" });
s.addText("ADV  ·  Interview appendix  ·  November 2026", { placeholder: "meta" });
s.addNotes("Companion to the client deck. This one explains how the work was done and why the analysis changed direction once.");

// ---------- 2 · process ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
content(s, "Six steps from the raw file to a client recommendation, with one change of direction", "Notebook numbers refer to the marimo notebooks in the repository.");
const steps = [
  ["Data audit", "Notebook 01", "Schema, coverage, price distributions"],
  ["Correlations", "Notebook 02", "Within-city vs. pooled, overlap checks"],
  ["Price model", "Notebook 03", "Grouped split, four candidate models"],
  ["Stress test", "Notebook 03", "Price-gap idea rejected"],
  ["Weekend lever", "Notebook 04", "Pairs, premiums, revenue sizing"],
  ["Client deck", "make deck", "Numbers flow from code to slides"],
];
const sw = (CW - 5 * 0.25) / 6;
steps.forEach(([head, where, body], i) => {
  const x = M + i * (sw + 0.25);
  const hot = i === 3;
  card(s, x, BODY_TOP + 0.05, sw, 2.3, hot ? C.accent1 : C.background2, `step-${i}`);
  numberBadge(s, i + 1, x + 0.2, BODY_TOP + 0.25, 0.45, hot ? C.text2 : C.accent1);
  textBlock(s, [
    { text: head, options: { bold: true, fontSize: 14, color: hot ? C.background1 : C.text2, breakLine: true } },
    { text: where, options: { fontSize: 12, color: hot ? C.background1 : MUTED, breakLine: true, paraSpaceAfter: 6 } },
    { text: body, options: { fontSize: 13, color: hot ? C.background1 : C.text1 } },
  ], { x: x + 0.2, y: BODY_TOP + 0.85, w: sw - 0.4, h: 1.4 });
});
s.addText("Principles applied throughout", { x: M, y: 4.25, w: 6, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
const principles = [
  ["Keep the data as supplied", "No rows trimmed or silently dropped; every exclusion is counted and shown."],
  ["Flag assumptions, don't guess", "Unclear fields (weekday flag, price basis, biz, multi) are listed as client questions."],
  ["One source for every number", "Slides read a JSON file written by code, so the deck cannot drift from the analysis."],
];
const prw = (CW - 2 * 0.3) / 3;
principles.forEach(([head, body], i) => {
  const x = M + i * (prw + 0.3);
  card(s, x, 4.75, prw, 1.6, C.background2, `principle-${i}`);
  textBlock(s, [
    { text: head, options: { bold: true, color: C.text2, breakLine: true } },
    { text: body },
  ], { x: x + 0.2, y: 4.9, w: prw - 0.4, h: 1.35 });
});
s.addNotes("Step 4 is the important one for the interview: the first pricing idea looked impressive but did not hold up, and the weekend lever came out of that check.");

// ---------- 3 · project setup ----------
pres.addSection({ title: "Setup" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Setup" });
content(s, "A reproducible Python project: locked environment, notebooks as code, outputs regenerated", "Raw data and all generated outputs are excluded from Git; every output can be rebuilt from the supplied files.");
card(s, M, BODY_TOP + 0.05, 5.6, 4.75, C.text2, "tree-card");
const tree = [
  ["data/raw/", "supplied CSV, catalogue"],
  ["notebooks/01–04", "marimo notebooks"],
  ["src/airbnb_analytics/", "shared code"],
  ["  data.py", "loading, profiling"],
  ["  modelling.py", "splits, models"],
  ["  weekend.py", "pairing, sizing"],
  ["  charts.py", "chart exports"],
  ["deck/", "deck builders"],
  ["outputs/", "tables, charts, model"],
  ["pyproject.toml", "dependencies"],
  ["uv.lock", "locked versions"],
  ["Makefile", "check, export, deck"],
];
textBlock(s, tree.map(([k, v], i) => ({ text: `${k.padEnd(23, " ")}${v}`, options: { breakLine: i < tree.length - 1 } })), { x: M + 0.3, y: BODY_TOP + 0.3, w: 5.0, h: 4.3, fontFace: MONO, fontSize: 11.5, color: C.background1, paraSpaceAfter: 4 });
const flow = [
  ["Supplied data", "data/raw (unchanged)"],
  ["Notebooks 01–04", "interactive analysis, controls for every assumption"],
  ["Outputs", "CSV tables, PNG/SVG charts, saved model + metadata"],
  ["slide_data.json", "every number the slides show"],
  ["Two PowerPoint decks", "native, editable charts"],
];
flow.forEach(([head, body], i) => {
  const y = BODY_TOP + 0.05 + i * 0.97;
  card(s, 6.6, y, W - M - 6.6, 0.72, i === flow.length - 1 ? C.accent1 : C.background2, `flow-${i}`);
  const last = i === flow.length - 1;
  textBlock(s, [
    { text: `${head}  `, options: { bold: true, color: last ? C.background1 : C.text2 } },
    { text: body, options: { color: last ? C.background1 : C.text1 } },
  ], { x: 6.85, y: y + 0.08, w: W - M - 7.1, h: 0.56, valign: "middle" });
  if (i < flow.length - 1) {
    s.addShape(pres.shapes.DOWN_ARROW, { x: 9.3, y: y + 0.75, w: 0.3, h: 0.2, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: `flow-arrow-${i}` });
  }
});
s.addNotes("make check runs ruff and marimo's notebook checks; make export runs all four notebooks; make deck rebuilds the slide data and both decks. Pre-commit hooks run ruff before every commit.");

// ---------- 4 · libraries ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Setup" });
content(s, "Key libraries: standard, well-supported tools chosen for reproducibility and clear charts", "Python 3.12. Versions are pinned in uv.lock; the deck builder's Node dependencies are pinned in deck/package.json.");
const libs = [
  ["uv", "Environment and lockfile", "One command (uv sync) recreates the exact environment."],
  ["marimo", "Reactive notebooks", "Stored as plain .py files; sliders and dropdowns for every scenario input."],
  ["pandas · NumPy", "Data handling", "Loading, profiling, weekday/weekend pairing, revenue sizing."],
  ["scikit-learn", "Modelling", "Pipelines, grouped splits, gradient boosting, ridge, permutation importance."],
  ["Altair · vl-convert", "Charts", "Interactive notebook charts, exported as 3600 × 2025 PNG and SVG."],
  ["matplotlib · seaborn", "Reference matrix", "Full correlation matrix exported at 300 dpi."],
  ["joblib", "Model persistence", "Saved model plus a metadata card with metrics and input hash."],
  ["Ruff · pre-commit", "Code quality", "Linting and formatting on every commit."],
  ["pptxgenjs (Node.js)", "Slides", "Both decks built from code with native, editable charts."],
];
const lw = (CW - 2 * 0.25) / 3;
const lh = 1.5;
libs.forEach(([name, role, body], i) => {
  const x = M + (i % 3) * (lw + 0.25);
  const y = BODY_TOP + 0.05 + Math.floor(i / 3) * (lh + 0.15);
  card(s, x, y, lw, lh, C.background2, `lib-${i}`);
  textBlock(s, [
    { text: name, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
    { text: role, options: { bold: true, fontSize: 12, color: C.accent5, breakLine: true, paraSpaceAfter: 4 } },
    { text: body, options: { fontSize: 13 } },
  ], { x: x + 0.2, y: y + 0.15, w: lw - 0.4, h: lh - 0.25 });
});
s.addNotes("Nothing exotic: the point was a setup any colleague could clone and rerun. marimo was chosen over Jupyter because notebooks stay diffable Python files and cells rerun when their inputs change.");

// ---------- 5 · data handling ----------
pres.addSection({ title: "Methods" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methods" });
content(s, "Data handling: keep every row, exclude nothing silently, write down open questions", "Source: supplied listing dataset and data catalogue.");
const audit = [
  [n(DATA.overview.observations), "rows"],
  [String(A.columns), "columns"],
  [String(DATA.overview.missing_values), "missing values"],
  [String(A.duplicate_rows), "duplicate rows"],
];
audit.forEach(([big, small], i) => {
  const y = BODY_TOP + 0.05 + i * 1.2;
  s.addText(big, { x: M, y, w: 2.6, h: 0.7, fontSize: 36, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  s.addText(small, { x: M, y: y + 0.68, w: 2.6, h: 0.35, fontSize: 14, color: C.text1, margin: 0, isTextBox: true });
});
card(s, 3.5, BODY_TOP + 0.05, 4.5, 4.75, C.background2, "decisions-card");
textBlock(s, [
  { text: "Decisions", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: `Prices kept untrimmed: the 99th percentile is $${n(A.p99_price)}, the maximum $${n(A.max_price)}. Charts use log scales; correlations use ranks.`, options: { bullet: true, breakLine: true } },
  { text: "Normalised attraction and restaurant indices only; their raw versions duplicate them.", options: { bullet: true, breakLine: true } },
  { text: "Room type used instead of its two indicator columns.", options: { bullet: true, breakLine: true } },
  { text: "City + coordinates as a listing proxy, because there is no listing ID.", options: { bullet: true } },
], { x: 3.75, y: BODY_TOP + 0.3, w: 4.0, h: 4.3, paraSpaceAfter: 8 });
card(s, 8.3, BODY_TOP + 0.05, W - M - 8.3, 4.75, C.text2, "questions-card");
textBlock(s, [
  { text: "Questions for the client", options: { bold: true, fontSize: 16, color: C.background1, breakLine: true } },
  { text: "Is realSum a nightly or per-stay price, and does it include fees?", options: { bullet: true, breakLine: true } },
  { text: "Which weekday flag value is the weekend?", options: { bullet: true, breakLine: true } },
  { text: "What do biz and multi mean? (excluded until confirmed)", options: { bullet: true, breakLine: true } },
  { text: "When and how was the snapshot collected?", options: { bullet: true } },
], { x: 8.55, y: BODY_TOP + 0.3, w: W - M - 8.8, h: 4.3, color: C.background1, paraSpaceAfter: 8 });
s.addNotes("The open questions double as the first agenda item of a follow-on project.");

// ---------- 6 · correlation method ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methods" });
content(s, "Correlations: rank-based, measured within each city, and checked for overlapping attributes", "Results are on client slides 5–7. Correlations describe associations, not causal effects.");
const corrMethods = [
  ["Spearman, not only Pearson", "Prices are heavily right-skewed. Rank correlation is robust to the long tail; large Pearson/Spearman differences flagged pairs for a closer look."],
  ["Within each city, not only pooled", `City price levels differ 3.6×, which masks relationships. Distance to the centre: ${sgn(corr.pooled.dist)} pooled, ${sgn(corr.within_median.dist)} within cities.`],
  ["Overlap between attributes", `${Object.entries(corr.redundant_pairs).map(([k, v]) => `${k} ${sgn(v)}`).join("; ")}. Overlapping attributes are not read as independent drivers.`],
];
const cmw = (CW - 2 * 0.3) / 3;
corrMethods.forEach(([head, body], i) => {
  const x = M + i * (cmw + 0.3);
  card(s, x, BODY_TOP + 0.05, cmw, 3.0, C.background2, `corr-method-${i}`);
  numberBadge(s, i + 1, x + 0.25, BODY_TOP + 0.3, 0.45);
  textBlock(s, [
    { text: head, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true, paraSpaceAfter: 6 } },
    { text: body },
  ], { x: x + 0.25, y: BODY_TOP + 0.95, w: cmw - 0.5, h: 2.0 });
});
card(s, M, 4.85, CW, 1.5, C.text2, "corr-exclusions");
textBlock(s, [
  { text: "Excluded on purpose:  ", options: { bold: true, color: C.background1 } },
  { text: "latitude and longitude, the raw attraction and restaurant indices, and the room-type indicator columns. The interactive notebook keeps the full matrix for reference.", options: { color: C.accent6 } },
], { x: M + 0.3, y: 5.0, w: CW - 0.6, h: 1.2, valign: "middle" });
s.addNotes("The pooled-versus-within-city comparison is the strongest methodological point: aggregated correlations would have told the client that distance does not matter.");

// ---------- 7 · model method ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methods" });
content(s, "Price model: four candidates, a grouped 60/20/20 split, and one look at the test set", "Error = mean absolute error in source price units. Models predict log(1 + price); errors are measured after transforming back.");
const split = A.split_summary;
s.addChart(pres.charts.BAR, split.map((p) => ({ name: p.split[0].toUpperCase() + p.split.slice(1), labels: ["Rows"], values: [p.rows] })), chartBase({
  x: M, y: BODY_TOP, w: 5.6, h: 1.6, barDir: "bar", barGrouping: "percentStacked", chartColors: [HEX.dk2, HEX.accent2, HEX.accent1],
  showValue: true, dataLabelPosition: "ctr", dataLabelColor: "FFFFFF", dataLabelFormatCode: "#,##0", valAxisHidden: true, catAxisHidden: true, valGridLine: { style: "none" },
  showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: MUTED,
}));
textBlock(s, [
  { text: "Why grouped: ", options: { bold: true, color: C.text2 } },
  { text: "most listings appear twice (weekday and weekend). Keeping each city + coordinate group in one split stops the model from seeing a listing's twin in training. The code raises an error if a group crosses splits.", options: {} },
], { x: M, y: 3.35, w: 5.6, h: 1.5 });
textBlock(s, [
  { text: "Then: ", options: { bold: true, color: C.text2 } },
  { text: "select on validation error, refit the winner on train + validation, score once on test. Permutation importance on validation data explains what the model relies on.", options: {} },
], { x: M, y: 4.95, w: 5.6, h: 1.4 });
const vs = A.validation_scores;
const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.dk2, fill: { color: HEX.lt2 }, align: "center", valign: "middle" } });
const modelRows = [[hdr("Model"), hdr("Validation error"), hdr("Test error"), hdr("Test median % error")]];
vs.forEach((v) => {
  const t = testScores[v.model];
  const win = v.model.startsWith("Gradient");
  const cell = (text, align = "center") => ({ text, options: { align, valign: "middle", bold: win, color: win ? "FFFFFF" : HEX.dk1, fill: { color: win ? HEX.accent1 : "FFFFFF" } } });
  modelRows.push([
    cell(v.model, "left"),
    cell(`$${v.MAE.toFixed(1)}`),
    cell(t ? `$${t.MAE.toFixed(1)}` : "not refitted"),
    cell(t ? `±${t.median_APE_pct.toFixed(0)}%` : "–"),
  ]);
});
s.addTable(modelRows, { x: 6.6, y: BODY_TOP + 0.1, w: W - M - 6.6, colW: [2.35, 1.35, 1.2, 1.233], rowH: 0.55, fontSize: 13, fontFace: "Arial", border: { type: "solid", pt: 0.75, color: "D3D8DE" } });
textBlock(s, [
  { text: "Only the selected model and the two simple baselines are refitted and tested, so the test set is used once for the decision that matters.", options: { color: MUTED } },
], { x: 6.6, y: 4.6, w: W - M - 6.6, h: 1.0, fontSize: 13 });
s.addNotes("Gradient boosting won on validation and held up on test. Location and size carry most of the signal; ratings add almost nothing, which matches the correlation results.");

// ---------- 8 · stress test ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methods" });
content(s, "Stress test: the first pricing idea did not hold up, so the approach changed", "Neighbour-price and rating-band checks were run as quick exploratory scripts with the same grouped cross-fitting; they are not part of the notebooks.");
const stages = [
  ["First idea", C.background2, [
    [`+${A.first_idea.uplift_pct.toFixed(1)}%`, "uplift if every listing priced below its model prediction moved up to it"],
    [`${pct(A.first_idea.candidates / A.first_idea.observations)}`, `of listings flagged as underpriced (${n(A.first_idea.candidates)} of ${n(A.first_idea.observations)})`],
  ]],
  ["Why it failed", C.background2, [
    ["Noise", "With ±18% typical error, about half of listings sit below any benchmark by chance."],
    ["Bias", `Mean error is negative in all ${A.cities_with_negative_bias} cities: the log model predicts closer to the median than the mean.`],
    ["Checks", "A neighbour-price feature left error unchanged ($70.9 → $70.9); price gaps were the same (+2–3.5%) across rating bands."],
  ]],
  ["What replaced it", C.text2, [
    ["Observed behaviour", "Most listings appear on both day types, so their own weekday and weekend prices can be compared directly."],
    [pct(wk.share_same_price), "of paired hosts charge the same on both: a lever that needs no model."],
  ]],
];
const stw = (CW - 2 * 0.45) / 3;
stages.forEach(([head, fill, items], i) => {
  const x = M + i * (stw + 0.45);
  const dark = fill === C.text2;
  card(s, x, BODY_TOP + 0.05, stw, 4.75, fill, `stage-${i}`);
  const runs = [{ text: head, options: { bold: true, fontSize: 18, color: dark ? C.background1 : C.text2, breakLine: true, paraSpaceAfter: 10 } }];
  items.forEach(([k, v], j) => {
    runs.push({ text: k, options: { bold: true, fontSize: k.length < 8 ? 24 : 15, color: dark ? C.accent4 : C.accent5, breakLine: true } });
    runs.push({ text: v, options: { color: dark ? C.background1 : C.text1, breakLine: j < items.length - 1, paraSpaceAfter: 12 } });
  });
  textBlock(s, runs, { x: x + 0.25, y: BODY_TOP + 0.3, w: stw - 0.5, h: 4.3 });
  if (i < 2) arrow(s, x + stw + 0.14, BODY_TOP + 2.25);
});
s.addNotes("This is the judgement call in the project. Summing positive gaps from a noisy model produces a large, attractive number that is mostly noise. The client deck therefore uses the model for guidance only, and sizes the revenue lever from observed host behaviour.");

// ---------- 9 · weekend method ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methods" });
content(s, "Weekend lever: pair listings, compare their own prices, then size with explicit assumptions", "Pairing and premiums: src/airbnb_analytics/weekend.py. Sizing inputs are editable in notebook 04; financial sources are on client slide 11.");
const funnel = A.pairing_steps;
s.addText("From locations to clean pairs", { x: M, y: BODY_TOP, w: 5.6, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
funnel.forEach((f, i) => {
  const y = BODY_TOP + 0.5 + i * 0.82;
  const first = i === 0;
  const last = i === funnel.length - 1;
  const fill = last ? C.accent1 : first ? C.text2 : C.background2;
  card(s, M, y, 5.6, 0.66, fill, `funnel-${i}`);
  const light = first || last;
  textBlock(s, [
    { text: `${first || last ? "" : "− "}${n(f.locations)}`, options: { bold: true, color: light ? C.background1 : C.text2 } },
    { text: `   ${f.step}`, options: { color: light ? C.background1 : C.text1 } },
  ], { x: M + 0.25, y: y + 0.05, w: 5.1, h: 0.56, valign: "middle" });
});
card(s, 6.6, BODY_TOP + 0.05, W - M - 6.6, 4.75, C.background2, "sizing-card");
textBlock(s, [
  { text: "Premium", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: "For each same-price host: the 25th percentile (conservative) or median (typical) premium of differentiating hosts in the same city and room type; city-wide when fewer than 20 references.", options: { breakLine: true, paraSpaceAfter: 12 } },
  { text: "Sizing", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: "Extra revenue = EMEA booking value × weekend share × same-price hosts' share × adoption × premium × take rate.", options: { fontFace: MONO, fontSize: 13, breakLine: true, paraSpaceAfter: 12 } },
  { text: "Assumptions shown on the slide", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: "Weekend = flag 0 (inferred from prices), coordinates = listing, bookings unchanged unless stated, EMEA booking value derived from reported revenue.", options: {} },
], { x: 6.85, y: BODY_TOP + 0.3, w: W - M - 7.1, h: 4.3 });
s.addNotes("Pairs require matching room type and capacity on both days, and locations with several rows per day type are dropped as likely multi-unit addresses.");

// ---------- 10 · quality ----------
pres.addSection({ title: "Wrap-up" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Wrap-up" });
content(s, "Quality checks from code style to slide numbers", "Generative AI (Claude Code) was used as a coding and review assistant, as the challenge allows; all results come from the code in the repository.");
const checks = [
  ["Code style", "Ruff lint and format, enforced by a pre-commit hook; marimo checks notebook structure."],
  ["Leakage guard", "The split function raises an error if a location group appears in more than one split."],
  ["Honest evaluation", "Model chosen on validation data; the test set is scored once, after the choice."],
  ["Traceable numbers", "Slides read slide_data.json, written from the notebook outputs by one script."],
  ["Saved model", "Model file plus a metadata card: features, test metrics, input-file hash, library version."],
  ["Deck checks", "Both decks are validated as files and rendered in PowerPoint to check layout."],
];
const qw = (CW - 2 * 0.3) / 3;
checks.forEach(([head, body], i) => {
  const x = M + (i % 3) * (qw + 0.3);
  const y = BODY_TOP + 0.05 + Math.floor(i / 3) * 2.45;
  card(s, x, y, qw, 2.2, C.background2, `check-${i}`);
  numberBadge(s, i + 1, x + 0.25, y + 0.25, 0.45);
  textBlock(s, [
    { text: head, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true, paraSpaceAfter: 6 } },
    { text: body },
  ], { x: x + 0.25, y: y + 0.85, w: qw - 0.5, h: 1.25 });
});
s.addNotes("Be ready to say how AI assistance was used: drafting code and slides, reviewing for errors, with every figure recomputed from the repository code.");

// ---------- 11 · limitations ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Wrap-up" });
content(s, "Limitations today, and what I would build next", "");
const cols = [
  ["Limitations", C.background2, [
    "No booking, demand or occupancy data: revenue figures are what-if calculations",
    "Weekend flag and price basis unconfirmed",
    "Coordinates stand in for listing IDs",
    "One snapshot: no seasonality or dates",
    "EMEA sizing extrapolates from 10 European cities",
    "No unit tests yet; correctness checked through the notebooks",
  ]],
  ["Next steps", C.text2, [
    "Confirm data definitions with the client",
    "Unit tests and CI for the shared package",
    "Prediction intervals (quantile models) and bias correction for the price model",
    "Price elasticity and utilization once booking data is available",
    "Turn the weekend pilot into a measured experiment",
  ]],
];
const colW = (CW - 0.4) / 2;
cols.forEach(([head, fill, items], i) => {
  const x = M + i * (colW + 0.4);
  const dark = fill === C.text2;
  card(s, x, BODY_TOP + 0.05, colW, 4.75, fill, `wrap-${i}`);
  textBlock(s, [
    { text: head, options: { bold: true, fontSize: 18, color: dark ? C.background1 : C.text2, breakLine: true, paraSpaceAfter: 10 } },
    ...items.map((t, j) => ({ text: t, options: { bullet: true, color: dark ? C.background1 : C.text1, breakLine: j < items.length - 1 } })),
  ], { x: x + 0.3, y: BODY_TOP + 0.3, w: colW - 0.6, h: 4.3, paraSpaceAfter: 8 });
});
s.addNotes("Close by linking the next steps to the client roadmap: the same booking data that removes the main limitation is what phase 2 of the engagement asks for.");

(async () => {
  await write(OUT);
  console.log(`Wrote ${path.relative(ROOT, OUT)}`);
})();
