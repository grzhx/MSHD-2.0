
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin, map, catchError } from 'rxjs';
import { environment } from '../environments/environment';

// 后端原始结构
interface ApiDisasterRecord {
  id: string;
  event_time?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_accessed_at?: string | null;
  lat_code?: string | null;
  lng_code?: string | null;
  source_code?: string | null;
  source_name?: string | null;
  carrier_code?: string | null;
  carrier_name?: string | null;
  disaster_category_code?: string | null;
  disaster_category_name?: string | null;
  disaster_sub_category_code?: string | null;
  disaster_sub_category_name?: string | null;
  indicator_code?: string | null;
  indicator_name?: string | null;
  value?: number | null;
  unit?: string | null;
  media_path?: string | null;
  raw_payload?: string | null;
}

export interface DisasterRecord {
  id: string;
  time: string;
  eventTimeRaw?: string | null;
  createdAt?: string | null;
  location: string;
  lat: number | null;
  lng: number | null;
  disasterType: string;
  disasterCategory: string;
  disasterSubCategory?: string | null;
  indicatorName?: string | null;
  source: string;
  carrier: string;
  intensity: number;
  unit?: string | null;
  loss: string;
  rawPayload?: string | null;
  media: { type: 'image' | 'video', url: string }[];
}

export interface DashboardStats {
  totalCount: number;
  disasterDistribution: { labels: string[]; data: number[] };
  sourceDistribution: { labels: string[]; data: number[] };
  recentActivity: { labels: string[]; data: number[] };
}

export interface ManualRecordInput {
  lat_code: string;
  lng_code: string;
  event_time: string | Date;
  source_code: string;
  carrier_code: string;
  disaster_category_code: string;
  disaster_sub_category_code: string;
  indicator_code: string;
  value?: number | null;
  unit?: string | null;
  media_path?: string | null;
  raw_payload?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);

  private codecApiUrl = environment.codecApiUrl;
  private disasterApiUrl = environment.disasterApiUrl;
  private locationCoordMap: Record<string, { lat: number; lng: number }> = {
    '110000000001': { lat: 39.9042, lng: 116.4074 }, // 北京
    '510823000000': { lat: 31.4769, lng: 103.4936 }, // 汶川县
    '632700000000': { lat: 33.0039, lng: 97.0065 },  // 玉树州
    '410100000000': { lat: 34.7466, lng: 113.6254 }, // 郑州
    '623027000000': { lat: 35.4763, lng: 102.8616 }, // 积石山县
    // 海外/示例事件编码（900...为自定义海外占位码）
    '900000000001': { lat: 3.3167, lng: 95.8547 },   // 北苏门答腊近海（2004 印度洋海啸震中附近）
    '900000000002': { lat: 38.297, lng: 142.372 },   // 日本宫城外海（2011 东北地震）
    '900000000003': { lat: 27.7172, lng: 85.3240 },  // 尼泊尔加德满都
    '900000000004': { lat: -6.093, lng: 105.423 },   // 巽他海峡 Anak Krakatoa 附近
    '900000000005': { lat: 52.9, lng: 158.7 },       // 堪察加半岛外海
    '900000000006': { lat: -8.576, lng: 116.100 },   // 印尼龙目岛
    '900000000007': { lat: 40.9, lng: 141.5 },       // 日本青森外海
  };
  
  // This method calculates stats on the frontend based on the full data list.
  // For large datasets, it's better to have a dedicated backend endpoint for stats.
  getDashboardStats(): Observable<DashboardStats> {
    const summary$ = this.http.get<DashboardStats>(`${this.disasterApiUrl}/dashboard/summary`).pipe(
      catchError(err => {
        console.error('Failed to fetch dashboard summary from backend:', err);
        return of<DashboardStats | null>(null);
      })
    );
    const records$ = this.getDisasterRecords();

    return forkJoin({ summary: summary$, records: records$ }).pipe(
      map(({ summary, records }) => {
        const computed = this.buildDashboardStats(records);
        return {
          totalCount: computed.totalCount,
          disasterDistribution: summary?.disasterDistribution ?? computed.disasterDistribution,
          sourceDistribution: summary?.sourceDistribution ?? computed.sourceDistribution,
          // recentActivity 统一用本地按小时重新聚合，避免时区差异
          recentActivity: computed.recentActivity,
        };
      })
    );
  }

  /**
   * Fetches all disaster records.
   * 后端新增 /api/storage/disaster-records 列表接口，返回 { total, items }。
   */
  getDisasterRecords(): Observable<DisasterRecord[]> {
    return this.http.get<{ total: number, items: ApiDisasterRecord[] }>(
      `${this.disasterApiUrl}/storage/disaster-records`,
      { params: { limit: 200 } }
    ).pipe(
      map(res => (res.items || []).map(item => this.toUiRecord(item))),
      catchError(err => {
        console.error('Failed to fetch disaster records:', err);
        return of([]); // Return an empty array on error to prevent UI crash
      })
    );
  }

  getMonitoringData() {
    return this.http.get(`${this.disasterApiUrl}/monitoring/summary`).pipe(
      catchError(err => {
        console.error('Failed to fetch monitoring data:', err);
        return of({ dataSources: [], apiCalls: [] });
      })
    );
  }

  /**
   * 写入一条手动录入的灾情数据（原始模式），后端会调用编码服务生成 ID 并入库。
   */
  createManualRecord(input: ManualRecordInput, adminPassword: string): Observable<string> {
    const eventTime = this.normalizeEventTime(input.event_time);

    const payload = {
      event: {
        lat_code: input.lat_code,
        lng_code: input.lng_code,
        event_time: eventTime,
        source_code: input.source_code,
        carrier_code: input.carrier_code,
        disaster_category_code: input.disaster_category_code,
        disaster_sub_category_code: input.disaster_sub_category_code,
        indicator_code: input.indicator_code,
        value: input.value ?? null,
        unit: input.unit ?? null,
        media_path: input.media_path ?? null,
        raw_payload: input.raw_payload ?? null
      }
    };

    return this.http.post<{ id: string; status: string; message?: string }>(
      `${this.disasterApiUrl}/ingest`,
      payload,
      { params: { mode: 'raw' }, headers: { 'X-Admin-Password': adminPassword } }
    ).pipe(
      map(res => res.id),
      catchError(err => {
        console.error('Failed to create manual record:', err);
        throw err;
      })
    );
  }

  deleteRecord(recordId: string, adminPassword: string): Observable<void> {
    return this.http.delete<void>(
      `${this.disasterApiUrl}/storage/disaster-records/${recordId}`,
      { headers: { 'X-Admin-Password': adminPassword } }
    );
  }

  getDictionaryData(): Observable<any> {
    const source$ = this.http.get<Record<string, Record<string, string>>>(`${this.codecApiUrl}/dict/source`);
    const carrier$ = this.http.get<Record<string, string>>(`${this.codecApiUrl}/dict/carrier`);
    const disaster$ = this.http.get<Record<string, Record<string, string>>>(`${this.codecApiUrl}/dict/disaster`);

    return forkJoin({
      source: source$,
      carrier: carrier$,
      disaster: disaster$
    }).pipe(
      map(res => ({
        source: this.flattenSource(res.source),
        carrier: this.flattenCarrier(res.carrier),
        disaster: this.flattenDisaster(res.disaster)
      })),
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
    
    // Disaster service 也提供 /health
    const disasterStatus$ = this.http.get(`${disasterBaseUrl}/health`, { responseType: 'text' }).pipe(
      map(() => 'Online'),
      catchError(() => of('Offline'))
    );

    return forkJoin({
      codec: codecStatus$,
      disaster: disasterStatus$
    });
  }

  private normalizeDashboardStats(data: DashboardStats | null | undefined): DashboardStats {
    return {
      totalCount: data?.totalCount ?? 0,
      disasterDistribution: {
        labels: data?.disasterDistribution?.labels ?? [],
        data: data?.disasterDistribution?.data ?? [],
      },
      sourceDistribution: {
        labels: data?.sourceDistribution?.labels ?? [],
        data: data?.sourceDistribution?.data ?? [],
      },
      recentActivity: {
        labels: data?.recentActivity?.labels ?? [],
        data: data?.recentActivity?.data ?? [],
      },
    };
  }

  private buildDashboardStats(records: DisasterRecord[]): DashboardStats {
    const disasterCounts = records.reduce((acc, rec) => {
      const key = rec.disasterCategory || '其他';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const sourceCounts = records.reduce((acc, rec) => {
      const key = rec.source || '未知来源';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const now = new Date();
    const windowStart = new Date(now.getTime());
    windowStart.setMinutes(0, 0, 0);
    windowStart.setHours(windowStart.getHours() - 23); // 包含当前小时在内的最近 24h
    const hourlyBuckets = Array.from({ length: 24 }, (_, i) => {
      const bucket = new Date(windowStart.getTime() + i * 3600 * 1000);
      return { time: bucket, count: 0 };
    });

    records.forEach(rec => {
      // 对于历史事件（事件时间可能很早），以写入时间优先计入 24h 新增
      const rawTime = rec.createdAt || rec.eventTimeRaw;
      const ts = this.parseDateValue(rawTime);
      if (!ts) return;

      const diff = ts.getTime() - hourlyBuckets[0].time.getTime();
      const bucketIndex = Math.floor(diff / (3600 * 1000));
      if (bucketIndex >= 0 && bucketIndex < hourlyBuckets.length) {
        hourlyBuckets[bucketIndex].count += 1;
      }
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
        labels: hourlyBuckets.map(bucket => this.formatHourLabel(bucket.time)),
        data: hourlyBuckets.map(bucket => bucket.count),
      },
    };
  }

  private formatHourLabel(date: Date): string {
    return `${date.getHours().toString().padStart(2, '0')}:00`;
  }

  private normalizeEventTime(raw: string | Date): string {
    if (raw instanceof Date) {
      return raw.toISOString();
    }
    const trimmed = (raw || '').trim();
    if (!trimmed) return new Date().toISOString();

    // 支持 "YY/MM/DD HH:mm UTC+8" 或 "YY/MM/DD UTC+8"
    const match = trimmed.match(/^(\d{2})\/(\d{2})\/(\d{2})(?:\s+(\d{2}):(\d{2}))?\s*(?:UTC\+8)?$/i);
    if (match) {
      const [, yy, mm, dd, hh = '00', mi = '00'] = match;
      const fullYear = 2000 + Number(yy);
      const month = Number(mm);
      const day = Number(dd);
      const hour = Number(hh);
      const minute = Number(mi);
      const pad = (n: number) => n.toString().padStart(2, '0');
      return `${fullYear}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}:00+08:00`;
    }

    // 其他格式尝试直接解析
    const date = new Date(trimmed);
    return Number.isNaN(date.getTime()) ? new Date().toISOString() : date.toISOString();
  }

  private parseCoord(code: string | null | undefined): number | null {
    if (!code) return null;
    const num = Number(code);
    if (!Number.isFinite(num)) return null;
    return num / 1000;
  }

  private toUiRecord(api: ApiDisasterRecord): DisasterRecord {
    const parsedEvent = this.parseDateValue(api.event_time);
    const time = parsedEvent ? parsedEvent.toLocaleString() : '未知时间';
    const latValue = this.parseCoord(api.lat_code);
    const lngValue = this.parseCoord(api.lng_code);
    const location = (latValue !== null && lngValue !== null)
      ? `${latValue.toFixed(3)}, ${lngValue.toFixed(3)}`
      : '未知地点';
    const indicatorName = api.indicator_name || '';
    const disasterCategory = api.disaster_category_name || '其他';
    const disasterSubCategory = api.disaster_sub_category_name || null;
    const disasterType = disasterSubCategory || disasterCategory || indicatorName || '其他';
    const loss = indicatorName && api.value != null
      ? `${indicatorName}: ${api.value}${api.unit ?? ''}`
      : (api.unit || indicatorName || '');
    const intensity = api.value ?? 0;

    return {
      id: api.id,
      time,
      eventTimeRaw: api.event_time || null,
      createdAt: api.created_at || null,
      location,
      lat: latValue,
      lng: lngValue,
      disasterType,
      disasterCategory,
      disasterSubCategory,
      indicatorName: indicatorName || null,
      source: api.source_name || api.source_code || '未知来源',
      carrier: api.carrier_name || api.carrier_code || '未知载体',
      intensity,
      unit: api.unit || null,
      loss,
      rawPayload: api.raw_payload || null,
      media: api.media_path ? [{ type: 'image', url: api.media_path }] : [],
    };
  }

  private flattenSource(dictObj: Record<string, Record<string, string>> | null | undefined) {
    const result: { code: string, name: string }[] = [];
    if (!dictObj) return result;
    Object.entries(dictObj).forEach(([cat, subMap]) => {
      Object.entries(subMap).forEach(([sub, name]) => {
        result.push({ code: `${cat}${sub}`, name });
      });
    });
    return result;
  }

  private flattenCarrier(dictObj: Record<string, string> | null | undefined) {
    const result: { code: string, name: string }[] = [];
    if (!dictObj) return result;
    Object.entries(dictObj).forEach(([code, name]) => result.push({ code, name }));
    return result;
  }

  private flattenDisaster(dictObj: Record<string, Record<string, string>> | null | undefined) {
    const result: { code: string, name: string }[] = [];
    if (!dictObj) return result;
    Object.entries(dictObj).forEach(([cat, subMap]) => {
      Object.entries(subMap).forEach(([sub, name]) => {
        result.push({ code: `${cat}${sub}`, name });
      });
    });
    return result;
  }

  private parseDateValue(raw: string | Date | null | undefined): Date | null {
    if (!raw) return null;
    if (raw instanceof Date) return raw;
    const trimmed = raw.trim();
    if (!trimmed) return null;
    const hasTZ = /[Zz]|[+-]\d{2}:\d{2}$/.test(trimmed);
    const iso = hasTZ ? trimmed : `${trimmed}Z`; // 后端 UTC 时间若缺时区标记，则按 UTC 解析
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? null : d;
  }
}
