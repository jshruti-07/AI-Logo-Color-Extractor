# AI Logo Color Extractor

A full-stack web application that analyzes genuine colors from uploaded logo images (JPG/PNG) using computer vision and clustering algorithms, generates candidate color palettes, and leverages an OpenAI LLM to classify the three definitive brand colors: **Primary**, **Secondary**, and **Accent**.

---

## Architecture & Color Pipeline

Unlike naive solutions that ask an LLM to guess colors or hallucinate HEX codes, this system strictly enforces a deterministic computer-vision pipeline:

```
[ Uploaded Logo Image ]
           │
           ▼
[ Image Preprocessing & Transparency Filter ] (Pillow & NumPy)
   • Strips transparent pixels (ignores them instead of treating as white/black)
   • Resizes maintaining aspect ratio
           │
           ▼
[ Pixel Clustering ] (scikit-learn K-Means)
   • Clusters visible pixels into 10–16 representative centroids
   • Calculates exact pixel frequencies and relative weights
           │
           ▼
[ Perceptual LAB Deduplication ] (Delta E CIE L*a*b*)
   • Eliminates visually indistinguishable neighbor colors
   • Merges near-duplicate frequencies into the representative centroid
           │
           ▼
[ OpenAI LLM Classification ] (Structured JSON)
   • Evaluates candidates based on brand visual identity and contrast
   • Strictly selects ONLY from extracted candidate colors (zero hallucinations)
   • Classifies Primary, Secondary, and Accent with rationale
           │
           ▼
[ Mathematical Color Conversion ] (Python Backend)
   • Computes HEX, RGB, HSL, human-readable name & WCAG contrast
           │
           ▼
[ MySQL Persistence & Saved History ] (SQLAlchemy + PyMySQL)
   • Stores extraction details, brand colors, candidate breakdown & metadata
           │
           ▼
[ Angular Frontend Display & Export ]
   • Interactive cards with dynamic contrast, copy actions, history drawer & JSON/CSS downloads
```

---

## Key Features

- **Accurate Color Extraction**: Powered by K-Means clustering over visible, non-transparent pixels.
- **Perceptual Deduplication**: Delta E CIE L\*a\*b\* metric eliminates redundant color swatches.
- **Intelligent Brand Roles**: OpenAI classifies Primary, Secondary, and Accent roles with explanations.
- **Hallucination Prevention**: Strict server-side validation rejects any color not present in the candidate list, with automatic retries and deterministic fallback.
- **Multiple Color Formats**: Real-time calculated HEX, RGB (`R, G, B`), and HSL (`H°, S%, L%`) values.
- **Dynamic Text Contrast**: Automatic light/dark foreground calculation based on W3C relative luminance.
- **MySQL Database Persistence**: Auto-saves every analysis and provides an interactive history drawer in the frontend.
- **Copy & Export Utilities**:
  - Individual format copy (`[ Copy HEX ]`, `[ Copy RGB ]`, `[ Copy HSL ]`)
  - `[ Copy All Colors ]` for instant palette clipboard export
  - Direct browser downloads for **JSON** and **CSS** custom properties
- **Progress Stepper**: Real-time visual feedback tracking each stage of the analysis pipeline.
- **Security-First**: The `OPENAI_API_KEY` stays exclusively on the server and is never exposed to the client.

---

## Project Structure

```text
Color Extractor/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── logo-upload/           # Drag & drop upload zone & file picker
│   │   │   │   ├── logo-preview/          # Logo preview, badges & progress stepper
│   │   │   │   └── color-palette/         # 3 brand cards, copy buttons & export
│   │   │   ├── models/
│   │   │   │   └── color.model.ts         # TypeScript interfaces & types
│   │   │   ├── services/
│   │   │   │   └── color-api.service.ts   # Angular HttpClient service
│   │   │   ├── app.component.ts           # Root component state orchestration
│   │   │   ├── app.component.html
│   │   │   └── app.component.scss
│   │   ├── index.html                     # Typography (Plus Jakarta Sans & JetBrains Mono)
│   │   └── styles.scss                    # Global theme styling
│   ├── proxy.conf.json                    # Angular dev proxy forwarding /api to port 8000
│   ├── package.json
│   └── angular.json
│
├── backend/
│   ├── main.py                            # FastAPI application with CORS & routes
│   ├── database.py                        # SQLAlchemy & MySQL connection pooling
│   ├── requirements.txt                   # Backend Python dependencies
│   ├── .env.example                       # Environment template
│   ├── .env                               # Local secrets (OPENAI_API_KEY, MySQL)
│   ├── models/
│   │   └── palette.py                     # SQLAlchemy database model
│   ├── services/
│   │   ├── image_processor.py             # Pillow loading, resizing & alpha masking
│   │   ├── color_extractor.py             # K-Means clustering & candidate generation
│   │   ├── color_converter.py             # HEX, RGB, HSL & contrast calculations
│   │   ├── llm_analyzer.py                # OpenAI structured prompt & validation
│   │   └── palette_repository.py          # MySQL database repository operations
│   ├── utils/
│   │   └── color_utils.py                 # Delta E, color naming DB & conversion math
│   └── tests/
│       ├── test_image_processor.py        # PNG/JPG/Transparency/Corrupt tests
│       ├── test_color_extractor.py        # Clustering & deduplication tests
│       ├── test_color_converter.py        # HSL, RGB, contrast tests
│       ├── test_database.py               # Database CRUD tests
│       └── test_api.py                    # FastAPI route & validation tests
│
└── README.md
```

---

## Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: v18 or higher (tested on Node v22)
- **npm**: v9 or higher (tested on npm v10)
- **MySQL**: 8.0 or higher
- **OpenAI API Key**: (Required for live LLM classification)

---

## Installation & Setup

### 1. Backend Setup

Open a terminal in the root directory:

```bash
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell / Command Prompt):
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment Variables

Create your `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `backend/.env` and configure your settings:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
PORT=8000
HOST=0.0.0.0

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=color_extractor_db
```

The database (`color_extractor_db`) and tables (`palettes`) will be automatically created upon FastAPI startup when MySQL is running.

#### Run Backend Server

```bash
# From within the backend directory:
uvicorn main:app --reload --port 8000
```

The backend API will be available at: `http://localhost:8000`  
Interactive Swagger docs: `http://localhost:8000/docs`

---

### 2. Frontend Setup

Open another terminal:

```bash
cd frontend

# Install npm dependencies
npm install

# Start the Angular development server
npm start
```

The Angular application will launch at: `http://localhost:4200`

---

## Running Automated Tests

Run the backend test suite:

```bash
cd backend
venv\Scripts\python -m pytest tests -v
```

This validates:
- Valid PNG and JPG processing
- Transparent PNG alpha filtering (transparent pixels not treated as brand colors)
- Rejection of invalid extensions, MIME types, and corrupt files
- K-Means candidate color extraction and frequencies
- Near-duplicate filtering using perceptual Delta E
- Accurate HEX, RGB, and HSL conversions
- Luminance-based readable foreground text selection
- MySQL repository CRUD operations
- API error handling and health endpoint responses
