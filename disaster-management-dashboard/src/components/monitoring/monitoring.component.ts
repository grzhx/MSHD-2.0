
import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-monitoring',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './monitoring.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MonitoringComponent {
  private apiService = inject(ApiService);
  monitoringData = signal<any>(null);

  constructor() {
    this.apiService.getMonitoringData().subscribe(data => {
      this.monitoringData.set(data);
    });
  }
}
