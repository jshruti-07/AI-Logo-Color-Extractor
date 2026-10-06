import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LogoUploadComponent } from './components/logo-upload/logo-upload.component';
import { LogoPreviewComponent } from './components/logo-preview/logo-preview.component';
import { ColorPaletteComponent } from './components/color-palette/color-palette.component';
import { ColorApiService } from './services/color-api.service';
import { BrandPalette, ProgressStep, PaletteHistorySummary } from './models/color.model';

type AppState = 'upload' | 'preview' | 'result';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    LogoUploadComponent,
    LogoPreviewComponent,
    ColorPaletteComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  currentState: AppState = 'upload';
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  isAnalyzing = false;
  palette: BrandPalette | null = null;
  errorMessage: string | null = null;
  currentLoadedFilename: string | null = null;

  // Backend & MySQL status
  backendOnline = true;
  llmConfigured = true;
  mysqlConnected = false;
  mysqlDatabase = 'color_extractor_db';

  // MySQL History
  history: PaletteHistorySummary[] = [];
  showHistoryDrawer = false;
  isLoadingHistory = false;

  private healthCheckInterval: any = null;

  // Progress steps
  analysisSteps: ProgressStep[] = [
    { id: 'upload', label: 'Logo uploaded', status: 'pending' },
    { id: 'preprocess', label: 'Image processed', status: 'pending' },
    { id: 'clustering', label: 'Extracting colors', status: 'pending' },
    { id: 'llm', label: 'AI analyzing brand palette', status: 'pending' },
    { id: 'complete', label: 'Persisting to MySQL & preparing results', status: 'pending' },
  ];

  constructor(
    private colorApi: ColorApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.checkBackendHealth();
    this.loadHistory();

    // Auto-poll health status every 5 seconds so status badges update live
    this.healthCheckInterval = setInterval(() => {
      this.checkBackendHealth();
    }, 5000);
  }

  ngOnDestroy(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
  }

  checkBackendHealth(): void {
    this.colorApi.checkHealth().subscribe({
      next: (res) => {
        this.backendOnline = true;
        this.llmConfigured = res.llm_configured;
        if (res.database) {
          this.mysqlConnected = res.database.connected;
          this.mysqlDatabase = res.database.database;
        }
        this.cdr.detectChanges();
      },
      error: () => {
        this.backendOnline = false;
        this.mysqlConnected = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadHistory(): void {
    this.isLoadingHistory = true;
    this.colorApi.getHistory(30).subscribe({
      next: (res) => {
        this.isLoadingHistory = false;
        if (res && res.history) {
          this.history = res.history;
        }
        this.cdr.detectChanges();
      },
      error: () => {
        this.isLoadingHistory = false;
        this.cdr.detectChanges();
      }
    });
  }

  toggleHistoryDrawer(): void {
    this.showHistoryDrawer = !this.showHistoryDrawer;
    if (this.showHistoryDrawer) {
      this.loadHistory();
    }
    this.cdr.detectChanges();
  }

  closeHistoryDrawer(): void {
    this.showHistoryDrawer = false;
    this.cdr.detectChanges();
  }

  loadPaletteFromHistory(item: PaletteHistorySummary): void {
    this.isLoadingHistory = true;
    this.colorApi.getPaletteById(item.id).subscribe({
      next: (res) => {
        this.isLoadingHistory = false;
        if (res && res.colors) {
          this.palette = res.colors;
          this.currentLoadedFilename = res.filename || item.filename;
          this.currentState = 'result';
          this.showHistoryDrawer = false;
        }
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isLoadingHistory = false;
        this.errorMessage = err.message || 'Failed to load historical palette.';
        this.cdr.detectChanges();
      }
    });
  }

  deleteHistoryItem(id: number, event: MouseEvent): void {
    event.stopPropagation();
    this.colorApi.deletePalette(id).subscribe({
      next: () => {
        this.history = this.history.filter((h) => h.id !== id);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err.message || 'Failed to delete record.';
        this.cdr.detectChanges();
      }
    });
  }

  onFileSelected(file: File): void {
    this.errorMessage = null;
    this.selectedFile = file;
    this.currentLoadedFilename = file.name;

    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
    this.previewUrl = URL.createObjectURL(file);
    this.currentState = 'preview';
    this.cdr.detectChanges();
  }

  onUploadError(error: string): void {
    this.errorMessage = error;
    this.cdr.detectChanges();
  }

  changeLogo(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
      this.previewUrl = null;
    }
    this.selectedFile = null;
    this.palette = null;
    this.errorMessage = null;
    this.currentLoadedFilename = null;
    this.currentState = 'upload';
    this.cdr.detectChanges();
  }

  startAnalysis(): void {
    if (!this.selectedFile || this.isAnalyzing) return;

    this.isAnalyzing = true;
    this.errorMessage = null;
    this.initSteps();
    this.cdr.detectChanges();

    setTimeout(() => {
      this.setStepStatus('upload', 'done');
      this.setStepStatus('preprocess', 'active');
      this.cdr.detectChanges();
    }, 300);

    setTimeout(() => {
      this.setStepStatus('preprocess', 'done');
      this.setStepStatus('clustering', 'active');
      this.cdr.detectChanges();
    }, 700);

    setTimeout(() => {
      this.setStepStatus('clustering', 'done');
      this.setStepStatus('llm', 'active');
      this.cdr.detectChanges();
    }, 1200);

    this.colorApi.analyzeLogo(this.selectedFile).subscribe({
      next: (response) => {
        if (response.success && response.colors) {
          this.setStepStatus('llm', 'done');
          this.setStepStatus('complete', 'done');

          setTimeout(() => {
            this.palette = response.colors!;
            this.isAnalyzing = false;
            this.currentState = 'result';
            this.loadHistory();
            this.cdr.detectChanges();
          }, 500);
        } else {
          this.isAnalyzing = false;
          this.errorMessage = response.error?.message || 'Color extraction failed. Please try another logo.';
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        this.isAnalyzing = false;
        this.errorMessage = err.message || 'An error occurred during logo analysis. Please try again.';
        this.cdr.detectChanges();
      }
    });
  }

  dismissError(): void {
    this.errorMessage = null;
    this.cdr.detectChanges();
  }

  private initSteps(): void {
    this.analysisSteps.forEach((step, idx) => {
      step.status = idx === 0 ? 'active' : 'pending';
    });
  }

  private setStepStatus(
    id: ProgressStep['id'],
    status: ProgressStep['status']
  ): void {
    const step = this.analysisSteps.find((s) => s.id === id);
    if (step) {
      step.status = status;
    }
  }
}
