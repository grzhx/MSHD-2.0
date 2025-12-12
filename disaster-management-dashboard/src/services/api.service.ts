
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin, map, catchError, tap } from 'rxjs';
import { environment } from '../environments/environment';

// Mock data models - In a real app, these would be in separate model files
export interface DisasterRecord {
  id: string;
  time: string;
  eventTime?: Date;
  location: string;
  lat: number;
  lng: number;
  disasterType: string;
  disasterCategory: 'Geological' | 'Meteorological' | 'Flood' | 'Other';
  source: string;
  carrier: string;
  intensity: number;
  loss: string;
  media: { type: 'image' | 'video', url: string }[];
}

interface BackendDisasterRecord {
  id: string;
  event_time?: string;
  location_code?: string;
  location_name?: string;
  source_code?: string;
  source_name?: string;
  carrier_code?: string;
  carrier_name?: string;
  disaster_category_code?: string;
  disaster_category_name?: string;
  disaster_sub_category_code?: string;
  disaster_sub_category_name?: string;
  indicator_code?: string;
  indicator_name?: string;
  value?: number;
  unit?: string;
  media_path?: string;
  raw_payload?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);

  private codecApiUrl = environment.codecApiUrl;
  private disasterApiUrl = environment.disasterApiUrl;
  private fallbackRecords: DisasterRecord[] = [
    { id: 'D-240730-1', time: '2024-07-30 14:30', location: '四川省阿坝州', lat: 31.7, lng: 103.5, disasterType: '地震', disasterCategory: 'Geological', source: '前方指挥部', carrier: '卫星电话', intensity: 7.2, loss: '房屋倒塌严重', media: [{ type: 'image', url: 'https://picsum.photos/seed/disaster1/400/300' }] },
    { id: 'D-240730-2', time: '2024-07-30 08:15', location: '河南省郑州市', lat: 34.7, lng: 113.6, disasterType: '暴雨', disasterCategory: 'Flood', source: '舆情感知', carrier: '社交媒体', intensity: 4, loss: '城市内涝，交通中断', media: [{ type: 'video', url: '#' }] },
    { id: 'D-240729-1', time: '2024-07-29 18:00', location: '福建省福州市', lat: 26.0, lng: 119.3, disasterType: '台风', disasterCategory: 'Meteorological', source: '气象预警', carrier: '官方发布', intensity: 9, loss: '大风导致树木倒伏', media: [{ type: 'image', url: 'https://picsum.photos/seed/disaster2/400/300' }] },
    { id: 'D-240728-3', time: '2024-07-28 11:45', location: '云南省昆明市', lat: 25.0, lng: 102.7, disasterType: '山体滑坡', disasterCategory: 'Geological', source: '无人机勘测', carrier: '航拍数据', intensity: 6, loss: '道路中断', media: [{ type: 'image', url: 'https://picsum.photos/seed/disaster3/400/300' }] },
    { id: 'D-240727-5', time: '2024-07-27 22:05', location: '河北省石家庄市', lat: 38.0, lng: 114.5, disasterType: '干旱', disasterCategory: 'Meteorological', source: '农业部门', carrier: '上报', intensity: 5, loss: '农作物受灾', media: [] },
    { id: 'D-240726-1', time: '2024-07-26 15:20', location: '湖南省长沙市', lat: 28.2, lng: 112.9, disasterType: '洪涝', disasterCategory: 'Flood', source: '水利部门', carrier: '监测站', intensity: 8, loss: '河流超警戒水位', media: [{ type: 'video', url: '#' }] },
    { id: 'D-240725-2', time: '2024-07-25 03:10', location: '新疆维吾尔自治区', lat: 43.8, lng: 87.6, disasterType: '沙尘暴', disasterCategory: 'Meteorological', source: '舆情感知', carrier: '社交媒体', intensity: 7, loss: '能见度低', media: [] },
  ];
  
  // This method calculates stats on the frontend based on the full data list.
  // For large datasets, it's better to have a dedicated backend endpoint for stats.
  getDashboardStats(): Observable<any> {
    return this.getDisasterRecords().pipe(
      map(records => {
        const now = new Date();
        const disasterCounts = records.reduce((acc, rec) => {
          acc[rec.disasterCategory] = (acc[rec.disasterCategory] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);

        const sourceCounts = records.reduce((acc, rec) => {
          acc[rec.source] = (acc[rec.source] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);

        const hoursWindow = 72;
        const buckets = Array.from({ length: hoursWindow }, () => 0);
        records.forEach(rec => {
          const ts = rec.eventTime ?? now;
          const hoursDiff = Math.floor((now.getTime() - ts.getTime()) / 3600000);
          const idx = hoursWindow - 1 - hoursDiff;
          if (idx >= 0 && idx < hoursWindow) {
            buckets[idx] += 1;
          }
        });
        const recentData = buckets.map((count, i) => {
          const hour = new Date(now.getTime() - (hoursWindow - 1 - i) * 3600 * 1000);
          return { time: `${hour.getHours()}:00`, count };
        });

        return {
          totalCount: records.length,
          disasterDistribution: {
            labels: Object.keys(disasterCounts),
            data: Object.values(disasterCounts),
          },
          sourceDistribution: {
            labels: Object.keys(sourceCounts),
            data: Object.values(sourceCounts),
          },
          recentActivity: {
            labels: recentData.map(d => d.time),
            data: recentData.map(d => d.count),
          }
        };
      })
    );
  }

  /**
   * Fetches all disaster records.
   */
  getDisasterRecords(): Observable<DisasterRecord[]> {
    return this.http.get<BackendDisasterRecord[]>(`${this.disasterApiUrl}/storage/disaster-records?limit=200`).pipe(
      map(records => records.map(r => this.mapBackendRecord(r))),
      tap(mapped => console.log(`[api] fetched ${mapped.length} records from backend`)),
      catchError(err => {
        console.error('Failed to fetch disaster records, falling back to mock data:', err);
        return of(this.fallbackRecords);
      })
    );
  }

  // Monitoring data remains mocked as no specific backend endpoints were provided for it.
  getMonitoringData() {
    return of({
      dataSources: [
        { name: '前方指挥部', lastReceived: '2024-07-30 14:30', count24h: 1, count7d: 5, errors: 0 },
        { name: '舆情感知', lastReceived: '2024-07-30 08:15', count24h: 2, count7d: 12, errors: 1 },
        { name: '气象预警', lastReceived: '2024-07-29 18:00', count24h: 0, count7d: 3, errors: 0 },
        { name: '无人机勘测', lastReceived: '2024-07-28 11:45', count24h: 0, count7d: 2, errors: 0 },
      ],
      apiCalls: [
        { endpoint: '/api/ingest', caller: '数据采集模块', requests: 1250, avgResponse: '15ms', errorRate: '0.2%' },
        { endpoint: '/api/codec/decode', caller: '数据展示模块', requests: 8730, avgResponse: '5ms', errorRate: '0.01%' },
        { endpoint: '/api/storage/disaster-records', caller: '内部服务', requests: 450, avgResponse: '8ms', errorRate: '0.0%' },
      ]
    });
  }

  getDictionaryData(): Observable<any> {
    const source$ = this.http.get<{code: string, name: string}[]>(`${this.codecApiUrl}/dict/source?flat=1`);
    const carrier$ = this.http.get<{code: string, name: string}[]>(`${this.codecApiUrl}/dict/carrier?flat=1`);
    const disaster$ = this.http.get<{code: string, name: string}[]>(`${this.codecApiUrl}/dict/disaster?flat=1`);

    return forkJoin({
      source: source$,
      carrier: carrier$,
      disaster: disaster$
    }).pipe(
      catchError(err => {
        console.error('Failed to fetch dictionary data:', err);
        return of({ source: [], carrier: [], disaster: [] }); // Return empty data on error
      })
    );
  }

  checkBackendStatus(): Observable<{ codec: string, disaster: string }> {
    // Construct the base URLs from the environment config to be more robust.
    const unifiedBaseUrl = new URL(this.disasterApiUrl).origin; // unified backend

    const healthCheck$ = this.http.get(`${unifiedBaseUrl}/health`, { responseType: 'text' }).pipe(
      map(() => 'Online'),
      catchError(err => {
        console.warn('Backend health check failed:', err);
        return of('Offline');
      })
    );

    return forkJoin({
      codec: healthCheck$,
      disaster: healthCheck$
    });
  }

  private mapBackendRecord(rec: BackendDisasterRecord): DisasterRecord {
    const eventTime = rec.event_time ? new Date(rec.event_time) : undefined;
    const location = rec.location_name || rec.location_code || '未知地点';
    const { lat, lng } = this.deriveCoordinates(rec.location_code);
    const disasterCategory = this.mapDisasterCategory(rec.disaster_category_code, rec.disaster_category_name);
    const loss = rec.raw_payload || rec.indicator_name || rec.disaster_category_name || '';
    const media = rec.media_path ? [{ type: 'image' as const, url: rec.media_path }] : [];

    return {
      id: rec.id,
      time: eventTime ? eventTime.toLocaleString() : '未知时间',
      eventTime,
      location,
      lat,
      lng,
      disasterType: rec.disaster_category_name || '灾情',
      disasterCategory,
      source: rec.source_name || rec.source_code || '未知来源',
      carrier: rec.carrier_name || rec.carrier_code || '未知载体',
      intensity: rec.value ?? 0,
      loss,
      media,
    };
  }

  private mapDisasterCategory(code?: string, name?: string): DisasterRecord['disasterCategory'] {
    if (name && /风|台风|气象|旱/.test(name)) return 'Meteorological';
    if (name && /洪|雨|水/.test(name)) return 'Flood';
    if (name && /滑坡|崩塌|泥石流/.test(name)) return 'Geological';
    switch (code) {
      case '1':
      case '3':
      case '5':
        return 'Geological';
      case '4':
        return 'Flood';
      case '0':
      case '2':
        return 'Other';
      default:
        return 'Other';
    }
  }

  private deriveCoordinates(locationCode?: string): { lat: number; lng: number } {
    if (!locationCode || locationCode.length < 4 || Number.isNaN(Number(locationCode))) {
      return { lat: 30.6, lng: 104.0 }; // 成都附近作为默认中心
    }
    const codeNum = Number(locationCode.slice(-6));
    // 生成一个稳定但分散的坐标，避免所有点重叠
    const lat = 20 + (codeNum % 1500) / 50; // 约 20-50 度
    const lng = 90 + (codeNum % 2000) / 30; // 约 90-156 度
    return { lat, lng };
  }
}
