import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CandidateColor } from '../../models/palette.model';
import { ColorExtractorService } from '../../services/color-extractor.service';

@Component({
  selector: 'app-candidate-palette',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './candidate-palette.component.html',
  styleUrls: ['./candidate-palette.component.scss']
})
export class CandidatePaletteComponent {
  @Input({ required: true }) candidates: CandidateColor[] = [];
  @Input() totalCandidates: number = 0;

  constructor(public colorService: ColorExtractorService) {}

  copyCandidateHex(candidate: CandidateColor) {
    this.colorService.copyToClipboard(candidate.hex, `${candidate.name} (${candidate.hex})`);
  }
}
