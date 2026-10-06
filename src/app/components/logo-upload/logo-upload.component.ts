import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-logo-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './logo-upload.component.html',
  styleUrls: ['./logo-upload.component.scss']
})
export class LogoUploadComponent {
  @Output() fileSelected = new EventEmitter<File>();
  @Output() errorOccurred = new EventEmitter<string>();

  isDragging = false;
  readonly maxSizeBytes = 5 * 1024 * 1024; // 5 MB
  readonly allowedExtensions = ['.jpg', '.jpeg', '.png'];
  readonly allowedMimeTypes = ['image/jpeg', 'image/png', 'image/pjpeg', 'image/x-png'];

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      this.validateAndEmitFile(file);
    }
  }

  onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      this.validateAndEmitFile(file);
      // Reset input value so re-selecting the same file triggers change
      input.value = '';
    }
  }

  private validateAndEmitFile(file: File): void {
    // Validate file size
    if (file.size > this.maxSizeBytes) {
      this.errorOccurred.emit(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maximum allowed size is 5MB.`);
      return;
    }

    // Validate extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const isAllowedExt = this.allowedExtensions.includes(ext);
    const isAllowedMime = this.allowedMimeTypes.includes(file.type.toLowerCase()) || file.type === '';

    if (!isAllowedExt && !isAllowedMime) {
      this.errorOccurred.emit('Please upload a valid JPG or PNG logo.');
      return;
    }

    this.fileSelected.emit(file);
  }
}
