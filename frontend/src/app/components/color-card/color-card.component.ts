import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ColorItem } from '../../models/palette.model';
import { ColorExtractorService } from '../../services/color-extractor.service';

@Component({
  selector: 'app-color-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './color-card.component.html',
  styleUrls: ['./color-card.component.scss']
})
export class ColorCardComponent {
  @Input({ required: true }) color!: ColorItem;
  @Input({ required: true }) roleTitle: string = 'PRIMARY';
  @Input() roleType: 'primary' | 'secondary' | 'accent' = 'primary';

  copiedField: string | null = null;

  constructor(public colorService: ColorExtractorService) {}

  copyValue(value: string, fieldName: string) {
    this.colorService.copyToClipboard(value, `${this.roleTitle} ${fieldName}`);
    this.copiedField = fieldName;
    setTimeout(() => {
      if (this.copiedField === fieldName) {
        this.copiedField = null;
      }
    }, 1800);
  }

  getBadgeClass(): string {
    switch (this.roleType) {
      case 'primary': return 'badge-primary';
      case 'secondary': return 'badge-secondary';
      case 'accent': return 'badge-accent';
      default: return '';
    }
  }
}
