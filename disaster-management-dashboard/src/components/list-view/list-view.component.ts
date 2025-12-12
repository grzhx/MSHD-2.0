
import { Component, ChangeDetectionStrategy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, DisasterRecord } from '../../services/api.service';

@Component({
  selector: 'app-list-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './list-view.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListViewComponent {
  private apiService = inject(ApiService);
  
  allRecords = signal<DisasterRecord[]>([]);
  searchQuery = signal('');
  selectedRecord = signal<DisasterRecord | null>(null);

  filteredRecords = computed(() => {
    const query = this.searchQuery().toLowerCase();
    if (!query) {
      return this.allRecords();
    }
    return this.allRecords().filter(record => 
      record.id.toLowerCase().includes(query) ||
      record.location.toLowerCase().includes(query) ||
      record.disasterType.toLowerCase().includes(query) ||
      record.source.toLowerCase().includes(query)
    );
  });

  constructor() {
    this.apiService.getDisasterRecords().subscribe(data => {
      this.allRecords.set(data);
    });
  }

  onSearch(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchQuery.set(input.value);
  }

  selectRecord(record: DisasterRecord): void {
    this.selectedRecord.set(record);
  }

  closeDetail(): void {
    this.selectedRecord.set(null);
  }

  exportToCSV(): void {
    const records = this.filteredRecords();
    if (records.length === 0) return;
    
    const headers = ['ID', '时间', '地点', '灾害类型', '来源', '载体', '关键指标值', '简要损失'];
    const rows = records.map(r => [r.id, r.time, r.location, r.disasterType, r.source, r.carrier, r.intensity, r.loss].join(','));
    
    const csvContent = "data:text/csv;charset=utf-8," + headers.join(',') + "\n" + rows.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "disaster_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
