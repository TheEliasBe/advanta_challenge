// Build the client deck from outputs/tables/deck/slide_data.json.
//   uv run python deck/export_slide_data.py && node deck/build_deck.js
const fs = require("fs");
const path = require("path");
const { HEX, MUTED, W, M, CW, BODY_TOP, fmtUSD, pct, sgn, title, mix, chartBase, createDeck } = require("./common.js");

const ROOT = path.resolve(__dirname, "..");
const DATA = JSON.parse(
  fs.readFileSync(path.join(ROOT, "outputs/tables/deck/slide_data.json"), "utf8"),
);
const OUT = path.join(ROOT, "outputs/slides/airbnb_initial_insights.pptx");

const { pres, C, content, numberBadge, card, write } = createDeck({
  title: "Initial insights from European listing data",
  footer: "ADV  ·  European listing analytics  ·  Initial results for discussion",
});

const corr = DATA.correlations;
const wk = DATA.weekend;
const fin = DATA.financials;
const takeRate = fin.revenue_bn / fin.gbv_bn;
const emeaGbv = fin.emea_revenue_bn / takeRate;
const scen = (premium, adoption) => wk.scenarios.find((s) => s.premium.startsWith(premium) && s.adoption_pct === adoption);
const low = scen("Conservative", 50);
const high = scen("Typical", 100);
const mid = scen("Typical", 50);
const scores = Object.fromEntries(DATA.model.test_scores.map((s) => [s.model, s]));
const gbm = scores["Gradient boosting (log price)"];
const cityMedian = scores["City/room median"];

// ---------- 1 · title ----------
pres.addSection({ title: "Introduction" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
s.addText("Pricing the weekend: what European listing data tells us", { placeholder: "title" });
s.addText("Correlation analysis and predictive modelling on 51,707 price observations in 10 cities", { placeholder: "subtitle" });
s.addText("ADV  ·  Initial results for discussion  ·  November 2026", { placeholder: "meta" });
s.addNotes("Purpose: share first results from the listing dataset and agree on a pilot to validate the largest opportunity.");

// ---------- 2 · executive summary ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
content(s, "Six in ten hosts leave weekend demand unpriced, worth an estimated $19–71M a year to Airbnb in EMEA", "Revenue range: 50% adoption of a conservative premium to 100% adoption of the typical premium, weekend bookings unchanged. See slide 11 for assumptions.");
const summary = [
  ["Size, room type and location set the price", `Guest capacity (ρ ${sgn(corr.within_median.person_capacity)}) and entire homes vs. private rooms dominate within every city. Guest ratings barely relate to price (ρ ≈ ${sgn(corr.within_median.guest_satisfaction_overall)}).`],
  ["A benchmark model prices listings within ±18%", `Median error; ${pct(1 - gbm.MAE / cityMedian.MAE)} lower than city/room averages. Good enough for price guidance, too noisy to call an individual listing underpriced.`],
  ["62% of hosts price weekends like weekdays", `Their neighbours who differentiate charge a median +${pct(wk.premium_median_differentiators)} at the weekend. Closing that gap is the clearest revenue lever in the data.`],
];
summary.forEach(([head, body], i) => {
  const y = BODY_TOP + 0.1 + i * 1.6;
  numberBadge(s, i + 1, M, y);
  s.addText(head, { x: M + 0.75, y: y - 0.05, w: 6.6, h: 0.45, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addText(body, { x: M + 0.75, y: y + 0.45, w: 6.6, h: 0.9, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
});
card(s, 8.4, BODY_TOP + 0.05, W - M - 8.4, 4.75, C.text2, "headline-card");
s.addText("Estimated extra Airbnb revenue per year, EMEA", { x: 8.75, y: BODY_TOP + 0.35, w: 3.6, h: 0.6, fontSize: 14, color: C.accent6, margin: 0, isTextBox: true });
s.addText(`$${low.extra_revenue_musd}–${high.extra_revenue_musd}M`, { x: 8.75, y: BODY_TOP + 1.0, w: 3.7, h: 1.1, fontSize: 54, bold: true, color: C.background1, margin: 0, isTextBox: true });
s.addText(`from $${low.extra_gbv_musd}–${high.extra_gbv_musd}M extra gross booking value`, { x: 8.75, y: BODY_TOP + 2.1, w: 3.6, h: 0.5, fontSize: 14, color: C.accent6, margin: 0, isTextBox: true });
s.addText([
  { text: "Proposed next step", options: { bold: true, color: C.accent4, breakLine: true } },
  { text: "A two-city weekend-pricing pilot, with booking data connected to measure utilization: the first step towards a pricing engine.", options: { color: C.background1 } },
], { x: 8.75, y: BODY_TOP + 2.9, w: 3.6, h: 1.6, fontSize: 14, margin: 0, valign: "top", isTextBox: true });
s.addNotes("Lead with the opportunity; the correlation and model findings explain why we focus on weekend pricing rather than on individual 'underpriced' listings.");

// ---------- 3 · data overview ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
content(s, "The dataset covers 10 European cities whose typical price differs by a factor of 3.6", "Source: supplied listing dataset; price field realSum (USD per catalogue; stay basis unconfirmed). Median per city across all observations.");
const cityPrices = Object.entries(DATA.overview.city_median_price).sort((a, b) => a[1] - b[1]);
s.addChart(pres.charts.BAR, [{ name: "Median price", labels: cityPrices.map(([c]) => title(c)), values: cityPrices.map(([, v]) => v) }], chartBase({
  x: M, y: BODY_TOP, w: 7.4, h: 4.9, barDir: "bar", chartColors: [HEX.dk2], barGapWidthPct: 45,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$#,##0", valAxisHidden: true, valGridLine: { style: "none" },
  showTitle: true, title: "Median price per observation", titleFontSize: 14, titleColor: MUTED,
}));
const stats = [
  [DATA.overview.observations.toLocaleString("en-US"), "price observations"],
  ["2", "day types per listing (weekday flag)"],
  [String(DATA.overview.missing_values), "missing values; no duplicate rows"],
];
stats.forEach(([big, small], i) => {
  const y = BODY_TOP + 0.2 + i * 1.25;
  s.addText(big, { x: 8.6, y, w: 4.1, h: 0.7, fontSize: 36, bold: true, color: C.accent1, margin: 0, isTextBox: true });
  s.addText(small, { x: 8.6, y: y + 0.68, w: 4.1, h: 0.4, fontSize: 14, color: C.text1, margin: 0, isTextBox: true });
});
s.addText("To confirm: price basis (night vs. stay), weekday-flag meaning, collection period. No listing IDs, dates or bookings are included.", { x: 8.6, y: BODY_TOP + 3.95, w: 4.1, h: 0.95, fontSize: 12, color: MUTED, margin: 0, valign: "top", isTextBox: true });
s.addNotes("Data quality is good: complete and duplicate-free. The missing pieces are what a pricing strategy ultimately needs: bookings, dates and listing identifiers.");

// ---------- 4 · section A ----------
pres.addSection({ title: "Correlation analysis" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Correlation analysis" });
s.addText("PART A", { placeholder: "kicker" });
s.addText("What moves the price?", { placeholder: "title" });
s.addText("Rank correlations (Spearman) between listing attributes and price, measured within each city and across cities", { placeholder: "body" });

// ---------- 5 · drivers ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Correlation analysis" });
content(s, "Size, room type and location drive price; guest ratings hardly matter", "Median of the 10 within-city Spearman correlations with price. Coordinates and raw (non-normalised) indices excluded.");
const drivers = Object.entries(corr.within_median).sort((a, b) => a[1] - b[1]);
const driverColor = (v) => (Math.abs(v) < 0.2 ? HEX.accent6 : v > 0 ? HEX.accent1 : HEX.accent3);
s.addChart(pres.charts.BAR, [{ name: "Correlation with price", labels: drivers.map(([k]) => corr.labels[k]), values: drivers.map(([, v]) => v) }], chartBase({
  x: M, y: BODY_TOP, w: 7.6, h: 4.95, barDir: "bar", chartColors: drivers.map(([, v]) => driverColor(v)), barGapWidthPct: 40,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.00;−0.00;0.00",
  valAxisMinVal: -0.8, valAxisMaxVal: 0.8, valAxisMajorUnit: 0.4, valAxisLabelFormatCode: "+0.0;−0.0;0",
  catAxisLabelPos: "low",
}));
const driverMsgs = [
  [C.accent1, "Size and location add value", `Capacity (+${corr.within_median.person_capacity.toFixed(2)}), attraction index (+${corr.within_median.attr_index_norm.toFixed(2)}) and bedrooms (+${corr.within_median.bedrooms.toFixed(2)}) rise with price in every city.`],
  [C.accent3, "Private rooms sell at a discount", `The strongest single relationship (${sgn(corr.within_median.room_private)}). Distance to the centre also lowers price (${sgn(corr.within_median.dist)}).`],
  [C.accent2, "Quality is not priced in", `Satisfaction, cleanliness and superhost status stay below 0.2. Prices follow size and location, and good reviews barely move them.`],
];
driverMsgs.forEach(([color, head, body], i) => {
  const y = BODY_TOP + 0.1 + i * 1.6;
  s.addShape(pres.shapes.OVAL, { x: 8.6, y: y + 0.07, w: 0.26, h: 0.26, fill: { color }, line: { color }, objectName: `legend-dot-${i}` });
  s.addText(head, { x: 9.05, y, w: 3.65, h: 0.42, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addText(body, { x: 9.05, y: y + 0.45, w: 3.65, h: 1.05, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
});
s.addNotes("Within-city correlations are the right lens: they compare listings that compete for the same guests. Ratings having almost no price relationship is a strategic signal: reputation is not monetised.");

// ---------- 6 · pooled vs within ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Correlation analysis" });
content(s, "Distance to the centre only matters within a city; pooled data hides it", `"Within each city" = median of 10 within-city Spearman correlations. Overlapping attribute pairs: ${Object.entries(corr.redundant_pairs).map(([k, v]) => `${k} ${sgn(v)}`).join("; ")}.`);
const pooledKeys = ["dist", "metro_dist", "person_capacity", "room_private", "attr_index_norm"];
s.addChart(pres.charts.BAR, [
  { name: "All cities pooled", labels: pooledKeys.map((k) => corr.labels[k]), values: pooledKeys.map((k) => corr.pooled[k]) },
  { name: "Within each city", labels: pooledKeys.map((k) => corr.labels[k]), values: pooledKeys.map((k) => corr.within_median[k]) },
], chartBase({
  x: M, y: BODY_TOP, w: 7.6, h: 4.95, barDir: "col", barGrouping: "clustered", chartColors: [HEX.accent6, HEX.accent1], barGapWidthPct: 60,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "+0.00;−0.00;0.00",
  valAxisMinVal: -0.8, valAxisMaxVal: 0.8, valAxisMajorUnit: 0.4, valAxisLabelFormatCode: "+0.0;−0.0;0",
  showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: MUTED, catAxisLabelPos: "low",
}));
card(s, 8.6, BODY_TOP + 0.05, W - M - 8.6, 4.75, C.background2, "insight-card");
s.addText([
  { text: "Why it matters", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: `Pooled, distance looks irrelevant (${sgn(corr.pooled.dist)}). Within each city it is clearly negative (${sgn(corr.within_median.dist)}), because expensive cities (Amsterdam, Paris) have different geography from cheaper ones.`, options: { breakLine: true, paraSpaceAfter: 10 } },
  { text: "Implication", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
  { text: "Price guidance and benchmarks must compare listings within the same city and room type. A Europe-wide rule of thumb misleads hosts." },
], { x: 8.85, y: BODY_TOP + 0.3, w: W - M - 9.1, h: 4.3, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
s.addNotes("Simpson's-paradox-style effect: aggregate correlations mask the within-market relationship. Several attributes also overlap strongly with each other (see footnote), so they should not be read as independent effects.");

// ---------- 7 · city heatmap ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Correlation analysis" });
content(s, "The same drivers hold in every city, but their strength differs", "Spearman correlation with price within each city. Red = higher price, blue = lower price; stronger colour = stronger relationship.");
const heatKeys = ["person_capacity", "room_private", "attr_index_norm", "dist", "metro_dist", "guest_satisfaction_overall"];
const cities = Object.keys(corr.by_city);
const heatFill = (v) => (v >= 0 ? mix("FFFFFF", HEX.accent1, Math.min(v / 0.75, 1)) : mix("FFFFFF", HEX.accent3, Math.min(-v / 0.75, 1)));
const headerCell = (text) => ({ text, options: { bold: true, color: HEX.dk2, fill: { color: HEX.lt2 }, align: "center", valign: "middle", fontSize: 12 } });
const rows = [[headerCell(""), ...heatKeys.map((k) => headerCell(corr.labels[k].replace(" (vs. other)", "")))]];
cities.forEach((c) => {
  rows.push([
    { text: title(c), options: { bold: true, color: HEX.dk2, fontSize: 12, valign: "middle" } },
    ...heatKeys.map((k) => {
      const v = corr.by_city[c][k];
      return { text: sgn(v), options: { fill: { color: heatFill(v) }, color: Math.abs(v) >= 0.5 ? "FFFFFF" : HEX.dk1, align: "center", valign: "middle", fontSize: 12 } };
    }),
  ]);
});
s.addTable(rows, { x: M, y: BODY_TOP, w: 8.4, colW: [1.5, ...heatKeys.map(() => 6.9 / heatKeys.length)], rowH: 0.42, border: { type: "solid", pt: 1, color: "FFFFFF" }, fontFace: "Arial" });
const cityMsgs = [
  ["Room type matters most in London and Lisbon", "Private rooms there carry the deepest discount (−0.73, −0.68); in Athens and Paris the gap is far smaller."],
  ["Location premiums peak in Athens and London", "Distance to the centre lowers price most (−0.44, −0.42), so central supply is the scarce good."],
  ["Satisfaction earns at most +0.19", "Even in Amsterdam, Athens and Lisbon, the best case, ratings explain little of price."],
];
cityMsgs.forEach(([head, body], i) => {
  const y = BODY_TOP + i * 1.6;
  s.addText(head, { x: 9.4, y, w: W - M - 9.4, h: 0.5, fontSize: 15, bold: true, color: C.text2, margin: 0, valign: "top", isTextBox: true });
  s.addText(body, { x: 9.4, y: y + 0.55, w: W - M - 9.4, h: 0.95, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
});
s.addNotes("This is the city-level view of the correlation matrix, restricted to the attributes that matter. The full matrix is in notebook 02.");

// ---------- 8 · section B ----------
pres.addSection({ title: "Predictive modelling" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Predictive modelling" });
s.addText("PART B", { placeholder: "kicker" });
s.addText("From insight to revenue", { placeholder: "title" });
s.addText("A price benchmark model, and what weekday/weekend price pairs reveal about host pricing behaviour", { placeholder: "body" });

// ---------- 9 · model ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Predictive modelling" });
content(s, `A benchmark model cuts price error by ${pct(1 - gbm.MAE / cityMedian.MAE)} versus city averages, but cannot single out underpriced listings`, "Held-out test set (20% of location groups, never seen in training). Importance = increase in mean absolute error when an attribute is shuffled on validation data.");
const modelRows = [["Europe-wide median", scores["Global median"]], ["City + room type median", cityMedian], ["Gradient boosting model", gbm]];
s.addChart(pres.charts.BAR, [{ name: "Median error", labels: modelRows.map(([n]) => n), values: modelRows.map(([, r]) => r.median_APE_pct / 100) }], chartBase({
  x: M, y: BODY_TOP, w: 5.4, h: 3.3, barDir: "col", chartColors: [HEX.accent6, HEX.accent2, HEX.accent1], barGapWidthPct: 50,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "±0%", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMinVal: 0, valAxisMaxVal: 0.45,
  showTitle: true, title: "Median price error on unseen listings", titleFontSize: 14, titleColor: MUTED,
}));
const imp = DATA.model.importance.slice(0, 8).reverse();
s.addChart(pres.charts.BAR, [{ name: "MAE increase", labels: imp.map((r) => r.attribute), values: imp.map((r) => r.mae_increase) }], chartBase({
  x: 6.3, y: BODY_TOP, w: W - M - 6.3, h: 3.3, barDir: "bar", chartColors: [HEX.dk2], barGapWidthPct: 40,
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$0", valAxisHidden: true, valGridLine: { style: "none" },
  showTitle: true, title: "What the model relies on (error increase if removed)", titleFontSize: 14, titleColor: MUTED,
}));
const modelMsgs = [
  ["Useful for", "Price guidance for new and existing hosts, and an outlier review of listings far from their benchmark."],
  ["Not enough for", "Calling an individual listing underpriced. The remaining ±18% reflects what the data lacks: interior, photos, reviews, dates."],
  ["So we looked for", "Pricing behaviour we can observe directly, without a model in between (next slide)."],
];
modelMsgs.forEach(([head, body], i) => {
  const cw = (CW - 2 * 0.3) / 3;
  const x = M + i * (cw + 0.3);
  card(s, x, 5.0, cw, 1.45, C.background2, `model-msg-${i}`);
  s.addText([
    { text: head, options: { bold: true, color: C.text2, breakLine: true } },
    { text: body, options: { color: C.text1 } },
  ], { x: x + 0.2, y: 5.12, w: cw - 0.4, h: 1.25, fontSize: 13, margin: 0, valign: "top", isTextBox: true });
});
s.addNotes(`Test MAE: model ${fmtUSD(gbm.MAE)}, city/room median ${fmtUSD(cityMedian.MAE)}. Location and size dominate; ratings contribute almost nothing, consistent with the correlation analysis. Summing all positive model gaps would overstate the opportunity: roughly half of listings sit above any unbiased benchmark by construction.`);

// ---------- 10 · weekend behaviour ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Predictive modelling" });
content(s, `${pct(wk.share_same_price)} of hosts charge the same price on weekdays and weekends`, `${wk.pairs.toLocaleString("en-US")} listings observed on both day types (same coordinates, room type and capacity). "Same price" = within ±0.5%. Weekend = flag 0, to be confirmed.`);
const order = [...wk.by_city].sort((a, b) => a.share_same_price - b.share_same_price);
const allCities = { city: "All cities", share_same_price: wk.share_same_price, share_weekend_higher: wk.share_weekend_higher, share_weekday_higher: wk.share_weekday_higher };
const stackRows = [...order, allCities];
s.addChart(pres.charts.BAR, [
  { name: "Same price", labels: stackRows.map((r) => title(r.city)), values: stackRows.map((r) => r.share_same_price) },
  { name: "Weekend higher", labels: stackRows.map((r) => title(r.city)), values: stackRows.map((r) => r.share_weekend_higher) },
  { name: "Weekday higher", labels: stackRows.map((r) => title(r.city)), values: stackRows.map((r) => r.share_weekday_higher) },
], chartBase({
  x: M, y: BODY_TOP, w: 7.9, h: 4.95, barDir: "bar", barGrouping: "percentStacked", chartColors: [HEX.accent1, HEX.accent2, HEX.accent6], barGapWidthPct: 35,
  showValue: true, dataLabelPosition: "ctr", dataLabelFormatCode: '[<0.06]"";0%', dataLabelColor: "FFFFFF", dataLabelFontSize: 10,
  valAxisLabelFormatCode: "0%", valAxisMajorUnit: 0.25, showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: MUTED,
}));
s.addText(`+${pct(wk.premium_median_differentiators)}`, { x: 8.9, y: BODY_TOP + 0.2, w: 3.8, h: 0.9, fontSize: 48, bold: true, color: C.accent1, margin: 0, isTextBox: true });
s.addText("median weekend premium charged by hosts who already differentiate", { x: 8.9, y: BODY_TOP + 1.1, w: 3.8, h: 0.7, fontSize: 14, color: C.text1, margin: 0, isTextBox: true });
s.addText([
  { text: "Flat pricing is widespread: from 43% of hosts in Budapest to 82% in Athens.", options: { bullet: true, breakLine: true } },
  { text: `Flat-pricing hosts hold ${pct(wk.flat_share_of_weekend_value)} of weekend booking value in the sample.`, options: { bullet: true, breakLine: true } },
  { text: "The benchmark is what comparable neighbours already charge, not a model estimate.", options: { bullet: true } },
], { x: 8.9, y: BODY_TOP + 2.1, w: 3.8, h: 2.7, fontSize: 14, color: C.text1, margin: 0, valign: "top", paraSpaceAfter: 8, isTextBox: true });
s.addNotes("Pairs share city, exact coordinates, room type and capacity; locations with several rows per day type are excluded. The 7% charging more on weekdays may be business-travel locations and are left unchanged.");

// ---------- 11 · sizing ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Predictive modelling" });
content(s, `Adopting the neighbours' weekend premium is worth an estimated $${low.extra_revenue_musd}–${high.extra_revenue_musd}M a year in Airbnb revenue in EMEA`, "Revenue and GBV: Airbnb Q4 2025 shareholder letter (FY2025). EMEA revenue $4.73B from third-party summaries of the FY2025 10-K, to be verified. EMEA GBV derived as EMEA revenue ÷ take rate. Weekend = 2 of 7 nights.");
const chain = [
  [`$${emeaGbv.toFixed(0)}B`, "EMEA gross booking value"],
  ["× 29%", "weekend share of nights"],
  [`× ${pct(wk.flat_share_of_weekend_value)}`, "booked with flat-pricing hosts"],
  ["× 50%", "of hosts adopt"],
  [`× +${pct(wk.effective_premium_typical, 1)}`, "typical neighbour premium"],
  [`$${mid.extra_gbv_musd}M`, "extra booking value"],
  [`× ${pct(takeRate, 1)}`, "Airbnb take rate"],
  [`$${mid.extra_revenue_musd}M`, "extra revenue per year"],
];
const boxW = (CW - 7 * 0.12) / 8;
chain.forEach(([big, small], i) => {
  const x = M + i * (boxW + 0.12);
  const result = i === 5 || i === 7;
  card(s, x, BODY_TOP + 0.05, boxW, 1.55, result ? C.text2 : C.background2, `chain-${i}`);
  s.addText(big, { x: x + 0.1, y: BODY_TOP + 0.2, w: boxW - 0.2, h: 0.6, fontSize: 22, bold: true, color: result ? C.background1 : C.text2, align: "center", margin: 0, isTextBox: true });
  s.addText(small, { x: x + 0.1, y: BODY_TOP + 0.85, w: boxW - 0.2, h: 0.65, fontSize: 12, color: result ? C.accent6 : C.text1, align: "center", valign: "top", margin: 0, isTextBox: true });
});
s.addText("Scenario range, weekend bookings unchanged", { x: M, y: 3.55, w: 7, h: 0.4, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.dk2, fill: { color: HEX.lt2 }, align: "center", valign: "middle" } });
const tableRows = [[hdr("Premium adopted"), hdr("25% adoption"), hdr("50% adoption"), hdr("100% adoption"), hdr("Break-even booking loss")]];
["Conservative", "Typical"].forEach((p) => {
  const r = [25, 50, 100].map((a) => scen(p, a));
  tableRows.push([
    { text: `${p} (+${r[0].premium_pct}%)`, options: { bold: true, color: HEX.dk2, valign: "middle" } },
    ...r.map((x) => ({ text: `$${x.extra_revenue_musd}M  ($${x.extra_gbv_musd}M GBV)`, options: { align: "center", valign: "middle", color: HEX.dk1, bold: (p === "Conservative" && x.adoption_pct === 50) || (p === "Typical" && x.adoption_pct === 100) } })),
    { text: `\u2212${Math.abs(r[0].break_even_booking_change_pct)}%`, options: { align: "center", valign: "middle", color: HEX.dk1 } },
  ]);
});
s.addTable(tableRows, { x: M, y: 4.05, w: CW, colW: [2.6, 2.4, 2.4, 2.4, 2.333], rowH: 0.48, fontSize: 14, fontFace: "Arial", border: { type: "solid", pt: 0.75, color: "D3D8DE" } });
s.addText("Conservative = 25th percentile, typical = median of the premium charged by differentiating hosts in the same city and room type.", { x: M, y: 5.65, w: CW, h: 0.4, fontSize: 12, color: MUTED, margin: 0, isTextBox: true });
s.addNotes("The chain uses only reported Airbnb financials and observed host behaviour. The two bold cells bound the headline range. EMEA includes the Middle East and Africa, while the behaviour is measured in 10 large European cities: treat this as an order of magnitude.");

// ---------- 12 · sensitivity ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Predictive modelling" });
content(s, `The premium pays off as long as adopters lose fewer than ${Math.abs(mid.break_even_booking_change_pct).toFixed(0)}% of weekend bookings, which a pilot can test`, `Typical premium (+${pct(wk.effective_premium_typical, 1)}). Booking change applies to adopters' weekend nights only; all other bookings unchanged.`);
const changes = Array.from({ length: 26 }, (_, i) => i - 20);
const revenueAt = (adoption, change) => emeaGbv * 1000 * fin.weekend_share * wk.flat_share_of_weekend_value * adoption * ((1 + wk.effective_premium_typical) * (1 + change / 100) - 1) * takeRate;
s.addChart(pres.charts.LINE, [0.25, 0.5, 1].map((a) => ({ name: `${a * 100}% adoption`, labels: changes.map((c) => `${c > 0 ? "+" : c < 0 ? "−" : ""}${Math.abs(c)}%`), values: changes.map((c) => revenueAt(a, c)) })), chartBase({
  x: M, y: BODY_TOP, w: 7.6, h: 4.95, chartColors: [HEX.accent4, HEX.accent1, HEX.accent5], lineSize: 3, lineDataSymbol: "none",
  valAxisLabelFormatCode: "$#,##0\"M\"", valAxisTitle: "Extra Airbnb revenue, EMEA ($M/yr)", showValAxisTitle: true, valAxisTitleFontSize: 12, valAxisTitleColor: MUTED,
  catAxisTitle: "Change in adopters' weekend bookings", showCatAxisTitle: true, catAxisTitleFontSize: 12, catAxisTitleColor: MUTED,
  catAxisLabelFrequency: 5, catAxisLabelPos: "low", showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: MUTED,
}));
card(s, 8.6, BODY_TOP + 0.05, W - M - 8.6, 4.75, C.background2, "pilot-card");
s.addText("How we would test it", { x: 8.85, y: BODY_TOP + 0.3, w: 3.7, h: 0.45, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
s.addText([
  { text: "Two pilot cities with high flat-pricing shares, e.g. Rome and Paris", options: { bullet: true, breakLine: true } },
  { text: "Randomly nudge half of flat-pricing hosts towards their neighbours' weekend premium", options: { bullet: true, breakLine: true } },
  { text: "Measure weekend bookings, conversion and revenue against the control group for 8–12 weeks", options: { bullet: true, breakLine: true } },
  { text: "Decide on roll-out against the break-even line", options: { bullet: true } },
], { x: 8.85, y: BODY_TOP + 0.85, w: 3.7, h: 3.8, fontSize: 14, color: C.text1, margin: 0, valign: "top", paraSpaceAfter: 10, isTextBox: true });
s.addNotes("The dataset contains no demand data, so the booking response is the key unknown. All three lines cross zero at the same point because break-even depends only on the premium, not on adoption.");

// ---------- 13 · section C ----------
pres.addSection({ title: "Next steps" });
s = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Next steps" });
s.addText("PART C", { placeholder: "kicker" });
s.addText("Where the data can take Airbnb next", { placeholder: "title" });
s.addText("Adding booking data turns a price snapshot into pricing and utilization decisions", { placeholder: "body" });

// ---------- 14 · pricing × utilization ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next steps" });
content(s, "Booking data adds the missing axis: utilization turns price gaps into pricing decisions", "Illustrative framework. Utilization = booked nights ÷ available nights per listing; benchmark = the price model on slide 9.");
const gx = M + 0.75;
const gy = BODY_TOP + 0.05;
const qw = 3.45;
const qh = 2.05;
const gap = 0.12;
const quadrants = [
  [0, 0, "Underpriced", "Fully booked below benchmark: raise price, starting with the weekend premium", true],
  [1, 0, "Premium earned", "Booked despite a higher price: protect it and learn what guests pay for", false],
  [0, 1, "Listing problem, not price", "Cheap yet empty: improve photos, reviews or visibility before touching price", false],
  [1, 1, "Overpriced", "Above benchmark and empty: lower price or reposition the listing", false],
];
quadrants.forEach(([col, row, head, body, hot]) => {
  const x = gx + col * (qw + gap);
  const y = gy + row * (qh + gap);
  card(s, x, y, qw, qh, hot ? C.accent1 : C.background2, `quadrant-${col}-${row}`);
  s.addText([
    { text: head, options: { bold: true, fontSize: 18, color: hot ? C.background1 : C.text2, breakLine: true } },
    { text: body, options: { fontSize: 14, color: hot ? C.background1 : C.text1 } },
  ], { x: x + 0.25, y: y + 0.2, w: qw - 0.5, h: qh - 0.4, margin: 0, valign: "top", paraSpaceAfter: 6, isTextBox: true });
});
s.addText("High utilization", { x: M - 0.75, y: gy + qh / 2 - 0.2, w: 2.0, h: 0.4, fontSize: 12, bold: true, color: MUTED, align: "center", rotate: 270, margin: 0, isTextBox: true });
s.addText("Low utilization", { x: M - 0.75, y: gy + qh + gap + qh / 2 - 0.2, w: 2.0, h: 0.4, fontSize: 12, bold: true, color: MUTED, align: "center", rotate: 270, margin: 0, isTextBox: true });
s.addText("Price below benchmark", { x: gx, y: gy + 2 * qh + gap + 0.1, w: qw, h: 0.35, fontSize: 12, bold: true, color: MUTED, align: "center", margin: 0, isTextBox: true });
s.addText("Price above benchmark", { x: gx + qw + gap, y: gy + 2 * qh + gap + 0.1, w: qw, h: 0.35, fontSize: 12, bold: true, color: MUTED, align: "center", margin: 0, isTextBox: true });
card(s, 9.0, BODY_TOP + 0.05, W - M - 9.0, 4.75, C.text2, "utilization-card");
s.addText([
  { text: "Today we see one axis", options: { bold: true, fontSize: 16, color: C.background1, breakLine: true } },
  { text: "The price model places each listing left or right of its benchmark, but cannot tell an underpriced listing from a weaker one.", options: { color: C.accent6, breakLine: true, paraSpaceAfter: 12 } },
  { text: "Booking data adds the other", options: { bold: true, fontSize: 16, color: C.background1, breakLine: true } },
  { text: "Occupancy, lead time and cancellations per listing put every host in one quadrant with its own action.", options: { color: C.accent6, breakLine: true, paraSpaceAfter: 12 } },
  { text: "Price changes over time then reveal how bookings respond: the elasticity behind a pricing engine.", options: { color: C.accent6 } },
], { x: 9.25, y: BODY_TOP + 0.3, w: W - M - 9.5, h: 4.3, fontSize: 14, margin: 0, valign: "top", isTextBox: true });
s.addNotes("This is the analysis we could not do with the snapshot: a price gap only means 'underpriced' if the listing is also in high demand. The top-left quadrant is where price increases are safest; the bottom-left shows that some low prices are a symptom, not the problem.");

// ---------- 15 · analytics portfolio ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next steps" });
content(s, "Weekend pricing is the first of six analyses that booking data makes possible", "Each analysis builds on findings in this deck (slide references in brackets). Phase = proposed roadmap phase on the next slide.");
const portfolio = [
  ["Pricing × utilization", "Which listings are truly under- or overpriced?", "Targeted nudges in both directions (14)", "Bookings, calendars", 2],
  ["Price elasticity", "How do bookings respond to price by city, season and lead time?", "Extends the weekend lever to seasons and events (12)", "Price history, searches, conversion", 2],
  ["Quality premium", "Do top-rated listings convert better and could they charge more?", "Ratings carry no price premium today (5)", "Reviews, conversion by rating", 3],
  ["New-listing pricing", "What should a new host charge on day one?", "Benchmark model without ratings (9)", "Onboarding and first-booking data", 3],
  ["Supply gaps", "Where does demand exceed supply?", "Central supply is scarce; target host acquisition (7)", "Searches without results, occupancy by area", 3],
  ["Host retention", "Which hosts are at risk of leaving the platform?", "Protects supply in high-demand areas", "Host activity, calendars, payouts", 3],
];
const pw = (CW - 2 * 0.3) / 3;
const ph = 2.3;
portfolio.forEach(([head, question, value, data, phase], i) => {
  const x = M + (i % 3) * (pw + 0.3);
  const y = BODY_TOP + 0.05 + Math.floor(i / 3) * (ph + 0.2);
  const first = i === 0;
  card(s, x, y, pw, ph, first ? C.text2 : C.background2, `usecase-${i}`);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + pw - 1.15, y: y + 0.22, w: 0.9, h: 0.3, rectRadius: 0.15, fill: { color: phase === 2 ? C.accent1 : C.accent2 }, line: { color: phase === 2 ? C.accent1 : C.accent2 }, objectName: `phase-pill-${i}` });
  s.addText(`Phase ${phase}`, { x: x + pw - 1.15, y: y + 0.22, w: 0.9, h: 0.3, fontSize: 10, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(head, { x: x + 0.25, y: y + 0.18, w: pw - 1.5, h: 0.4, fontSize: 16, bold: true, color: first ? C.background1 : C.text2, margin: 0, valign: "top", isTextBox: true });
  s.addText([
    { text: question, options: { breakLine: true, paraSpaceAfter: 6, color: first ? C.background1 : C.text1 } },
    { text: value, options: { color: first ? C.accent4 : C.accent5, bold: true } },
  ], { x: x + 0.25, y: y + 0.65, w: pw - 0.5, h: 1.15, fontSize: 14, margin: 0, valign: "top", isTextBox: true });
  s.addText(`Data: ${data}`, { x: x + 0.25, y: y + ph - 0.45, w: pw - 0.5, h: 0.3, fontSize: 11, color: first ? C.accent6 : MUTED, margin: 0, isTextBox: true });
});
s.addNotes("The portfolio is ordered by how directly it builds on today's results. Pricing × utilization and elasticity come first because they validate and extend the weekend lever; the others reuse the same booking data foundation.");

// ---------- 16 · roadmap ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next steps" });
content(s, "Proposed roadmap: from a price snapshot to a pricing engine", "Durations are indicative and depend on data access.");
const phases = [
  ["Validate", "Weeks 1–4", ["Confirm data definitions: weekend flag, price basis, listing IDs", "Connect booking and calendar data for two pilot cities", "Design the weekend pilot"]],
  ["Pilot and measure", "Weeks 5–16", ["Run the weekend nudge as a controlled experiment", "Build the pricing × utilization matrix", "First price-elasticity estimates by city"]],
  ["Scale", "From month 5", ["Dynamic weekday, seasonal and event pricing across EMEA", "New-listing guidance and quality premium", "Supply-gap targeting and host retention"]],
];
phases.forEach(([name, when, items], i) => {
  const w = (CW - 2 * 0.3) / 3;
  const x = M + i * (w + 0.3);
  card(s, x, BODY_TOP + 0.05, w, 3.35, i === 0 ? C.text2 : C.background2, `phase-${i}`);
  numberBadge(s, i + 1, x + 0.3, BODY_TOP + 0.35, 0.55, C.accent1);
  const dark = i === 0;
  s.addText(name, { x: x + 1.05, y: BODY_TOP + 0.33, w: w - 1.3, h: 0.4, fontSize: 20, bold: true, color: dark ? C.background1 : C.text2, margin: 0, isTextBox: true });
  s.addText(when, { x: x + 1.05, y: BODY_TOP + 0.72, w: w - 1.3, h: 0.3, fontSize: 12, color: dark ? C.accent6 : MUTED, margin: 0, isTextBox: true });
  s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })), { x: x + 0.3, y: BODY_TOP + 1.35, w: w - 0.55, h: 1.95, fontSize: 14, color: dark ? C.background1 : C.text1, margin: 0, valign: "top", paraSpaceAfter: 10, isTextBox: true });
});
card(s, M, 5.2, CW, 1.2, C.background2, "data-asks");
s.addText([
  { text: "Data that unlocks phases 2 and 3:  ", options: { bold: true, color: C.text2 } },
  { text: "listing and host IDs · stay dates and calendars · bookings, search and conversion · fees and price basis · listing content (photos, amenities, reviews)", options: { color: C.text1 } },
], { x: M + 0.3, y: 5.3, w: CW - 0.6, h: 1.0, fontSize: 14, margin: 0, valign: "middle", isTextBox: true });
s.addNotes("Phase 1 is low-cost and can start immediately. The data asks (listing IDs, dates, bookings) unlock the utilization matrix and the elasticity model, and with them the full portfolio on the previous slide.");

// ---------- 17 · appendix ----------
pres.addSection({ title: "Appendix" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
content(s, "Appendix: method and assumptions", "Full analysis in notebooks 01–04 (marimo); all figures regenerate from the supplied data.");
const appendix = [
  ["Correlations", "Spearman rank correlation within each city and pooled; latitude/longitude and raw indices excluded. Associations, not causal effects."],
  ["Price model", "Gradient boosting on log price; 60/20/20 split by location group (city + coordinates) to avoid leakage; selected on validation, evaluated once on test."],
  ["Weekend pairs", "Same city, coordinates, room type and capacity on both day types; one row per day type. Flag 0 read as weekend (higher prices), to be confirmed."],
  ["Premium", "25th percentile / median premium of differentiating hosts per city × room type (city-wide when fewer than 20 references); weighted by weekend price."],
  ["Revenue sizing", "EMEA GBV = EMEA revenue ÷ group take rate (12.2 / 91.3). Static what-if: no seasonality, no demand response unless stated; EMEA includes Middle East and Africa."],
];
s.addTable(appendix.map(([k, v]) => [
  { text: k, options: { bold: true, color: HEX.dk2, fill: { color: HEX.lt2 }, valign: "middle" } },
  { text: v, options: { color: HEX.dk1, valign: "middle" } },
]), { x: M, y: BODY_TOP, w: CW, colW: [2.4, CW - 2.4], rowH: 0.88, fontSize: 14, fontFace: "Arial", border: { type: "solid", pt: 0.75, color: "D3D8DE" } });
s.addNotes("Reference slide for questions on method.");

(async () => {
  await write(OUT);
  console.log(`Wrote ${path.relative(ROOT, OUT)}`);
})();
