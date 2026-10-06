/**
 * Data models for AI Logo Color Extractor.
 */

export interface RGBValues {
  r: number;
  g: number;
  b: number;
}

export interface HSLValues {
  h: number;
  s: number;
  l: number;
}

export interface ColorAccessibility {
  luminance: number;
  contrast_with_white: number;
  contrast_with_black: number;
  preferred_text_color: string;
  is_dark: boolean;
}

export interface ColorItem {
  name: string;
  hex: string;
  rgb: string;
  hsl: string;
  rgb_values?: RGBValues;
  hsl_values?: HSLValues;
  percentage?: number;
  accessibility?: ColorAccessibility;
  role?: 'primary' | 'secondary' | 'accent';
  reasoning?: string;
}

export interface CandidateColor {
  id: number;
  hex: string;
  name: string;
  rgb: string;
  hsl: string;
  percentage: number;
  is_selected_role?: 'primary' | 'secondary' | 'accent' | null;
}

export interface ImageMetadata {
  filename: string;
  format: string;
  width: number;
  height: number;
  has_alpha: boolean;
  filtered_transparent_percentage: number;
  total_pixels_analyzed: number;
}

export interface ExtractedPaletteResponse {
  primary: ColorItem;
  secondary: ColorItem;
  accent: ColorItem;
  candidates: CandidateColor[];
  total_candidates: number;
  ai_selection_source: 'openai' | 'heuristic_fallback' | string;
  ai_summary?: string;
  image_metadata?: ImageMetadata;
}

export interface ToastMessage {
  id: string;
  text: string;
  type: 'success' | 'error' | 'info';
}

export interface SampleLogo {
  id: string;
  name: string;
  category: string;
  description: string;
  svgContent: string;
}
