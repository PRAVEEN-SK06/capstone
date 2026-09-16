const pptxgen = require("D:/pm_env_support/node_deck/node_modules/pptxgenjs");

// Palette: "Midnight Executive" — navy dominant, ice blue accent, white.
const NAVY = "1E2761";
const NAVY_DARK = "141A47";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const INK = "1A1D2E";
const MUTED = "5B6485";
const GOOD = "2E7D5B";
const WARN = "B8621B";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
const W = 13.33, H = 7.5;

function titleSlideBg(slide) {
  slide.background = { color: NAVY };
}

function lightSlide(slide) {
  slide.background = { color: WHITE };
}

function header(slide, kicker, title) {
  slide.addText(kicker.toUpperCase(), {
    x: 0.6, y: 0.45, w: W - 1.2, h: 0.35, isTextBox: true,
    fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED, charSpacing: 2,
  });
  slide.addText(title, {
    x: 0.6, y: 0.78, w: W - 1.2, h: 0.75, isTextBox: true,
    fontFace: "Cambria", fontSize: 30, bold: true, color: NAVY, margin: 0,
  });
}

function pageNum(slide, n) {
  slide.addText(String(n), {
    x: W - 0.9, y: H - 0.55, w: 0.5, h: 0.35, isTextBox: true,
    fontFace: "Calibri", fontSize: 11, color: MUTED, align: "right",
  });
}

function iconCircle(slide, x, y, size, bgColor, glyph, glyphColor) {
  slide.addShape("ellipse", { x, y, w: size, h: size, fill: { color: bgColor }, line: { type: "none" } });
  slide.addText(glyph, {
    x, y, w: size, h: size, isTextBox: true, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: size * 28, color: glyphColor, margin: 0,
  });
}

function statTile(slide, x, y, w, h, value, label, valueColor) {
  slide.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.08, fill: { color: "F4F6FC" }, line: { type: "none" },
    shadow: { type: "outer", color: "1E2761", opacity: 0.12, blur: 6, offset: 2, angle: 90 },
  });
  slide.addText(value, {
    x, y: y + 0.18, w, h: h - 0.7, isTextBox: true, align: "center", valign: "middle",
    fontFace: "Cambria", fontSize: 40, bold: true, color: valueColor || NAVY, margin: 0,
  });
  slide.addText(label, {
    x: x + 0.15, y: y + h - 0.5, w: w - 0.3, h: 0.4, isTextBox: true, align: "center",
    fontFace: "Calibri", fontSize: 12, color: MUTED, margin: 0,
  });
}

// ============================================================ Slide 1 — Title
{
  const s = pres.addSlide();
  titleSlideBg(s);
  iconCircle(s, 0.9, 0.9, 0.9, "2A3372", "\uD83E\uDDE0", ICE);
  s.addText("PaperMind", {
    x: 0.9, y: 2.6, w: 10, h: 1.1, isTextBox: true,
    fontFace: "Cambria", fontSize: 54, bold: true, color: WHITE, margin: 0,
  });
  s.addText("Research Paper Answer Bot — a RAG system over seminal GenAI papers", {
    x: 0.9, y: 3.6, w: 10.5, h: 0.6, isTextBox: true,
    fontFace: "Calibri", fontSize: 20, color: ICE, margin: 0,
  });
  s.addText([
    { text: "GenAI Pinnacle Plus Program — Capstone Project\n", options: { bold: true } },
    { text: "Name: ___________________     Date: ___________________" },
  ], {
    x: 0.9, y: 6.3, w: 10.5, h: 0.8, isTextBox: true,
    fontFace: "Calibri", fontSize: 14, color: ICE, lineSpacingMultiple: 1.4, margin: 0,
  });
}

// ============================================================ Slide 2 — Problem Statement
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Problem Statement", "Ask questions of research papers, get grounded answers");
  s.addText([
    { text: "Business context\n", options: { bold: true, color: NAVY, fontSize: 16 } },
    { text: "An ArXiv-like organization holds a curated set of important GenAI/LLM research papers. Researchers need to query this corpus in natural language rather than manually searching PDFs.\n\n", options: { breakLine: true } },
    { text: "Objective\n", options: { bold: true, color: NAVY, fontSize: 16 } },
    { text: "Build a RAG system that indexes the papers, retrieves relevant passages for a query, and generates accurate answers grounded strictly in the retrieved text — with citations.\n\n", options: { breakLine: true } },
    { text: "Use case\n", options: { bold: true, color: NAVY, fontSize: 16 } },
    { text: "A researcher asks \u201CWhat problem does LoRA solve?\u201D and gets a direct answer plus the exact paper + page it came from — not a link dump to go read themselves." },
  ], {
    x: 0.6, y: 1.8, w: 7.3, h: 5.2, isTextBox: true,
    fontFace: "Calibri", fontSize: 15, color: INK, lineSpacingMultiple: 1.25, margin: 0,
  });

  // Right: 6-paper stack visual
  const papers = ["BERT", "Attention Is\nAll You Need", "GPT-3", "InstructGPT", "LoRA", "SELF-RAG"];
  const colX = 8.3, colW = 4.4;
  s.addShape("roundRect", { x: colX, y: 1.75, w: colW, h: 5.15, rectRadius: 0.08, fill: { color: "F4F6FC" }, line: { type: "none" } });
  s.addText("THE CORPUS — 6 PAPERS", { x: colX + 0.3, y: 2.0, w: colW - 0.6, h: 0.35, isTextBox: true, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED, charSpacing: 1 });
  papers.forEach((p, i) => {
    const py = 2.5 + i * 0.72;
    s.addShape("roundRect", { x: colX + 0.3, y: py, w: colW - 0.6, h: 0.58, rectRadius: 0.06, fill: { color: WHITE }, line: { color: "DDE3F5", width: 1 } });
    s.addText(p, { x: colX + 0.5, y: py, w: colW - 1.0, h: 0.58, isTextBox: true, valign: "middle", fontFace: "Calibri", fontSize: 13, bold: true, color: NAVY, margin: 0 });
  });
  pageNum(s, 2);
}

// ============================================================ Slide 3 — Architecture
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Architecture Overview", "End-to-end RAG pipeline");

  const steps = [
    ["\uD83D\uDCC4", "PDF Papers", "6 papers, per-page text extraction"],
    ["\u2702\uFE0F", "Chunking", "Recursive splitter, 900 chars / 150 overlap"],
    ["\uD83E\uDDEE", "Embeddings", "HuggingFace (local) or Gemini (commercial)"],
    ["\uD83D\uDDC3\uFE0F", "Vector DB", "FAISS + BM25 (hybrid lexical index)"],
    ["\uD83D\uDD0D", "Retriever", "Dense / MMR / Hybrid / Reranked"],
    ["\u2728", "Gemini LLM", "Strict grounded-answer generation"],
  ];
  const boxW = 1.85, boxH = 1.5, gap = 0.15, startX = 0.6, y = 2.3;
  steps.forEach((step, i) => {
    const x = startX + i * (boxW + gap);
    s.addShape("roundRect", { x, y, w: boxW, h: boxH, rectRadius: 0.1, fill: { color: i === 5 ? NAVY : "F4F6FC" }, line: { type: "none" } });
    s.addText(step[0], { x, y: y + 0.12, w: boxW, h: 0.5, isTextBox: true, align: "center", fontFace: "Calibri", fontSize: 22, margin: 0 });
    s.addText(step[1], { x: x + 0.08, y: y + 0.6, w: boxW - 0.16, h: 0.35, isTextBox: true, align: "center", fontFace: "Calibri", fontSize: 12, bold: true, color: i === 5 ? WHITE : NAVY, margin: 0 });
    s.addText(step[2], { x: x + 0.08, y: y + 0.95, w: boxW - 0.16, h: 0.5, isTextBox: true, align: "center", fontFace: "Calibri", fontSize: 9.5, color: i === 5 ? ICE : MUTED, margin: 0 });
    if (i < steps.length - 1) {
      s.addText("\u2192", { x: x + boxW, y: y + 0.45, w: gap, h: 0.6, isTextBox: true, align: "center", fontFace: "Calibri", fontSize: 16, color: MUTED, margin: 0 });
    }
  });

  s.addShape("roundRect", { x: 0.6, y: 4.3, w: 12.1, h: 1.9, rectRadius: 0.08, fill: { color: "F4F6FC" }, line: { type: "none" } });
  s.addText([
    { text: "Answer + Top-3 Citations\n", options: { bold: true, color: NAVY, fontSize: 15, breakLine: true } },
    { text: "Every response cites paper title + page number for the passages it was grounded in, and the model is instructed to answer \u201CI don\u2019t know based on the provided papers\u201D when the retrieved context doesn\u2019t contain the answer \u2014 rather than guessing.", options: { color: INK, fontSize: 13 } },
  ], { x: 0.9, y: 4.55, w: 11.5, h: 1.5, isTextBox: true, fontFace: "Calibri", lineSpacingMultiple: 1.2, margin: 0 });
  pageNum(s, 3);
}

// ============================================================ Slide 4 — Data & Chunking (1)
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Data & Chunking — Dataset", "Six papers, extracted per page for accurate citations");

  const rows = [
    ["Paper", "Pages", "Extracted chars"],
    ["Attention Is All You Need", "15", "39,585"],
    ["BERT", "16", "64,087"],
    ["GPT-3 (Few-Shot Learners)", "75", "236,657"],
    ["InstructGPT", "68", "181,755"],
    ["LoRA", "26", "82,529"],
    ["SELF-RAG", "30", "105,688"],
  ];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({
    text: c,
    options: {
      fontFace: "Calibri", fontSize: 13, color: i === 0 ? WHITE : INK,
      bold: i === 0 || j === 0, fill: { color: i === 0 ? NAVY : (i % 2 === 0 ? "F4F6FC" : WHITE) },
      align: j === 0 ? "left" : "center", valign: "middle",
    },
  }))), { x: 0.6, y: 1.9, w: 7.0, h: 3.6, border: { type: "none" }, autoPage: false, rowH: 0.5 });

  statTile(s, 8.0, 1.9, 2.2, 1.6, "230", "pages loaded", NAVY);
  statTile(s, 10.4, 1.9, 2.2, 1.6, "710K", "characters extracted", NAVY);
  statTile(s, 8.0, 3.7, 2.2, 1.6, "1,021", "final chunks", GOOD);
  statTile(s, 10.4, 3.7, 2.2, 1.6, "100%", "pages had usable text\n(no OCR needed)", GOOD);
  pageNum(s, 4);
}

// ============================================================ Slide 5 — Chunking strategy
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Data & Chunking — Strategy", "Three approaches compared; recursive splitting selected");

  const rows = [
    ["Strategy", "Chunks", "Avg chars", "Verdict"],
    ["Fixed-size", "898", "790.5", "Cuts mid-sentence, no boundary awareness"],
    ["Recursive splitter", "1,021", "780.1", "Clean boundaries, predictable size \u2014 chosen"],
    ["Semantic (embedding-based)", "576", "1,232.2", "Coherent but highly variable size, slowest"],
  ];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({
    text: c,
    options: {
      fontFace: "Calibri", fontSize: 13, color: i === 0 ? WHITE : INK,
      bold: i === 0, fill: { color: i === 0 ? NAVY : (i === 2 ? "E7F0E9" : (i % 2 === 0 ? "F4F6FC" : WHITE)) },
      align: j === 0 ? "left" : (j === 3 ? "left" : "center"), valign: "middle",
    },
  }))), { x: 0.6, y: 1.9, w: 12.1, colW: [3.0, 1.6, 1.8, 5.7], h: 2.4, border: { type: "none" }, autoPage: false, rowH: 0.6 });

  s.addShape("roundRect", { x: 0.6, y: 4.7, w: 12.1, h: 1.9, rectRadius: 0.08, fill: { color: "F4F6FC" }, line: { type: "none" } });
  s.addText([
    { text: "Why recursive splitting won: ", options: { bold: true, color: NAVY, fontSize: 14 } },
    { text: "it respects paragraph/sentence boundaries so chunks read cleanly, produces a predictable chunk-size distribution (important for comparable retrieval scores), and is far cheaper to compute than the semantic approach, which must embed every sentence up front.", options: { color: INK, fontSize: 13 } },
  ], { x: 0.9, y: 4.95, w: 11.5, h: 1.5, isTextBox: true, fontFace: "Calibri", lineSpacingMultiple: 1.25, margin: 0 });
  pageNum(s, 5);
}

// ============================================================ Slide 6 — Embeddings
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Embeddings", "Open-source vs. commercial, compared head-to-head");

  const colW = 5.6, y = 1.9, h = 3.9;
  // Left card - HuggingFace
  s.addShape("roundRect", { x: 0.6, y, w: colW, h, rectRadius: 0.1, fill: { color: "F4F6FC" }, line: { type: "none" } });
  s.addText("OPEN-SOURCE", { x: 0.9, y: y + 0.25, w: colW - 0.6, h: 0.3, isTextBox: true, fontFace: "Calibri", fontSize: 11, bold: true, color: MUTED, charSpacing: 1 });
  s.addText("BAAI/bge-small-en-v1.5", { x: 0.9, y: y + 0.55, w: colW - 0.6, h: 0.45, isTextBox: true, fontFace: "Cambria", fontSize: 20, bold: true, color: NAVY, margin: 0 });
  s.addText([
    { text: "\u2022 Runs 100% locally on CPU, zero API cost\n", options: { breakLine: true } },
    { text: "\u2022 Indexed full corpus: 1,021 chunks\n", options: { breakLine: true } },
    { text: "\u2022 Time to embed full corpus: ~150-430s\n", options: { breakLine: true } },
    { text: "\u2022 Used as the app's production index" },
  ], { x: 0.9, y: y + 1.15, w: colW - 0.6, h: 2.2, isTextBox: true, fontFace: "Calibri", fontSize: 13.5, color: INK, lineSpacingMultiple: 1.35, margin: 0 });

  // Right card - Gemini
  s.addShape("roundRect", { x: 0.6 + colW + 0.3, y, w: colW, h, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("COMMERCIAL", { x: 0.9 + colW + 0.3, y: y + 0.25, w: colW - 0.6, h: 0.3, isTextBox: true, fontFace: "Calibri", fontSize: 11, bold: true, color: ICE, charSpacing: 1 });
  s.addText("Gemini gemini-embedding-001", { x: 0.9 + colW + 0.3, y: y + 0.55, w: colW - 0.6, h: 0.45, isTextBox: true, fontFace: "Cambria", fontSize: 20, bold: true, color: WHITE, margin: 0 });
  s.addText([
    { text: "\u2022 3072-dim vectors, hosted API\n", options: { breakLine: true } },
    { text: "\u2022 Indexed a representative sample: 60 chunks (10/paper)\n", options: { breakLine: true } },
    { text: "\u2022 Time to embed sample: ~4-11s\n", options: { breakLine: true } },
    { text: "\u2022 Sampled deliberately \u2014 embedding the full 1,021-chunk corpus through a paid API for a comparison exercise isn't worth the cost/quota" },
  ], { x: 0.9 + colW + 0.3, y: y + 1.15, w: colW - 0.6, h: 2.6, isTextBox: true, fontFace: "Calibri", fontSize: 13.5, color: ICE, lineSpacingMultiple: 1.3, margin: 0 });
  pageNum(s, 6);
}

// ============================================================ Slide 7 — Vector DB & Retrieval
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Vector DB & Retrieval", "FAISS + BM25, four retrieval strategies compared");

  s.addText([
    { text: "Vector database: ", options: { bold: true, color: NAVY } },
    { text: "FAISS (local, in-memory) \u2014 zero setup, fast nearest-neighbour search, right-sized for a single-digit-GB corpus like this one.", options: { color: INK } },
  ], { x: 0.6, y: 1.85, w: 12.1, h: 0.55, isTextBox: true, fontFace: "Calibri", fontSize: 13.5, lineSpacingMultiple: 1.2, margin: 0 });

  const rows = [
    ["Strategy", "How it works", "Example: \u201Clow-rank matrices\u201D query"],
    ["Dense (cosine)", "Baseline vector similarity", "Top hit: LoRA p9, score 0.75"],
    ["MMR", "Relevance + diversity", "Top hit: LoRA p9, score 1.0"],
    ["Hybrid (BM25 + dense, RRF)", "Lexical + semantic fusion", "Top hit: LoRA p1, score 0.032"],
    ["Hybrid + reranker", "Cross-encoder re-scores candidates", "Top hit: LoRA p1, score 4.84 \u2014 selected"],
  ];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({
    text: c,
    options: {
      fontFace: "Calibri", fontSize: 12.5, color: i === 0 ? WHITE : INK,
      bold: i === 0, fill: { color: i === 0 ? NAVY : (i === 4 ? "E7F0E9" : (i % 2 === 0 ? "F4F6FC" : WHITE)) },
      align: "left", valign: "middle",
    },
  }))), { x: 0.6, y: 2.55, w: 12.1, colW: [3.0, 3.5, 5.6], h: 3.0, border: { type: "none" }, autoPage: false, rowH: 0.6 });

  s.addText("Selected for the app: Hybrid (BM25 + dense) \u2014 best precision/recall trade-off without the reranker's extra latency; reranker kept available as the highest-precision option.", {
    x: 0.6, y: 5.75, w: 12.1, h: 0.9, isTextBox: true, fontFace: "Calibri", fontSize: 13, italic: true, color: MUTED, lineSpacingMultiple: 1.2, margin: 0,
  });
  pageNum(s, 7);
}

// ============================================================ Slide 8 — RAG Pipeline
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "RAG Pipeline", "Prompt design, LLM, and grounded generation");

  s.addShape("roundRect", { x: 0.6, y: 1.9, w: 6.9, h: 4.7, rectRadius: 0.1, fill: { color: "F4F6FC" }, line: { type: "none" } });
  s.addText("PROMPT DESIGN", { x: 0.9, y: 2.1, w: 6.3, h: 0.3, isTextBox: true, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED, charSpacing: 1 });
  s.addText([
    { text: "1. Answer ONLY from provided context\n", options: { breakLine: true, bold: true } },
    { text: "   No outside knowledge, ever.\n\n", options: { breakLine: true, fontSize: 12, color: MUTED } },
    { text: "2. Say \u201CI don\u2019t know\u201D when insufficient\n", options: { breakLine: true, bold: true } },
    { text: "   Hard-coded refusal string \u2014 makes hallucination-refusal measurable in evaluation.\n\n", options: { breakLine: true, fontSize: 12, color: MUTED } },
    { text: "3. Use conversation history for follow-ups\n", options: { breakLine: true, bold: true } },
    { text: "   But still ground the answer in retrieved passages.", options: { fontSize: 12, color: MUTED } },
  ], { x: 0.9, y: 2.55, w: 6.3, h: 3.8, isTextBox: true, fontFace: "Calibri", fontSize: 14, color: INK, lineSpacingMultiple: 1.2, margin: 0 });

  s.addShape("roundRect", { x: 7.8, y: 1.9, w: 4.9, h: 4.7, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("LLM & CITATIONS", { x: 8.1, y: 2.1, w: 4.3, h: 0.3, isTextBox: true, fontFace: "Calibri", fontSize: 12, bold: true, color: ICE, charSpacing: 1 });
  s.addText([
    { text: "Model: ", options: { bold: true } }, { text: "Google Gemini (Flash)\n\n", options: { breakLine: true } },
    { text: "Chain: ", options: { bold: true } }, { text: "Custom LCEL-style pipeline in src/rag_chain.py\n\n", options: { breakLine: true } },
    { text: "Output: ", options: { bold: true } }, { text: "Answer + top-3 cited passages, each with paper title, page number, and retrieval score" },
  ], { x: 8.1, y: 2.55, w: 4.3, h: 3.8, isTextBox: true, fontFace: "Calibri", fontSize: 13.5, color: WHITE, lineSpacingMultiple: 1.3, margin: 0 });
  pageNum(s, 8);
}

// ============================================================ Slide 9 — Results & Demo
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Results & Demo", "12-question evaluation set, honestly assessed");

  statTile(s, 0.6, 1.9, 2.85, 1.7, "100%", "correct paper retrieved\nin top-6, every question", GOOD);
  statTile(s, 3.6, 1.9, 2.85, 1.7, "9/10", "answerable questions\ncorrectly answered", GOOD);
  statTile(s, 6.6, 1.9, 2.85, 1.7, "1", "genuine hedging\nfailure found (q1)", WARN);
  statTile(s, 9.6, 1.9, 2.85, 1.7, "2/2", "unanswerable /\nmislabeled Qs handled right", GOOD);

  s.addShape("roundRect", { x: 0.6, y: 3.9, w: 12.1, h: 2.7, rectRadius: 0.1, fill: { color: "F4F6FC" }, line: { type: "none" } });
  s.addText("SAMPLE Q&A", { x: 0.9, y: 4.1, w: 5, h: 0.3, isTextBox: true, fontFace: "Calibri", fontSize: 12, bold: true, color: MUTED, charSpacing: 1 });
  s.addText([
    { text: "Q: What are the two main pretraining tasks used to train BERT?\n", options: { breakLine: true, bold: true, color: NAVY } },
    { text: "A: BERT is pre-trained using two unsupervised tasks: \u201Cmasked language model\u201D (MLM) and \u201Cnext sentence prediction\u201D (NSP)...\n\n", options: { breakLine: true, color: INK } },
    { text: "Sources: ", options: { bold: true, color: NAVY } },
    { text: "[1] BERT p1  \u00b7  [2] BERT p4  \u00b7  [3] BERT p16", options: { color: MUTED, italic: true } },
  ], { x: 0.9, y: 4.45, w: 11.5, h: 2.0, isTextBox: true, fontFace: "Calibri", fontSize: 13, lineSpacingMultiple: 1.25, margin: 0 });
  pageNum(s, 9);
}

// ============================================================ Slide 10 — Stretch Goals
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Stretch Goals", "Two implemented: a polished UI and conversational memory");

  const colW = 5.6, y = 1.9, h = 4.6;
  s.addShape("roundRect", { x: 0.6, y, w: colW, h, rectRadius: 0.1, fill: { color: "F4F6FC" }, line: { type: "none" } });
  iconCircle(s, 0.9, y + 0.3, 0.55, NAVY, "\uD83D\uDCAC", WHITE);
  s.addText("Option 2 \u2014 Streamlit App", { x: 1.65, y: y + 0.3, w: colW - 1.2, h: 0.55, isTextBox: true, valign: "middle", fontFace: "Cambria", fontSize: 16, bold: true, color: NAVY, margin: 0 });
  s.addText([
    { text: "\u2022 Full chat UI with sidebar controls\n", options: { breakLine: true } },
    { text: "\u2022 Switch embedding model & retrieval strategy live\n", options: { breakLine: true } },
    { text: "\u2022 Expandable \u201CSources\u201D panel per answer\n", options: { breakLine: true } },
    { text: "\u2022 Deployment-ready: Docker + Streamlit Cloud config" },
  ], { x: 0.9, y: y + 1.1, w: colW - 0.6, h: 3.2, isTextBox: true, fontFace: "Calibri", fontSize: 14, color: INK, lineSpacingMultiple: 1.35, margin: 0 });

  s.addShape("roundRect", { x: 0.6 + colW + 0.3, y, w: colW, h, rectRadius: 0.1, fill: { color: "F4F6FC" }, line: { type: "none" } });
  iconCircle(s, 0.9 + colW + 0.3, y + 0.3, 0.55, NAVY, "\uD83E\uDDE0", WHITE);
  s.addText("Option 1 \u2014 Conversational Memory", { x: 1.65 + colW + 0.3, y: y + 0.3, w: colW - 1.2, h: 0.55, isTextBox: true, valign: "middle", fontFace: "Cambria", fontSize: 16, bold: true, color: NAVY, margin: 0 });
  s.addText([
    { text: "Follow-up: ", options: { bold: true } }, { text: "\u201CWhat benchmark datasets did it use for evaluation?\u201D\n\n", options: { breakLine: true, italic: true } },
    { text: "Rewritten standalone: ", options: { bold: true } }, { text: "\u201CWhat benchmark datasets did SELF-RAG use for evaluation?\u201D", options: { italic: true, color: GOOD } },
  ], { x: 0.9 + colW + 0.3, y: y + 1.1, w: colW - 0.6, h: 3.2, isTextBox: true, fontFace: "Calibri", fontSize: 14, color: INK, lineSpacingMultiple: 1.4, margin: 0 });
  pageNum(s, 10);
}

// ============================================================ Slide 11 — Challenges & Learnings
{
  const s = pres.addSlide();
  lightSlide(s);
  header(s, "Challenges & Learnings", "Three real problems hit during development \u2014 and how each was resolved");

  const items = [
    ["\u26A0\uFE0F", "Gemini free-tier quota as low as 20 requests/day", "Discovered mid-evaluation when a working model suddenly 429'd. Fixed by making the evaluation script resumable \u2014 it saves after every question and skips completed ones \u2014 with backoff that honours the server's own retry delay."],
    ["\uD83D\uDCC4", "A dataset file was mislabeled", "\u201CRAG.pdf\u201D in the provided dataset is actually SELF-RAG, not the original RAG paper. Caught when a test question about RAG-Sequence/RAG-Token was correctly refused \u2014 the model was right, the question was wrong. Fixed the filename and the question."],
    ["\uD83E\uDD14", "An LLM-judge can be wrong in a findable way", "The automated judge scored an incorrect refusal as fully relevant, since it only checks the answer's internal consistency, not whether the context actually held one. Reading raw answers, not just scores, caught this."],
  ];
  let y = 1.85;
  items.forEach((item) => {
    iconCircle(s, 0.6, y, 0.5, "F4F6FC", item[0], NAVY);
    s.addText(item[1], { x: 1.3, y: y - 0.03, w: 11.2, h: 0.4, isTextBox: true, fontFace: "Calibri", fontSize: 15, bold: true, color: NAVY, margin: 0 });
    s.addText(item[2], { x: 1.3, y: y + 0.4, w: 11.2, h: 1.05, isTextBox: true, fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacingMultiple: 1.2, margin: 0 });
    y += 1.78;
  });
  pageNum(s, 11);
}

// ============================================================ Slide 12 — Conclusion
{
  const s = pres.addSlide();
  titleSlideBg(s);
  s.addText("Conclusion", {
    x: 0.9, y: 0.9, w: 10, h: 0.8, isTextBox: true, fontFace: "Cambria", fontSize: 34, bold: true, color: WHITE, margin: 0,
  });
  s.addText([
    { text: "What was built\n", options: { bold: true, color: ICE, fontSize: 16, breakLine: true } },
    { text: "A full RAG pipeline over 6 GenAI papers: page-level PDF loading, 3 chunking strategies compared, 2 embedding models compared, 4 retrieval strategies compared, grounded generation with citations, and an honest quantitative evaluation \u2014 plus a polished Streamlit app with conversational memory.\n\n", options: { color: WHITE, fontSize: 14, breakLine: true } },
    { text: "What's next\n", options: { bold: true, color: ICE, fontSize: 16, breakLine: true } },
    { text: "\u2022 Fix the q1-style hedging failure with a context-completeness hint in the prompt\n", options: { color: WHITE, fontSize: 14, breakLine: true } },
    { text: "\u2022 Strengthen the LLM-judge to check context sufficiency before accepting a refusal\n", options: { color: WHITE, fontSize: 14, breakLine: true } },
    { text: "\u2022 Add Corrective RAG (web-search fallback) and a larger evaluation set", options: { color: WHITE, fontSize: 14 } },
  ], { x: 0.9, y: 2.0, w: 11.0, h: 4.7, isTextBox: true, fontFace: "Calibri", lineSpacingMultiple: 1.3, margin: 0 });
  pageNum(s, 12);
}

pres.writeFile({ fileName: "presentation/PaperMind_Capstone.pptx" }).then(() => {
  console.log("Wrote presentation/PaperMind_Capstone.pptx");
});
