// Shared theme, slide layouts and drawing helpers for both decks.
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

const THEME = {
  name: "ADV Airbnb Insights",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "1F2328",
    lt1: "FFFFFF",
    dk2: "17233A",
    lt2: "F2F4F7",
    accent1: "E04F5F",
    accent2: "8C99A6",
    accent3: "2F6F8F",
    accent4: "F2A7AE",
    accent5: "C0283A",
    accent6: "D3D8DE",
    hlink: "2F6F8F",
    folHlink: "5B6B7B",
  },
};
const HEX = THEME.colors;
const MUTED = "5B6670";
const W = 13.333; // LAYOUT_WIDE is 13.333 x 7.5 in
const M = 0.6;
const CW = W - 2 * M;
const BODY_TOP = 1.55;

const fmtUSD = (v) => `$${Math.round(v).toLocaleString("en-US")}`;
const pct = (v, d = 0) => `${(v * 100).toFixed(d)}%`;
const sgn = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(2);
const title = (s) => s.charAt(0).toUpperCase() + s.slice(1);

function mix(hexA, hexB, t) {
  const a = hexA.match(/../g).map((h) => parseInt(h, 16));
  const b = hexB.match(/../g).map((h) => parseInt(h, 16));
  return a.map((v, i) => Math.round(v + (b[i] - v) * t).toString(16).padStart(2, "0")).join("").toUpperCase();
}

function chartBase(extra = {}) {
  return {
    catAxisLabelColor: MUTED,
    valAxisLabelColor: MUTED,
    catAxisLabelFontFace: "+mn-lt",
    valAxisLabelFontFace: "+mn-lt",
    dataLabelFontFace: "+mn-lt",
    legendFontFace: "+mn-lt",
    titleFontFace: "+mn-lt",
    catAxisLabelFontSize: 12,
    valAxisLabelFontSize: 11,
    dataLabelFontSize: 11,
    dataLabelColor: HEX.dk1,
    valGridLine: { color: "E3E6EA", size: 0.75 },
    catGridLine: { style: "none" },
    catAxisLineShow: false,
    valAxisLineShow: false,
    showLegend: false,
    ...extra,
  };
}

// A new presentation with the three layouts (TITLE_DARK, SECTION_DARK, CONTENT) and helpers
// bound to it. `footer` is the running text at the bottom of content slides.
function createDeck({ title: deckTitle, footer }) {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = deckTitle;
  pres.author = "ADV";
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "TITLE_DARK",
    background: { color: HEX.dk2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: M, y: 2.2, w: 10.5, h: 1.9, fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "subtitle", type: "body", x: M, y: 4.3, w: 10.5, h: 1.0, fontSize: 18, color: C.accent6, valign: "top", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "meta", type: "body", x: M, y: 6.4, w: 10.5, h: 0.4, fontSize: 12, color: C.accent2, margin: 0 }, text: "" } },
    ],
  });

  pres.defineSlideMaster({
    title: "SECTION_DARK",
    background: { color: HEX.dk2 },
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: M, y: 2.5, w: 10, h: 0.5, fontSize: 16, bold: true, color: C.accent1, margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: M, y: 3.0, w: 11, h: 1.2, fontSize: 36, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: M, y: 4.3, w: 10, h: 1.2, fontSize: 16, color: C.accent6, valign: "top", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent2, align: "right" },
  });

  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: HEX.lt1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: M, y: 0.4, w: CW, h: 1.0, fontSize: 26, bold: true, color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "source", type: "body", x: M, y: 6.62, w: CW - 1, h: 0.32, fontSize: 10, color: C.accent2, valign: "bottom", margin: 0 }, text: "" } },
      { text: { text: footer, options: { x: M, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent2, margin: 0 } } },
    ],
    slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent2, align: "right" },
  });

  function content(slide, heading, source) {
    slide.addText(heading, { placeholder: "title" });
    if (source) slide.addText(source, { placeholder: "source" });
  }

  function numberBadge(slide, n, x, y, d = 0.5, fill = C.accent1) {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: `badge-${n}` });
    slide.addText(String(n), { x, y, w: d, h: d, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
  }

  function card(slide, x, y, w, h, fill = C.background2, name = "card") {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill }, objectName: name });
  }

  async function write(fileName) {
    await pres.writeFile({ fileName });
    await applyTheme(fileName, THEME);
  }

  return { pres, C, content, numberBadge, card, write };
}

module.exports = { THEME, HEX, MUTED, W, M, CW, BODY_TOP, fmtUSD, pct, sgn, title, mix, chartBase, createDeck };
