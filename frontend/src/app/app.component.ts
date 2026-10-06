import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from './components/header/header.component';
import { UploadZoneComponent } from './components/upload-zone/upload-zone.component';
import { ColorCardComponent } from './components/color-card/color-card.component';
import { CandidatePaletteComponent } from './components/candidate-palette/candidate-palette.component';
import { LivePreviewComponent } from './components/live-preview/live-preview.component';
import { ExportModalComponent } from './components/export-modal/export-modal.component';
import { ColorExtractorService } from './services/color-extractor.service';
import { ExtractedPaletteResponse } from './models/palette.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    UploadZoneComponent,
    ColorCardComponent,
    CandidatePaletteComponent,
    LivePreviewComponent,
    ExportModalComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  isBackendHealthy: boolean = true;
  isOpenAiConnected: boolean = false;

  // Workflow states
  currentStep: 'upload' | 'analyzing' | 'result' | 'error' = 'upload';
  selectedFile: File | null = null;
  previewImageUrl: string | null = null;
  analysisError: string | null = null;

  // Analysis result
  paletteResult: ExtractedPaletteResponse | null = null;
  isExportModalOpen: boolean = false;

  constructor(public colorService: ColorExtractorService) {}

  ngOnInit() {
    this.checkHealth();
  }

  checkHealth() {
    this.colorService.checkBackendHealth().subscribe({
      next: (res) => {
        this.isBackendHealthy = true;
        this.isOpenAiConnected = res.openai_configured;
      },
      error: () => {
        this.isBackendHealthy = false;
      }
    });
  }

  onFileSelected(file: File) {
    this.selectedFile = file;
    this.analysisError = null;

    // Create local object URL for preview
    if (this.previewImageUrl) {
      URL.revokeObjectURL(this.previewImageUrl);
    }
    this.previewImageUrl = URL.createObjectURL(file);

    this.startAnalysis(file);
  }

  startAnalysis(file: File) {
    this.currentStep = 'analyzing';

    this.colorService.analyzeLogo(file).subscribe({
      next: (response) => {
        this.paletteResult = response;
        this.currentStep = 'result';
        this.colorService.showToast('Brand colors successfully extracted!', 'success');
      },
      error: (err: Error) => {
        this.analysisError = err.message || 'Failed to extract colors from image.';
        this.currentStep = 'error';
        this.colorService.showToast(this.analysisError, 'error');
      }
    });
  }

  retryUpload() {
    if (this.selectedFile) {
      this.startAnalysis(this.selectedFile);
    } else {
      this.resetAnalysis();
    }
  }

  resetAnalysis() {
    this.currentStep = 'upload';
    this.paletteResult = null;
    this.analysisError = null;
    this.selectedFile = null;
    if (this.previewImageUrl) {
      URL.revokeObjectURL(this.previewImageUrl);
      this.previewImageUrl = null;
    }
  }

  copyAllColors() {
    if (!this.paletteResult) return;
    const p = this.paletteResult;
    const text = `PRIMARY: ${p.primary.hex} (${p.primary.name})
SECONDARY: ${p.secondary.hex} (${p.secondary.name})
ACCENT: ${p.accent.hex} (${p.accent.name})`;

    this.colorService.copyToClipboard(text, 'All 3 Brand Colors');
  }

  openExportModal() {
    this.isExportModalOpen = true;
  }

  closeExportModal() {
    this.isExportModalOpen = false;
  }
}
