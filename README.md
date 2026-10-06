# 🎨 AI Logo Color Extractor

A modern, full-stack web application designed to extract dominant brand colors from any uploaded logo image (PNG, JPG, WEBP) using image processing & K-Means clustering, and then intelligently determine **Primary**, **Secondary**, and **Accent** semantic brand roles using OpenAI LLM intelligence.

---

## 🌟 Architecture & Key Features

### 🖼️ 1. True Image Processing First (Zero Guessing)
- **Transparent PNG Background Isolation**: Automatically filters out transparent and translucent alpha channels (`alpha < 30`) before clustering to prevent white or checkerboard canvas bias.
- **K-Means Color Clustering**: Clusters valid foreground pixels into **10 to 18 candidate colors** with dominance percentages.
- **Accurate Color Naming & Conversions**: Computes **HEX**, **RGB**, **HSL**, and nearest human-readable color names using standard CIELAB Delta-E perceptual matching.
- **Accessibility & Contrast Metrics**: Precomputes WCAG 2.1 relative luminance and text contrast against white and black.

### 🤖 2. Semantic LLM Role Selection
- Candidate colors and percentage weights are structured and passed to the **OpenAI LLM**.
- The LLM selects exactly three meaningful colors:
  - **PRIMARY**: The strongest color anchoring brand identity.
  - **SECONDARY**: Supporting foundation color for harmony and balance.
  - **ACCENT**: Distinctive, vibrant color ideal for CTAs, badges, and highlights.
- **Strict Guardrails**: The LLM is restricted to choosing strictly from the extracted candidates list.
- **Intelligent Fallback**: Gracefully falls back to a color-theory heuristic engine if the OpenAI API key is unset or unreachable.

### 💻 3. Angular Single-Page UI
- **Modern Glassmorphic Dark Design**: Custom SCSS design system with Google Fonts (Outfit & Inter), glowing borders, and micro-animations.
- **Drag-and-Drop Upload Zone**: Supports PNG, JPG, and WEBP with client-side file size and format validation.
- **Instant 1-Click Sample Logos**: Test immediately with pre-configured vector logos across tech, luxury, clean energy, and cyber industries.
- **Interactive Three Color Cards**: Prominent color swatches, human-friendly names, HEX, RGB, HSL with one-click copy buttons and "Copy HEX" main CTA.
- **Live Brand UI Simulator**: Preview extracted colors in a real-time web interface mockup with Light & Dark canvas toggles.
- **Candidate Spectrum Visualizer**: Inspect all 10-20 clustered candidate colors and their percentage distribution.
- **Multi-Format Palette Export**:
  - CSS Variables (`:root { --primary: ...; }`)
  - JSON Design Tokens
  - SCSS Variables (`$color-primary: ...;`)
  - Tailwind CSS configuration snippet
  - Standalone SVG Swatch Card download

---

## 🚀 Quick Start Guide

### 1. Backend Setup (Python + FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional but recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and optionally set your OPENAI_API_KEY
cp .env.example .env

# Run FastAPI Server
python run.py
# Server runs on: http://localhost:8000
# Interactive API Docs: http://localhost:8000/docs
```

### 2. Frontend Setup (Angular + TypeScript + SCSS)

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start development server
npm start
# App runs on: http://localhost:4200
```

---

## 📡 API Specification

### `POST /api/analyze-logo`
Accepts `multipart/form-data` with an image file (`image/png`, `image/jpeg`, `image/webp`).

#### Request
- `file`: Binary image file (up to 10MB)

#### Response (`200 OK`)
```json
{
  "primary": {
    "name": "Electric Indigo",
    "hex": "#4F46E5",
    "rgb": "rgb(79, 70, 229)",
    "hsl": "hsl(243, 75%, 59%)",
    "percentage": 42.5,
    "role": "primary",
    "reasoning": "Dominant anchor representing primary digital presence."
  },
  "secondary": {
    "name": "Cyan Blue",
    "hex": "#06B6D4",
    "rgb": "rgb(6, 182, 212)",
    "hsl": "hsl(189, 94%, 43%)",
    "percentage": 28.1,
    "role": "secondary",
    "reasoning": "Harmonious high-clarity accent."
  },
  "accent": {
    "name": "Hot Pink",
    "hex": "#F43F5E",
    "rgb": "rgb(244, 63, 94)",
    "hsl": "hsl(350, 89%, 60%)",
    "percentage": 14.8,
    "role": "accent",
    "reasoning": "High-contrast focal point for CTAs."
  },
  "candidates": [
    {
      "id": 1,
      "hex": "#4F46E5",
      "name": "Electric Indigo",
      "percentage": 42.5,
      "is_selected_role": "primary"
    }
  ],
  "total_candidates": 12,
  "ai_selection_source": "openai",
  "ai_summary": "Modern tech palette balancing deep indigo identity with cyan energy and vibrant rose call-to-actions.",
  "image_metadata": {
    "filename": "logo.png",
    "format": "PNG",
    "width": 800,
    "height": 800,
    "has_alpha": true,
    "filtered_transparent_percentage": 58.4,
    "total_pixels_analyzed": 266240
  }
}
```

---

## 🔒 Security Best Practices
- **Never expose OpenAI API keys**: Kept securely on backend in `.env`.
- **Validation**: Strict file magic bytes, MIME types, extension checking, and max file size limits.
- **Sanitization**: Safe SVG rendering and secure buffer handling via Pillow.

---

## 🧪 Testing Backend
Run the backend automated test suite:
```bash
cd backend
python test_backend.py
```
