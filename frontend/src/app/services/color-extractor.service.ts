import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { ExtractedPaletteResponse, ToastMessage, SampleLogo } from '../models/palette.model';

@Injectable({
  providedIn: 'root'
})
export class ColorExtractorService {
  private readonly apiUrl = 'http://localhost:8000/api';

  // Reactive state signals
  readonly toasts = signal<ToastMessage[]>([]);

  // Built-in sample logos for immediate 1-click testing
  readonly sampleLogos: SampleLogo[] = [
    {
      id: 'tech-nexus',
      name: 'Nexus Cloud',
      category: 'Tech & SaaS',
      description: 'Modern indigo, cyan and electric blue gradient tech logo',
      svgContent: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300">
        <defs>
          <linearGradient id="nexusGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#4F46E5" />
            <stop offset="50%" stop-color="#06B6D4" />
            <stop offset="100%" stop-color="#3B82F6" />
          </linearGradient>
          <filter id="nexusGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        <circle cx="150" cy="150" r="110" fill="none" stroke="url(#nexusGrad)" stroke-width="18" stroke-dasharray="380 40" stroke-linecap="round" filter="url(#nexusGlow)"/>
        <polygon points="150,85 195,165 105,165" fill="#4F46E5" opacity="0.95"/>
        <polygon points="150,215 105,135 195,135" fill="#06B6D4" opacity="0.85"/>
        <circle cx="150" cy="150" r="24" fill="#F43F5E" />
      </svg>`
    },
    {
      id: 'aurora-luxury',
      name: 'Aurora Jewels',
      category: 'Luxury & Fashion',
      description: 'Sophisticated deep emerald, warm champagne gold, and burgundy',
      svgContent: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300">
        <rect width="300" height="300" fill="#0F172A"/>
        <path d="M150 40 L230 150 L150 260 L70 150 Z" fill="#064E3B" stroke="#F59E0B" stroke-width="6"/>
        <path d="M150 75 L205 150 L150 225 L95 150 Z" fill="#991B1B" opacity="0.9"/>
        <circle cx="150" cy="150" r="32" fill="#FBBF24" />
      </svg>`
    },
    {
      id: 'solar-energy',
      name: 'Solaris Energy',
      category: 'Clean Energy',
      description: 'Vibrant sunset orange, sunflower amber, and deep forest green',
      svgContent: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300">
        <circle cx="150" cy="150" r="105" fill="#EA580C"/>
        <path d="M150 30 L165 105 L135 105 Z" fill="#FDE047"/>
        <path d="M150 270 L165 195 L135 195 Z" fill="#FDE047"/>
        <path d="M30 150 L105 165 L105 135 Z" fill="#FDE047"/>
        <path d="M270 150 L195 165 L195 135 Z" fill="#FDE047"/>
        <path d="M110 190 Q150 90 190 190 Z" fill="#15803D"/>
      </svg>`
    },
    {
      id: 'cyber-pulse',
      name: 'CyberPulse AI',
      category: 'Gaming & Cyber',
      description: 'Neon electric purple, hot magenta, and dark obsidian navy',
      svgContent: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300">
        <rect width="300" height="300" fill="#050814"/>
        <path d="M60 210 L120 70 L180 180 L210 120 L240 210" fill="none" stroke="#8B5CF6" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="120" cy="70" r="18" fill="#EC4899"/>
        <circle cx="180" cy="180" r="14" fill="#06B6D4"/>
        <circle cx="210" cy="120" r="12" fill="#F43F5E"/>
      </svg>`
    }
  ];

  constructor(private http: HttpClient) {}

  /**
   * Uploads logo image file to FastAPI backend.
   */
  analyzeLogo(file: File): Observable<ExtractedPaletteResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post<ExtractedPaletteResponse>(`${this.apiUrl}/analyze-logo`, formData).pipe(
      catchError((error: HttpErrorResponse) => {
        let errorMsg = 'An unexpected server error occurred while analyzing the logo.';
        if (error.error && error.error.message) {
          errorMsg = error.error.message;
        } else if (error.status === 0) {
          errorMsg = 'Cannot connect to the FastAPI backend. Please ensure the backend server is running on http://localhost:8000.';
        } else if (error.status === 413) {
          errorMsg = 'The uploaded file is too large. Please upload an image under 10MB.';
        }
        return throwError(() => new Error(errorMsg));
      })
    );
  }

  /**
   * Health check to check connection to backend.
   */
  checkBackendHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  /**
   * Converts SVG sample string to a File object for seamless uploading.
   */
  convertSvgToFile(svgString: string, filename: string): File {
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    return new File([blob], filename, { type: 'image/svg+xml' });
  }

  /**
   * Generate CSS Variables export string.
   */
  generateCssExport(palette: ExtractedPaletteResponse): string {
    return `:root {
  /* AI Extracted Brand Palette */
  --primary: ${palette.primary.hex};
  --primary-rgb: ${palette.primary.rgb_values?.r ?? 0}, ${palette.primary.rgb_values?.g ?? 0}, ${palette.primary.rgb_values?.b ?? 0};
  --primary-hsl: ${palette.primary.hsl_values?.h ?? 0}, ${palette.primary.hsl_values?.s ?? 0}%, ${palette.primary.hsl_values?.l ?? 0}%;

  --secondary: ${palette.secondary.hex};
  --secondary-rgb: ${palette.secondary.rgb_values?.r ?? 0}, ${palette.secondary.rgb_values?.g ?? 0}, ${palette.secondary.rgb_values?.b ?? 0};
  --secondary-hsl: ${palette.secondary.hsl_values?.h ?? 0}, ${palette.secondary.hsl_values?.s ?? 0}%, ${palette.secondary.hsl_values?.l ?? 0}%;

  --accent: ${palette.accent.hex};
  --accent-rgb: ${palette.accent.rgb_values?.r ?? 0}, ${palette.accent.rgb_values?.g ?? 0}, ${palette.accent.rgb_values?.b ?? 0};
  --accent-hsl: ${palette.accent.hsl_values?.h ?? 0}, ${palette.accent.hsl_values?.s ?? 0}%, ${palette.accent.hsl_values?.l ?? 0}%;
}`;
  }

  /**
   * Generate SCSS Variables export string.
   */
  generateScssExport(palette: ExtractedPaletteResponse): string {
    return `// AI Extracted Brand Palette (SCSS)
$color-primary: ${palette.primary.hex}; // ${palette.primary.name}
$color-secondary: ${palette.secondary.hex}; // ${palette.secondary.name}
$color-accent: ${palette.accent.hex}; // ${palette.accent.name}

$color-primary-rgb: (${palette.primary.rgb_values?.r ?? 0}, ${palette.primary.rgb_values?.g ?? 0}, ${palette.primary.rgb_values?.b ?? 0});
$color-secondary-rgb: (${palette.secondary.rgb_values?.r ?? 0}, ${palette.secondary.rgb_values?.g ?? 0}, ${palette.secondary.rgb_values?.b ?? 0});
$color-accent-rgb: (${palette.accent.rgb_values?.r ?? 0}, ${palette.accent.rgb_values?.g ?? 0}, ${palette.accent.rgb_values?.b ?? 0});
`;
  }

  /**
   * Generate Tailwind Config export string.
   */
  generateTailwindExport(palette: ExtractedPaletteResponse): string {
    return `/** @type {import('tailwindcss').Config} */
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '${palette.primary.hex}',   // ${palette.primary.name}
          secondary: '${palette.secondary.hex}', // ${palette.secondary.name}
          accent: '${palette.accent.hex}',       // ${palette.accent.name}
        }
      }
    }
  }
};`;
  }

  /**
   * Generate JSON export string.
   */
  generateJsonExport(palette: ExtractedPaletteResponse): string {
    const exportObj = {
      palette_name: "AI Logo Extracted Palette",
      extracted_at: new Date().toISOString(),
      primary: {
        name: palette.primary.name,
        hex: palette.primary.hex,
        rgb: palette.primary.rgb,
        hsl: palette.primary.hsl,
        percentage: `${palette.primary.percentage}%`,
        reasoning: palette.primary.reasoning
      },
      secondary: {
        name: palette.secondary.name,
        hex: palette.secondary.hex,
        rgb: palette.secondary.rgb,
        hsl: palette.secondary.hsl,
        percentage: `${palette.secondary.percentage}%`,
        reasoning: palette.secondary.reasoning
      },
      accent: {
        name: palette.accent.name,
        hex: palette.accent.hex,
        rgb: palette.accent.rgb,
        hsl: palette.accent.hsl,
        percentage: `${palette.accent.percentage}%`,
        reasoning: palette.accent.reasoning
      },
      candidates: palette.candidates.map(c => ({
        hex: c.hex,
        name: c.name,
        percentage: `${c.percentage}%`,
        selected_role: c.is_selected_role || 'none'
      })),
      ai_selection_source: palette.ai_selection_source,
      ai_summary: palette.ai_summary
    };

    return JSON.stringify(exportObj, null, 2);
  }

  /**
   * Trigger file download in browser.
   */
  downloadFile(content: string, filename: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Copies text to clipboard and emits toast.
   */
  async copyToClipboard(text: string, label: string = 'Color code') {
    try {
      await navigator.clipboard.writeText(text);
      this.showToast(`Copied ${label} (${text}) to clipboard!`, 'success');
    } catch (e) {
      // Fallback for older browsers or restricted contexts
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      this.showToast(`Copied ${label} to clipboard!`, 'success');
    }
  }

  /**
   * Displays temporary toast notification.
   */
  showToast(text: string, type: 'success' | 'error' | 'info' = 'info') {
    const id = Math.random().toString(36).substring(2, 9);
    const toast: ToastMessage = { id, text, type };
    this.toasts.update(current => [...current, toast]);

    setTimeout(() => {
      this.toasts.update(current => current.filter(t => t.id !== id));
    }, 3200);
  }
}
