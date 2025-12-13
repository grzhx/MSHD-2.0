
import { Component, ChangeDetectionStrategy, inject, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, DisasterRecord } from '../../services/api.service';

declare var L: any;

@Component({
  selector: 'app-map-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map-view.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MapViewComponent implements AfterViewInit, OnDestroy {
  private apiService = inject(ApiService);
  private map: any;

  private categoryColors: Record<string, string> = {
    'Geological': '#F97316', // orange-500
    'Meteorological': '#3B82F6', // blue-500
    'Flood': '#10B981', // green-500
    'Other': '#6B7280', // gray-500
  };
  
  ngAfterViewInit(): void {
    this.initMap();
    this.loadDisasterPoints();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap(): void {
    this.map = L.map('map', {
      center: [34.0, 108.0], // Center of China
      zoom: 5
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(this.map);
  }

  private loadDisasterPoints(): void {
    this.apiService.getDisasterRecords().subscribe(records => {
      records.forEach(record => {
        this.addMarker(record);
      });
    });
  }

  private addMarker(record: DisasterRecord): void {
    if (record.lat === null || record.lng === null) {
        return; // 没有坐标信息则跳过绘制
    }
    const color = this.categoryColors[record.disasterCategory] || '#3B82F6';
    const safeIntensity = Number.isFinite(record.intensity) ? record.intensity : 0;
    const radius = Math.min(20, Math.max(5, 5 + safeIntensity)); // clamp to avoid oversized circles
    
    const marker = L.circleMarker([record.lat, record.lng], {
      radius: radius,
      fillColor: color,
      color: "#fff",
      weight: 1,
      opacity: 1,
      fillOpacity: 0.7
    }).addTo(this.map);
    
    const popupContent = `
      <div class="text-gray-200">
        <h3 class="font-bold text-lg mb-2 border-b border-gray-600 pb-1">${record.disasterType} - ${record.location}</h3>
        <p><strong>时间:</strong> ${record.time}</p>
        <p><strong>来源:</strong> ${record.source}</p>
        <p><strong>损失:</strong> ${record.loss}</p>
        <p><strong>烈度:</strong> ${record.intensity}</p>
      </div>
    `;

    marker.bindPopup(popupContent);
  }
}
