import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ColorItem } from '../../models/palette.model';

@Component({
  selector: 'app-live-preview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './live-preview.component.html',
  styleUrls: ['./live-preview.component.scss']
})
export class LivePreviewComponent {
  @Input({ required: true }) primary!: ColorItem;
  @Input({ required: true }) secondary!: ColorItem;
  @Input({ required: true }) accent!: ColorItem;

  previewTheme: 'dark' | 'light' = 'dark';

  toggleTheme() {
    this.previewTheme = this.previewTheme === 'dark' ? 'light' : 'dark';
  }
}
