# Phase 1 — Repository Audit & Migration Plan

Target: *AI-Powered Intelligent Land Record Digitization and Validation System*, Telangana v1.
Baseline: `github.com/arsalaanuddin/land-record-system-ai` (cloned, working tree clean).

Everything in section 1 was measured, not assumed. Commands are listed so each claim can be re-checked.

---

## 1. VERIFIED AUDIT

### 1.1 Repository shape

| Path | Reality |
|---|---|
| `frontend/` | React 18 + Vite 5 + TypeScript 5.5 + Tailwind + Leaflet. 12 pages, 3 components, 2 CSS-heavy page dirs. Real UI, ~4.5k LOC. |
| `ai_pipeline/` | The **only working backend**. `server.py` (FastAPI, port 8000) + `routers/land_records.py` (~500 LOC) is the whole API. |
| `backend/` | **Completely empty.** All 12 files are 0 bytes: `main.py`, `database.py`, `worker.py`, `routers/{records,ingest,gis,dashboard}.py`, `schemas/land_record.py`, `requirements.txt`. It has never contained code. |
| `ai_pipeline/requirements.txt` | 0 bytes. |
| `README.md` (root) | 0 bytes. `frontend/README.md` is a stale structure doc that describes a `backend/` with PostgreSQL/PostGIS that does not exist. |
| `weights/` | `yolov8_layout.pt`, `language_detector.onnx` — **never referenced by any source file**. |
| `yolov8n.pt` (root) | 6.5 MB COCO object detector, loaded by the live router. |
| `__MACOSX/`, `*.tsbuildinfo`, `__pycache__/*.pyc` | Committed build junk. |

### 1.2 The active API (verified by reading `ai_pipeline/routers/land_records.py`)

Prefix `/api/v1`, all defined in one file:

- `POST /ingest/upload` — saves file, runs pipeline **inline**, returns `recordId`
- `GET /records` — reads every `storage/exports/*.json`
- `GET /records/{id}` — one JSON export
- `PUT /records/{id}/verify` — **returns a success message and persists nothing**
- `POST /active-learning/feedback` — returns a message, persists nothing
- `GET /dashboard/stats` — **hardcoded numbers** (12,450 / 11,200 / 1,250 / 96.4%)
- `GET /gis/parcels` — one hardcoded polygon

Storage is JSON files on disk (`storage/exports`, `storage/uploads`, both outside the repo tree, not committed). No database, no migrations, no models, no job queue, no schema versioning.

### 1.3 Hardcoded / fabricated output (must be removed)

In `POST /ingest/upload`:

- Fallback record fields injected when OCR finds nothing: `"Ramesh Balwant Kumar"`, `"142/A"`, `"2.50 Hectares"`, `"1024"`, `"KT-4891"` — written into the stored JSON as if extracted.
- `coOwners: ["Ganpat Rao Patil (50%)"]`, `ownershipType: "Joint"`, `village: "Rampur"`, `tehsil: "Haveli"`, `mutationNumber: "MUT/2026/0981"`, `landClassification`, `stampDutyStatus` — all constants.
- `cadastral_coordinates` — one hardcoded square near Pune (18.52, 73.85), Maharashtra, for a Telangana product.
- `validation.crossDatabaseChecks` — claims "DILRMP Bhu-Naksha ... verified" although no external service is called.
- `overall_confidence = 88.0` default, then replaced by mean OCR confidence; status derived from it.

### 1.4 AI modules — what they actually do

| File | Reality |
|---|---|
| `model1_yolo_layout.py` | Named YOLO, contains **no YOLO**. OpenCV morphological contours. The useful part (contour → bbox crops) must be preserved. |
| `model2_language_id.py` | **No model.** Hardcoded `if layout_type == "table"` rules; never reads pixels or text. |
| `model3_paddle_ocr.py` | Real PaddleOCR, but `lang='en'` — an English recogniser. Cannot read Telugu. |
| `model4_handwriting.py` | **Not handwriting recognition.** Morphological TOPHAT + sets `"[Handwritten Entry Detected]"`. |
| `model5_parser.py` | Two regexes (survey, area) on joined text. No semantics, no layout, no model. |
| `model6_exporter.py` | Pydantic, but validates a 5-field stub object unrelated to the record schema. |
| `routers/land_records.py` | Loads `yolov8n.pt` and a HuggingFace English NER (`dslim/bert-base-NER`) at import time; never uses the YOLO boxes (the loop body is `pass`). |

Live PaddleOCR + NER type mismatches: `PaddleOCR(use_angle_cls=True, lang='en')` is the v2 API while `model3` uses the v4/v5 keyword API (`use_doc_orientation_classify`), so the two files target different PaddleOCR majors and one of them will fail depending on the installed version.

### 1.5 Frontend — build is broken (measured)

`npm ci` → exit 0. `npm run build` (`tsc -b && vite build`) → **exit 2**, 32 errors. Root cause: `src/services/api.ts` exports only `uploadDocument/getAllRecords/getRecord/submitVerification/getDashboardStats`, while pages import `getRecords`, `getAuditLogs`, `getApiPortalData`, `login` and types `LandRecord`, `DashboardStats`, `AuditLogEntry`, `ApiKeyItem`, `IntegrationStatus`, `UserRole`. Plus 6 `TS6133` unused-`React` errors and cascading implicit-`any`.

### 1.6 Frontend — routing is half-wired

`App.tsx` defines only `/dashboard` (static JSX with hardcoded 12,450 etc.), `/upload`, `/verify/:recordId`, `/gis` (placeholder div). `Sidebar.tsx` links to `/dashboard/upload`, `/dashboard/review`, `/dashboard/records`, `/dashboard/map`, `/dashboard/reports`, `/dashboard/apis` — **none exist**. `Splash` (`/login`) is unreachable. `Layout.tsx` is a second, older shell; `AllRecords`, `ReviewQueue`, `GISMap`, `Reports`, `ApiPortal`, `Login`, `Processing` are orphaned files. `App.tsx` also reimplements verification instead of using `pages/Verification.tsx`.

### 1.7 Frontend — simulated processing (must be replaced)

`Processing.tsx` runs `setInterval(..., 1600)`, advances 5 fake stages, then navigates to **hardcoded `REC-002`**. Never calls the API. The real upload flow (`Upload.tsx` → `/verify/{recordId}`) skips it entirely.

### 1.8 Runtime environment (this workspace)

- Python 3.12.3; `cv2`, `PIL`, `sqlalchemy` importable. **Missing:** `torch`, `paddleocr`, `paddle`, `fitz` (PyMuPDF), `fasttext`, `psycopg2`, `pytest`.
- **No PostgreSQL binaries**, no Docker assumed, CPU-only, 9.7 GB free disk.
- Node 26.13.0 / npm 11.20.0; `frontend/node_modules` installed.

---

## 2. EXISTING → TARGET FILE MAPPING

Target tree is section 5 of the spec. Every row is an explicit action.

### 2.1 AI pipeline

| Existing | Target | Action |
|---|---|---|
| `server.py` | `ai_pipeline/app.py` | Move; keep CORS; mount new routers under `/api`; keep legacy `/api/v1` aliases temporarily. |
| `routers/land_records.py` | `api/{upload,processing,results,verification}.py` + `services/pipeline_service.py` | **Split and rewrite.** Upload becomes thin (validate, id, store, enqueue). Pipeline moves to service. All hardcoded record fields deleted. |
| — | `config.py` | New: paths, limits, model paths, `DATABASE_URL`, state config selection. |
| — | `preprocessing/pdf_processor.py` | New: PyMuPDF page → PNG, page order, `total_pages`. |
| `preprocessor.py` (partial), `land_records.py` CLAHE block | `preprocessing/image_preprocessor.py` | Port useful OpenCV ops; **two strategies** (printed / handwriting-friendly); never overwrite original. |
| — | `preprocessing/image_quality.py` | New: blur/contrast/resolution metrics + quality status. |
| `model1_yolo_layout.py` | `extraction/layout_extractor.py` | Keep contour fallback as `contour_fallback()`; add PP-StructureV3 backend; return regions with ids/bboxes/confidence. Drop YOLO naming. |
| — | `classification/document_classifier.py` | New: EfficientNet-B0 inference + keyword cross-check + `other` category + `requires_manual_confirmation`. |
| — | `classification/content_classifier.py` | New: MobileNetV3 per-region printed/handwritten/mixed/uncertain. |
| `model2_language_id.py` | `classification/language_detector.py` | Replace rules with Unicode-range script detection + fastText; mixed-language output; low-text handling. |
| `model3_paddle_ocr.py` | `ocr/printed_ocr.py` | Rewrite for Telugu+English (`lang='te'`/`'en'` per region), one engine instance, structured results. |
| `model4_handwriting.py` | `ocr/handwriting_ocr.py` | Split: keep sharpening as a *preprocessing* helper, add a real `HandwritingRecognizer` interface + loader; report `recognized: false` rather than inventing text. |
| — | `ocr/table_extractor.py` | New: PP-StructureV3 table → cells → `cell → text` association, bbox fallback. |
| `model5_parser.py` | `extraction/field_extractor.py` + `extraction/telangana_fields.py` | Keep regexes as `entity_normalizer` helpers; add LayoutLMv3 token-classification adapter and label-grouping. |
| `model6_exporter.py` | `schemas/{document,extraction,api}_schema.py` + `validation/field_validator.py` | Rewrite schemas to the spec's field object (value / original_text / ocr_confidence / extraction_confidence / validation_status / verification_status / source). |
| `run_pipeline.py` | `services/pipeline_service.py` | Replace monolithic demo script with staged orchestrator + per-stage status + per-page failure isolation. |
| `convert_pdf.py` | `preprocessing/pdf_processor.py` | Fold in; delete hardcoded paths. |
| `__pycache__/`, `__MACOSX/` | — | Delete from tracking. |
| `yolov8n.pt`, `weights/yolov8_layout.pt` | — | **Remove** after the YOLO loader is gone (only `land_records.py` references `yolov8n.pt`; `weights/` is unreferenced). |
| — | `database/{connection,models,repository}.py` | New: SQLAlchemy models for the 6 tables in spec §10. |
| — | `state_configs/telangana/{document_types,field_mapping,validation_rules}.json` | New: field names (Telugu labels + English), required fields per doc type, survey-number patterns, area units. |
| — | `tests/test_*.py` | New: per-module tests using saved fixtures. |

### 2.2 Backend layer

The spec's Layer 2 and the current `routers/` are the same thing. **Do not create a third backend.** `backend/` (empty) is deleted; FastAPI inside `ai_pipeline/` is the backend, organised into `api/` + `services/` + `database/`.

### 2.3 Frontend

| Existing | Action |
|---|---|
| `services/api.ts` | Rewrite to the new `/api/documents/*` endpoints; export `LandRecord`, `DashboardStats`, `AuditLogEntry`, `UserRole`, etc. |
| `api/api.ts` | **Delete** (duplicate legacy client). |
| `App.tsx` | Add real routes: `/`, `/login`, `/dashboard`, `/dashboard/upload`, `/dashboard/processing/:documentId`, `/dashboard/verification/:documentId`, `/dashboard/records`, `/dashboard/review`, `/dashboard/map`, `/dashboard/reports`, `/dashboard/apis`. Remove inline duplicate `VerificationStudio`. |
| `components/Layout.tsx` | Delete (older shell); `Sidebar.tsx` + `Navbar.tsx` become the shell. |
| `Processing.tsx` | Delete timer; poll `GET /api/documents/{id}/status`; render real stages; no fixed record id. |
| `Upload.tsx` | Post to `/api/documents/upload`; navigate to `/dashboard/processing/{documentId}`. |
| `Verification.tsx` | Show page image with bbox overlay on field select, Telugu original text, separate confidence/validation/verification badges; PUT corrections. |
| `Dashboard.tsx` | Real aggregates (uploaded / processed / failed / awaiting verification / by type). Remove fabricated accuracy + state-progress tables unless backed by stored data. |
| `AllRecords.tsx`, `ReviewQueue.tsx`, `GISMap.tsx`, `Reports.tsx`, `ApiPortal.tsx` | Keep UI; point at real endpoints. `ApiPortal`'s fake API keys/integration latency and `GISMap`'s fake polygons must not claim live government integration — mark as not configured. |
| `Login.tsx`, `Splash.tsx` | Keep; `login` becomes a local session stub (no real IdP) — labelled as such. |
| `frontend/README.md` | Replace with accurate docs. |

---

## 3. WHAT THIS ENVIRONMENT CANNOT DO

Stated up front so no phase is faked:

1. **No GPU, ~9.7 GB free disk, CPU only.** Fine-tuning EfficientNet-B0, MobileNetV3, LayoutLMv3, or a handwriting model is not possible here. Models will be *architecturally integrated with loaders and training scripts*, and the app must run without trained checkpoints (explicit "model not trained" status, never fake output).
2. **No Telangana dataset and no sample scans in the repo.** Classification, printed/handwritten, and field-extraction accuracy cannot be measured. They also cannot be *demonstrated* without at least a few real documents.
3. **No PostgreSQL server here.** Plan: SQLAlchemy models written for PostgreSQL (JSONB, proper types) with `DATABASE_URL`; local dev falls back to SQLite. Requires your approval (spec says PostgreSQL — it stays the production target).
4. **No Telugu handwriting checkpoint exists that I can honestly certify.** PaddleOCR has no handwriting model; `microsoft/trocr-base-handwritten` is English. Plan: a `HandwritingRecognizer` interface with (a) a scaffold for fine-tuning a TrOCR-style encoder-decoder on Telugu crops, (b) a low-confidence "unreadable → human review" path, (c) no invented text. Alternative to decide: hosted vision-LLM fallback (outside the agreed stack).
5. **PaddleOCR Telugu support must be verified against the installed version** before claiming Telugu OCR. This is a phase-5 gate, tested on a real crop.

---

## 4. DECISIONS NEEDED BEFORE PHASE 3

1. **Sample documents** — 3–10 real Telangana scans (Pahani, ROR-1B, Pattadar Passbook), at least one multi-page PDF and one skewed/faded scan. Without them, phases 5–7 can only be built blind.
2. **Database** — PostgreSQL-only, or SQLite for local + Postgres for deployment (recommended)?
3. **Handwriting fallback** — interface-only + manual review (recommended), or add a hosted vision model?
4. **Frontend scope** — the spec says preserve it, but `Dashboard`/`GISMap`/`ApiPortal`/`Reports` currently display invented government integration and statistics. Delete those panels, or keep them clearly labelled "not configured"?
5. **Auth** — role selection with no password (current), or real sessions?

---

## 5. PHASE PLAN

Each phase ends with a runnable check, not just files on disk.

| # | Phase | Key files | Done when |
|---|---|---|---|
| 1 | Audit | this document | ✅ complete |
| 2 | Reorg + schemas + config | `app.py`, `config.py`, `schemas/*`, `state_configs/telangana/*` | ✅ complete — package imports as `ai_pipeline.*`, enum/schema tests pass. |
| 3 | Upload + PDF → images | `api/upload.py`, `preprocessing/pdf_processor.py`, `services/storage_service.py`, `database/*` | ✅ complete — upload stores the original, renders pages and persists a document row; `GET /status` reports per-stage state. |
| 4 | Classification | `classification/*` | Real page → document type + language + region content type, with `other`/`uncertain` paths. Tests with 2 labelled images. |
| 5 | Preprocess + OCR | `preprocessing/*`, `ocr/printed_ocr.py`, `ocr/handwriting_ocr.py` | 🟡 printed Telugu verified (PaddleOCR 3.x, `te_PP-OCRv5_mobile_rec`, fixture → real Telugu text + bboxes + confidences). Handwriting still routes to human review; CER/WER not measured (no real scans). |
| 6 | Layout + tables | `extraction/layout_extractor.py`, `ocr/table_extractor.py` | Table cells reconstructed; fallback path exercised. |
| 7 | Semantic extraction | `extraction/field_extractor.py`, `telangana_fields.py`, `state_configs/*` | ✅ complete for the rule set — field objects with source bbox and separate confidences; Telugu label variants, Telugu-letter survey suffixes and unit-anchored values are covered by tests. |
| 8 | Validation + DB | `validation/*`, `database/*` | ✅ complete — required-field/format rules, warnings, verification status; corrections and audit history persisted. |
| 9 | Frontend | routes, `services/api.ts`, `Processing`, `Verification`, `Dashboard` | ✅ `npm run build` exits 0; upload → processing → extraction → correct → approve exercised through the API. |
| 10 | Tests + evaluation | `tests/*` | Per-module + pipeline tests; multi-page, mixed print/handwriting, missing-field, failure cases. Real measured numbers only. |

**Measured so far (2026-11-19).** One synthetic printed Telugu fixture (`ai_pipeline/tests/fixtures/telugu_printed_sample.png`, rendered with Noto Sans Telugu) is read as 6 lines, mean recogniser confidence 0.87; 5 lines are correct and one 3-character fragment (`paa`, 0.497) is spurious. That is a smoke test of the engine path, **not** an accuracy figure — no CER/WER, no held-out set, no real Telangana scans exist in this repo, so `extractionAccuracy` stays `null`.

### Sequencing note
Phase 2 will *also* fix the frontend build/routing, out of order, because a broken `tsc` makes every later UI verification meaningless. That work is small (routing + client types) and independent of the AI phases.

---

## 6. RISKS

- **Model downloads** (PaddleOCR ~1 GB, torch ~900 MB, LayoutLMv3 ~500 MB) may exceed disk/network budget in this VM; each phase must degrade to an explicit "engine unavailable" status rather than a crash or fake result.
- **Telugu OCR quality on historical scans** is the single largest unknown; it is measurable only with real documents.
- **LayoutLMv3 needs labels.** Until fine-tuning data exists, field extraction is regex + config-driven rules, explicitly labelled as such in the output (`extraction_method: "rules"`), never presented as model output.
