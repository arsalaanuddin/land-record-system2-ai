# Intelligent Land Record Digitization & Validation System (LRDS)

An AI-powered, DILRMP-compliant end-to-end platform for extracting, classifying, and validating historical land records (7/12 extracts, Jamabandi, Bhoomi RTC, Cadastral Maps) in multiple Indian languages with Human-in-the-Loop (HITL) review and Cadastral GIS mapping.

---

## 🏛️ System Architecture

```
land-record-system/
│
├── frontend/                               # React.js Frontend (Vite)
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   └── api.ts                      # Service calls matching backend endpoints
│   │   ├── components/
│   │   │   ├── Navbar.tsx                  # Top banner, node health & live telemetry
│   │   │   ├── Sidebar.tsx                 # Navigation, RBAC badges, collapse toggle
│   │   │   └── Layout.tsx                  # App layout shell
│   │   ├── pages/
│   │   │   ├── Upload.tsx                  # POST /api/v1/ingest/upload UI
│   │   │   ├── Verification.tsx            # HITL side-by-side review & bounding box viewer
│   │   │   ├── Dashboard.tsx               # Stats, error distribution & progress charts
│   │   │   ├── GISMap.tsx                  # Leaflet / PostGIS cadastral parcel mapping
│   │   │   ├── ReviewQueue.tsx             # Flagged low-confidence review queue (<85%)
│   │   │   ├── AllRecords.tsx              # Searchable digitized record repository
│   │   │   ├── Reports.tsx                 # SHA-256 document archive & audit log
│   │   │   ├── ApiPortal.tsx               # GovTech OpenAPI docs & gateway keys
│   │   │   └── Login.tsx                   # Role-Based Access Control (RBAC)
│   │   ├── App.tsx                         # Router configuration
│   │   └── main.tsx                        # Application root
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                                # FastAPI & Celery Asynchronous Backend
│   ├── app/
│   │   ├── main.py                         # FastAPI instance, CORS setup, router registration
│   │   ├── database.py                     # PostgreSQL & PostGIS database session manager
│   │   ├── worker.py                       # Celery background broker (invokes AI pipeline)
│   │   ├── schemas/
│   │   │   └── land_record.py              # Pydantic V2 request/response validation models
│   │   └── routers/
│   │       ├── ingest.py                   # POST /api/v1/ingest/upload (multipart form-data)
│   │       ├── records.py                  # GET /api/v1/records/{id} & PUT verify
│   │       ├── dashboard.py                # GET /api/v1/dashboard/stats
│   │       └── gis.py                      # GET /api/v1/gis/parcels (GeoJSON spatial output)
│   └── requirements.txt
│
└── ai_pipeline/                            # 6-Model AI Pipeline Package
    ├── preprocessor.py                     # OpenCV deskew, binarization, & noise removal
    ├── model1_yolo_layout.py               # Model 1: YOLOv8 Layout Analysis & Segmentation
    ├── model2_language_id.py               # Model 2: Script & Language Identification Routing
    ├── model3_paddle_ocr.py                # Model 3: PaddleOCR Printed Text Extraction
    ├── model4_trocr_htr.py                 # Model 4: TRoCR Regional Handwriting Recognition
    ├── model5_layoutlm_ner.py              # Model 5: LayoutLM Named Entity Recognition (NER)
    ├── model6_schema_mapper.py             # Model 6: Key-Value Structured Schema Mapper
    └── run_pipeline.py                     # Unified entry point
```

---

## 🚀 Getting Started

### Frontend Development
```bash
# Install dependencies
npm install

# Run local development server
npm run dev

# Build production bundle
npm run build
```

---

## 🔗 Connected Endpoints Summary

| Frontend Page | Backend Endpoint | Method | Functionality |
| :--- | :--- | :---: | :--- |
| [`Upload.tsx`](file:///c:/Users/parup/.gemini/antigravity-ide/scratch/land-record-system/src/pages/Upload.tsx) | `/api/v1/ingest/upload` | `POST` | Ingests PDF/Images, computes SHA-256 hash, queues Celery job |
| [`Verification.tsx`](file:///c:/Users/parup/.gemini/antigravity-ide/scratch/land-record-system/src/pages/Verification.tsx) | `/api/v1/records/{id}` | `GET` | Fetches extracted fields with bounding box coordinates & cross-DB checks |
| [`Verification.tsx`](file:///c:/Users/parup/.gemini/antigravity-ide/scratch/land-record-system/src/pages/Verification.tsx) | `/api/v1/records/{id}/verify` | `PUT` | Submits human reviewer corrections & applies digital signature |
| [`Verification.tsx`](file:///c:/Users/parup/.gemini/antigravity-ide/scratch/land-record-system/src/pages/Verification.tsx) | `/api/v1/active-learning/feedback`| `POST` | Feeds corrections into Model v2.5 retraining buffer |
| [`Dashboard.tsx`](file:///c:/Users/parup/.gemini/antigravity-ide/scratch/land-record-system/src/pages/Dashboard.tsx) | `/api/v1/dashboard/stats` | `GET` | Fetches volume counts, accuracy metrics, error stats & state progress |
| [`GISMap.tsx`](file:///c:/Users/parup/.gemini/antigravity-ide/scratch/land-record-system/src/pages/GISMap.tsx) | `/api/v1/gis/parcels` | `GET` | Fetches PostGIS cadastral polygon boundaries in GeoJSON format |
