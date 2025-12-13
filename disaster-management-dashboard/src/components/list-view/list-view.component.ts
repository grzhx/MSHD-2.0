
import { Component, ChangeDetectionStrategy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, DisasterRecord, ManualRecordInput } from '../../services/api.service';

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
  creating = signal(false);
  deletingId = signal<string | null>(null);
  toast = signal<string | null>(null);
  showManualForm = signal(false);
  newRecord = signal<ManualRecordInput>(this.createDefaultRecord());
  adminPassword = signal('');

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
    this.loadRecords();
  }

  private loadRecords() {
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

  toggleManualForm(): void {
    this.showManualForm.update((v) => !v);
    if (this.showManualForm()) {
      this.newRecord.set(this.createDefaultRecord());
    }
  }

  updateField<K extends keyof ManualRecordInput>(key: K, value: any): void {
    this.newRecord.update((prev) => ({
      ...prev,
      [key]: key === 'value' ? (value === '' ? null : Number(value)) : value
    }));
  }

  updateAdminPassword(value: string): void {
    this.adminPassword.set(value);
  }

  submitManual(): void {
    if (this.creating()) return;
    const payload = this.newRecord();
    const pwd = this.adminPassword().trim();

    if (!payload.lat_code || !payload.lng_code) {
      this.toast.set('请填写纬度/经度编码');
      return;
    }
    if (!payload.event_time) {
      this.toast.set('请填写事件时间');
      return;
    }
    if (!pwd) {
      this.toast.set('请输入管理员密码');
      return;
    }

    this.creating.set(true);
    this.toast.set(null);
    this.apiService.createManualRecord(payload, pwd).subscribe({
      next: (id) => {
        this.toast.set(`已写入数据：${id}`);
        this.loadRecords();
      },
      error: (err) => {
        console.error(err);
        this.toast.set("写入失败，请检查填写是否符合编码规则或后端服务状态");
        this.creating.set(false);
      },
      complete: () => this.creating.set(false),
    });
  }

  deleteRecord(record: DisasterRecord, event: Event): void {
    event.stopPropagation();
    const pwd = this.adminPassword().trim();
    if (!pwd) {
      this.toast.set('删除前请输入管理员密码');
      return;
    }
    if (this.deletingId()) return;
    this.deletingId.set(record.id);
    this.toast.set(null);
    this.apiService.deleteRecord(record.id, pwd).subscribe({
      next: () => {
        this.toast.set(`已删除：${record.id}`);
        this.allRecords.update(list => list.filter(r => r.id !== record.id));
        if (this.selectedRecord()?.id === record.id) {
          this.selectedRecord.set(null);
        }
      },
      error: (err) => {
        console.error(err);
        this.toast.set('删除失败，请检查管理员密码或后端状态');
        this.deletingId.set(null);
      },
      complete: () => this.deletingId.set(null),
    });
  }

  private createDefaultRecord(): ManualRecordInput {
    return {
      lat_code: '39904',   // 39.904 -> +39904
      lng_code: '116408',  // 116.408 -> +116408
      event_time: '',
      source_code: '101',
      carrier_code: '0',
      disaster_category_code: '3',
      disaster_sub_category_code: '02',
      indicator_code: '001',
      value: 10,
      unit: '万平米',
      media_path: '',
      raw_payload: ''
    };
  }
}
