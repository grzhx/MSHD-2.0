
import { Component, ChangeDetectionStrategy, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DashboardComponent } from './components/dashboard/dashboard.component';
import { MapViewComponent } from './components/map-view/map-view.component';
import { ListViewComponent } from './components/list-view/list-view.component';
import { MonitoringComponent } from './components/monitoring/monitoring.component';
import { DictionaryComponent } from './components/dictionary/dictionary.component';
import { SafeHtmlPipe } from './pipes/safe-html.pipe';
import { ApiService } from './services/api.service';

type View = 'dashboard' | 'map' | 'list' | 'monitoring' | 'dictionary';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [
    CommonModule,
    DashboardComponent,
    MapViewComponent,
    ListViewComponent,
    MonitoringComponent,
    DictionaryComponent,
    SafeHtmlPipe
  ]
})
export class AppComponent {
  private apiService = inject(ApiService);
  
  currentView = signal<View>('dashboard');
  sidebarOpen = signal(true);
  backendStatus = signal<{ codec: string; disaster: string } | null>(null);

  navItems = [
    { id: 'dashboard', name: '总览大屏', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>' },
    { id: 'map', name: '地图视图', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>' },
    { id: 'list', name: '列表视图', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>' },
    { id: 'monitoring', name: '运维管理', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V7a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
    { id: 'dictionary', name: '字典配置', icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v11.494m-9-5.747h18" /></svg>' }
  ];

  constructor() {
    this.apiService.checkBackendStatus().subscribe(status => {
      this.backendStatus.set(status);
    });
  }

  changeView(view: View): void {
    this.currentView.set(view);
  }

  toggleSidebar(): void {
    this.sidebarOpen.update(open => !open);
  }
}
