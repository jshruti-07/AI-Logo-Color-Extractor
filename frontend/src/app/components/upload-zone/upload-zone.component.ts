import { Component, EventEmitter, Output, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ColorExtractorService } from '../../services/color-extractor.service';
import { SampleLogo } from '../../models/palette.model';

@Component({
  selector: 'app-upload-zone',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload-zone.component.html',
  styleUrls: ['./upload-zone.component.scss']
})
export class UploadZoneComponent {
  @Input() isAnalyzing: boolean = false;
  @Output() fileSelected = new EventEmitter<File>();

  isDragging: boolean = false;
  uploadError: string | null = null;

  constructor(
    public colorService: ColorExtractorService,
    private sanitizer: DomSanitizer
  ) {}

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  onFileInputChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      this.handleFile(target.files[0]);
    }
  }

  handleFile(file: File) {
    this.uploadError = null;

    // Validate type
    const validExtensions = ['png', 'jpg', 'jpeg', 'webp', 'svg'];
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!validExtensions.includes(ext) && !file.type.startsWith('image/')) {
      this.uploadError = `Invalid file format "${file.name}". Please upload a PNG, JPG, or WEBP logo image.`;
      this.colorService.showToast(this.uploadError, 'error');
      return;
    }

    // Validate size (10MB limit)
    const maxBytes = 10 * 1024 * 1024;
    if (file.size > maxBytes) {
      this.uploadError = 'File size exceeds the 10MB limit. Please upload a smaller logo.';
      this.colorService.showToast(this.uploadError, 'error');
      return;
    }

    this.fileSelected.emit(file);
  }

  selectSampleLogo(sample: SampleLogo) {
    const file = this.colorService.convertSvgToFile(sample.svgContent, `${sample.id}.svg`);
    this.fileSelected.emit(file);
    this.colorService.showToast(`Selected "${sample.name}" sample logo!`, 'info');
  }

  sanitizeSvg(svg: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(svg);
  }
}
