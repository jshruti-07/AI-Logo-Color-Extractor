import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProgressStep } from '../../models/color.model';

@Component({
  selector: 'app-logo-preview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './logo-preview.component.html',
  styleUrls: ['./logo-preview.component.scss']
})
export class LogoPreviewComponent {
  @Input() file: File | null = null;
  @Input() previewUrl: string | null = null;
  @Input() isAnalyzing = false;
  @Input() steps: ProgressStep[] = [];

  @Output() changeLogo = new EventEmitter<void>();
  @Output() analyzeLogo = new EventEmitter<void>();

  get formattedFileSize(): string {
    if (!this.file) return '';
    const bytes = this.file.size;
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  get fileExtension(): string {
    if (!this.file) return '';
    return (this.file.name.split('.').pop() || '').toUpperCase();
  }

  onChangeClicked(): void {
    if (!this.isAnalyzing) {
      this.changeLogo.emit();
    }
  }

  onAnalyzeClicked(): void {
    if (!this.isAnalyzing) {
      this.analyzeLogo.emit();
    }
  }
}
