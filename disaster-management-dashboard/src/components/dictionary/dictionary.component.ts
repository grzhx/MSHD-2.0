
import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

type DictionaryDomain = 'source' | 'carrier' | 'disaster';

@Component({
  selector: 'app-dictionary',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dictionary.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DictionaryComponent {
  private apiService = inject(ApiService);
  dictionaryData = signal<any>(null);
  activeTab = signal<DictionaryDomain>('source');
  
  constructor() {
    this.apiService.getDictionaryData().subscribe(data => {
      this.dictionaryData.set(data);
    });
  }

  setTab(tab: DictionaryDomain) {
    this.activeTab.set(tab);
  }
}
