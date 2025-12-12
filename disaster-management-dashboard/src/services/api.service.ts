
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin, map, catchError } from 'rxjs';
import { environment } from '../environments/environment';

// Mock data models - In a real app, these would be in separate model files
export interface DisasterRecord {
  id: string;
  time: string;
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

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);

  private codecApiUrl = environment.codecApiUrl;
  private disasterApiUrl = environment.disasterApiUrl;
  
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

        const recentData = Array.from({length: 72}, (_, i) => {
            const hour = new Date(now.getTime() - (71 - i) * 3600 * 1000);
            return {
                time: `${hour.getHours()}:00`,
                count: Math.floor(Math.random() * 5) // Note: This part is still random
            };
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
   * NOTE: Assumes a GET endpoint at /api/storage/disaster-records that returns an array.
   * This endpoint is not explicitly listed in the backend spec but is a standard REST pattern.
   * If the backend only supports getting records by ID, this implementation will need to be changed.
   */
  getDisasterRecords(): Observable<DisasterRecord[]> {
    // Faking the implementation with mock data since the list endpoint doesn't exist.
    const mockRecords: DisasterRecord[] = [
      { id: 'D-240730-1', time: '2024-07-30 14:30', location: '四川省阿坝州', lat: 31.7, lng: 103.5, disasterType: '地震', disasterCategory: 'Geological', source: '前方指挥部', carrier: '卫星电话', intensity: 7.2, loss: '房屋倒塌严重', media: [{ type: 'image', url: 'https://picsum.photos/seed/disaster1/400/300' }] },
      { id: 'D-240730-2', time: '2024-07-30 08:15', location: '河南省郑州市', lat: 34.7, lng: 113.6, disasterType: '暴雨', disasterCategory: 'Flood', source: '舆情感知', carrier: '社交媒体', intensity: 4, loss: '城市内涝，交通中断', media: [{ type: 'video', url: '#' }] },
      { id: 'D-240729-1', time: '2024-07-29 18:00', location: '福建省福州市', lat: 26.0, lng: 119.3, disasterType: '台风', disasterCategory: 'Meteorological', source: '气象预警', carrier: '官方发布', intensity: 9, loss: '大风导致树木倒伏', media: [{ type: 'image', url: 'https://picsum.photos/seed/disaster2/400/300' }] },
      { id: 'D-240728-3', time: '2024-07-28 11:45', location: '云南省昆明市', lat: 25.0, lng: 102.7, disasterType: '山体滑坡', disasterCategory: 'Geological', source: '无人机勘测', carrier: '航拍数据', intensity: 6, loss: '道路中断', media: [{ type: 'image', url: 'https://picsum.photos/seed/disaster3/400/300' }] },
      { id: 'D-240727-5', time: '2024-07-27 22:05', location: '河北省石家庄市', lat: 38.0, lng: 114.5, disasterType: '干旱', disasterCategory: 'Meteorological', source: '农业部门', carrier: '上报', intensity: 5, loss: '农作物受灾', media: [] },
      { id: 'D-240726-1', time: '2024-07-26 15:20', location: '湖南省长沙市', lat: 28.2, lng: 112.9, disasterType: '洪涝', disasterCategory: 'Flood', source: '水利部门', carrier: '监测站', intensity: 8, loss: '河流超警戒水位', media: [{ type: 'video', url: '#' }] },
      { id: 'D-240725-2', time: '2024-07-25 03:10', location: '新疆维吾尔自治区', lat: 43.8, lng: 87.6, disasterType: '沙尘暴', disasterCategory: 'Meteorological', source: '舆情感知', carrier: '社交媒体', intensity: 7, loss: '能见度低', media: [] },
    ];
    return of(mockRecords);
    
    // REAL IMPLEMENTATION WOULD BE:
    // return this.http.get<DisasterRecord[]>(`${this.disasterApiUrl}/storage/disaster-records`).pipe(
    //   catchError(err => {
    //     console.error('Failed to fetch disaster records:', err);
    //     return of([]); // Return an empty array on error to prevent UI crash
    //   })
    // );
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
    const source$ = this.http.get<{code: string, name: string}[]>(`${this.codecApiUrl}/dict/source`);
    const carrier$ = this.http.get<{code: string, name: string}[]>(`${this.codecApiUrl}/dict/carrier`);
    const disaster$ = this.http.get<{code: string, name: string}[]>(`${this.codecApiUrl}/dict/disaster`);

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
    const codecBaseUrl = new URL(this.codecApiUrl).origin; // e.g., "http://localhost:8000"
    const disasterBaseUrl = new URL(this.disasterApiUrl).origin; // e.g., "http://localhost:8001"

    // Check the /health endpoint for the codec service.
    const codecStatus$ = this.http.get(`${codecBaseUrl}/health`, { responseType: 'text' }).pipe(
      map(() => 'Online'),
      catchError(() => of('Offline'))
    );
    
    // The disaster service doesn't have a specific /health endpoint, so we check the root URL.
    const disasterStatus$ = this.http.get(disasterBaseUrl, { responseType: 'text' }).pipe(
      map(() => 'Online'),
      catchError(() => of('Offline'))
    );

    return forkJoin({
      codec: codecStatus$,
      disaster: disasterStatus$
    });
  }
}
