export interface BrandColor {
  name: string;
  hex: string;
  rgb: string;
  hsl: string;
  reason?: string;
  luminance?: number;
  text_color?: string;
}

export interface BrandPalette {
  primary: BrandColor;
  secondary: BrandColor;
  accent: BrandColor;
}

export interface CandidateColor {
  hex: string;
  percentage: number;
}

export interface AnalyzeLogoResponse {
  success: boolean;
  id?: number | null;
  filename?: string;
  created_at?: string | null;
  colors?: BrandPalette;
  meta?: {
    dimensions: { width: number; height: number };
    candidate_count: number;
    candidates: CandidateColor[];
  };
  error?: {
    code: string;
    message: string;
  };
}

export interface DatabaseStatus {
  connected: boolean;
  type: string;
  host: string;
  port: number;
  database: string;
  error?: string | null;
}

export interface ApiHealthResponse {
  status: string;
  llm_configured: boolean;
  model: string | null;
  database?: DatabaseStatus;
}

export interface PaletteHistorySummary {
  id: number;
  filename: string;
  created_at: string | null;
  primary: { name: string; hex: string };
  secondary: { name: string; hex: string };
  accent: { name: string; hex: string };
}

export interface HistoryApiResponse {
  success: boolean;
  history: PaletteHistorySummary[];
}

export type ProgressStepId = 'upload' | 'preprocess' | 'clustering' | 'llm' | 'complete';

export interface ProgressStep {
  id: ProgressStepId;
  label: string;
  status: 'pending' | 'active' | 'done';
}
