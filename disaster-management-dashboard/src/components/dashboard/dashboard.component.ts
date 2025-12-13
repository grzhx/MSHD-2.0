
import { Component, ChangeDetectionStrategy, ElementRef, viewChild, inject, signal, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import Chart from 'chart.js/auto';
import { ApiService, DashboardStats } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements AfterViewInit, OnDestroy {
  private apiService = inject(ApiService);
  
  stats = signal<DashboardStats | null>(null);
  recent24hCount = signal<number>(0);
  private viewReady = signal(false);
  private barChart?: Chart;
  private pieChart?: Chart;
  private lineChart?: Chart;

  barChartEl = viewChild<ElementRef<HTMLCanvasElement>>('barChart');
  pieChartEl = viewChild<ElementRef<HTMLCanvasElement>>('pieChart');
  lineChartEl = viewChild<ElementRef<HTMLCanvasElement>>('lineChart');

  constructor() {
    this.apiService.getDashboardStats().subscribe(data => {
      this.stats.set(data);
      this.recent24hCount.set((data.recentActivity?.data || []).reduce((sum, n) => sum + n, 0));
      this.tryRenderCharts();
    });
  }

  ngAfterViewInit(): void {
    this.viewReady.set(true);
    this.tryRenderCharts();
  }

  ngOnDestroy(): void {
    this.barChart?.destroy();
    this.pieChart?.destroy();
    this.lineChart?.destroy();
  }

  private tryRenderCharts(): void {
    if (!this.viewReady() || !this.stats()) {
      return;
    }
    queueMicrotask(() => {
      this.createBarChart();
      this.createPieChart();
      this.createLineChart();
    });
  }

  private createBarChart() {
    const canvas = this.barChartEl()?.nativeElement;
    const data = this.stats()?.disasterDistribution;
    if (!canvas || !data) return;

    this.barChart?.destroy();
    
    this.barChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [{
          label: '灾害数量',
          data: data.data,
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { 
            beginAtZero: true, 
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
            ticks: { color: '#d1d5db' }
          },
          x: { 
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
            ticks: { color: '#d1d5db' }
          }
        }
      }
    });
  }

  private createPieChart() {
    const canvas = this.pieChartEl()?.nativeElement;
    const data = this.stats()?.sourceDistribution;
    if (!canvas || !data) return;

    this.pieChart?.destroy();

    this.pieChart = new Chart(canvas, {
      type: 'pie',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.data,
          backgroundColor: ['#3B82F6', '#10B981', '#F97316', '#8B5CF6'],
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#d1d5db' }
          }
        }
      }
    });
  }

  private createLineChart() {
    const canvas = this.lineChartEl()?.nativeElement;
    const data = this.stats()?.recentActivity;
    if (!canvas || !data) return;

    this.lineChart?.destroy();

    this.lineChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: data.labels.slice(-24), // Show last 24h
        datasets: [{
          label: '新增灾情',
          data: data.data.slice(-24),
          fill: true,
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          borderColor: '#10B981',
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { 
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
            ticks: { color: '#d1d5db' }
          },
          x: { 
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
            ticks: { color: '#d1d5db' }
          }
        }
      }
    });
  }
}
