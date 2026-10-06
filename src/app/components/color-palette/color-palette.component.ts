import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BrandPalette, BrandColor } from '../../models/color.model';

@Component({
  selector: 'app-color-palette',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './color-palette.component.html',
  styleUrls: ['./color-palette.component.scss']
})
export class ColorPaletteComponent {
  @Input() palette!: BrandPalette;
  @Input() logoPreviewUrl: string | null = null;
  @Output() reset = new EventEmitter<void>();

  copiedMessage: string | null = null;
  copiedTimeout: any = null;

  get roleList(): Array<{ role: 'primary' | 'secondary' | 'accent'; title: string; color: BrandColor }> {
    if (!this.palette) return [];
    return [
      { role: 'primary', title: 'PRIMARY', color: this.palette.primary },
      { role: 'secondary', title: 'SECONDARY', color: this.palette.secondary },
      { role: 'accent', title: 'ACCENT', color: this.palette.accent },
    ];
  }

  getTextColor(hex: string): string {
    if (!hex) return '#FFFFFF';
    const cleanHex = hex.replace('#', '');
    if (cleanHex.length !== 6) return '#FFFFFF';
    const r = parseInt(cleanHex.substring(0, 2), 16);
    const g = parseInt(cleanHex.substring(2, 4), 16);
    const b = parseInt(cleanHex.substring(4, 6), 16);

    // WCAG relative luminance calculation
    const pivot = (v: number) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    const lum = 0.2126 * pivot(r) + 0.7152 * pivot(g) + 0.0722 * pivot(b);

    return lum < 0.5 ? '#FFFFFF' : '#0F172A';
  }

  copyValue(val: string, label: string = 'Copied!'): void {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(val).then(() => {
        this.triggerCopiedToast(label);
      }).catch(() => {
        this.fallbackCopy(val, label);
      });
    } else {
      this.fallbackCopy(val, label);
    }
  }

  copyAllColors(): void {
    if (!this.palette) return;
    const content = 
`Primary: ${this.palette.primary.hex}
Secondary: ${this.palette.secondary.hex}
Accent: ${this.palette.accent.hex}`;
    this.copyValue(content, 'Copied all colors!');
  }

  exportJson(): void {
    if (!this.palette) return;
    const payload = {
      primary: this.palette.primary.hex,
      secondary: this.palette.secondary.hex,
      accent: this.palette.accent.hex
    };
    const jsonStr = JSON.stringify(payload, null, 2);
    this.triggerDownload(jsonStr, 'brand-palette.json', 'application/json');
    this.triggerCopiedToast('Downloaded JSON palette!');
  }

  exportCss(): void {
    if (!this.palette) return;
    const cssContent = 
`:root {
  --primary: ${this.palette.primary.hex};
  --secondary: ${this.palette.secondary.hex};
  --accent: ${this.palette.accent.hex};
}`;
    this.triggerDownload(cssContent, 'brand-palette.css', 'text/css');
    this.triggerCopiedToast('Downloaded CSS palette!');
  }

  private triggerDownload(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }

  private fallbackCopy(text: string, label: string): void {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      this.triggerCopiedToast(label);
    } catch {
      // Ignored
    }
    document.body.removeChild(textArea);
  }

  private triggerCopiedToast(msg: string): void {
    this.copiedMessage = msg;
    if (this.copiedTimeout) {
      clearTimeout(this.copiedTimeout);
    }
    this.copiedTimeout = setTimeout(() => {
      this.copiedMessage = null;
    }, 2200);
  }
}
