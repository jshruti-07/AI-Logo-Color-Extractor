import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExtractedPaletteResponse } from '../../models/palette.model';
import { ColorExtractorService } from '../../services/color-extractor.service';

@Component({
  selector: 'app-export-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './export-modal.component.html',
  styleUrls: ['./export-modal.component.scss']
})
export class ExportModalComponent {
  @Input({ required: true }) palette!: ExtractedPaletteResponse;
  @Output() close = new EventEmitter<void>();

  activeTab: 'css' | 'json' | 'scss' | 'tailwind' = 'css';
  copiedTab: string | null = null;

  constructor(public colorService: ColorExtractorService) {}

  get activeContent(): string {
    switch (this.activeTab) {
      case 'css':
        return this.colorService.generateCssExport(this.palette);
      case 'json':
        return this.colorService.generateJsonExport(this.palette);
      case 'scss':
        return this.colorService.generateScssExport(this.palette);
      case 'tailwind':
        return this.colorService.generateTailwindExport(this.palette);
      default:
        return '';
    }
  }

  copyActiveContent() {
    const text = this.activeContent;
    this.colorService.copyToClipboard(text, `${this.activeTab.toUpperCase()} Snippet`);
    this.copiedTab = this.activeTab;
    setTimeout(() => {
      if (this.copiedTab === this.activeTab) {
        this.copiedTab = null;
      }
    }, 1800);
  }

  downloadActiveContent() {
    const content = this.activeContent;
    const baseName = 'brand-palette';
    switch (this.activeTab) {
      case 'css':
        this.colorService.downloadFile(content, `${baseName}.css`, 'text/css');
        break;
      case 'json':
        this.colorService.downloadFile(content, `${baseName}.json`, 'application/json');
        break;
      case 'scss':
        this.colorService.downloadFile(content, `_${baseName}.scss`, 'text/x-scss');
        break;
      case 'tailwind':
        this.colorService.downloadFile(content, `tailwind.colors.js`, 'application/javascript');
        break;
    }
    this.colorService.showToast(`Downloaded ${this.activeTab.toUpperCase()} palette file!`, 'success');
  }

  downloadSvgPalette() {
    const p = this.palette;
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="600" height="240" viewBox="0 0 600 240" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="600" height="240" rx="16" fill="#0B0F19"/>
  <text x="30" y="40" fill="#F8FAFC" font-family="sans-serif" font-size="16" font-weight="bold">AI Logo Color Extractor - Brand Palette</text>
  
  <!-- Primary -->
  <rect x="30" y="60" width="160" height="110" rx="10" fill="${p.primary.hex}"/>
  <text x="42" y="195" fill="#F8FAFC" font-family="sans-serif" font-size="13" font-weight="bold">${p.primary.name}</text>
  <text x="42" y="215" fill="#94A3B8" font-family="monospace" font-size="12">PRIMARY: ${p.primary.hex}</text>
  
  <!-- Secondary -->
  <rect x="220" y="60" width="160" height="110" rx="10" fill="${p.secondary.hex}"/>
  <text x="232" y="195" fill="#F8FAFC" font-family="sans-serif" font-size="13" font-weight="bold">${p.secondary.name}</text>
  <text x="232" y="215" fill="#94A3B8" font-family="monospace" font-size="12">SECONDARY: ${p.secondary.hex}</text>
  
  <!-- Accent -->
  <rect x="410" y="60" width="160" height="110" rx="10" fill="${p.accent.hex}"/>
  <text x="422" y="195" fill="#F8FAFC" font-family="sans-serif" font-size="13" font-weight="bold">${p.accent.name}</text>
  <text x="422" y="215" fill="#94A3B8" font-family="monospace" font-size="12">ACCENT: ${p.accent.hex}</text>
</svg>`;
    this.colorService.downloadFile(svg, 'brand-palette.svg', 'image/svg+xml');
    this.colorService.showToast('Downloaded SVG Swatch Card!', 'success');
  }

  onBackdropClick(event: MouseEvent) {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.close.emit();
    }
  }
}
