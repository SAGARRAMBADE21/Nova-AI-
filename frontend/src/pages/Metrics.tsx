import { useEffect, useMemo, useRef, useState } from 'react';
import { MessageSquare, Cpu, AlertTriangle, Users, LineChart, PieChart } from 'lucide-react';
import type Chart from 'chart.js/auto';
import { getMetrics, type MetricsResponse } from '../lib/api';

type Period = '7d' | '30d';

const EMPTY_METRICS: MetricsResponse = {
  period_days: 7,
  query_count: 0,
  previous_query_count: 0,
  tool_invocations: 0,
  security_blocks: 0,
  hitl_requests: 0,
  avg_latency_ms: 0,
  total_tokens: 0,
  errors: 0,
  confidence_breakdown: {
    high: 0,
    medium: 0,
    low: 0,
  },
  query_timeseries: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    values: [0, 0, 0, 0, 0, 0, 0],
  },
};

function formatCompact(num: number): string {
  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (num >= 1_000) {
    return `${Math.round(num / 1_000)}K`;
  }
  return num.toLocaleString();
}

const Metrics = () => {
  const [period, setPeriod] = useState<Period>('7d');
  const [metrics, setMetrics] = useState<MetricsResponse>(EMPTY_METRICS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const queryChartRef = useRef<HTMLCanvasElement>(null);
  const confidenceChartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let active = true;

    const loadMetrics = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getMetrics(period === '7d' ? 7 : 30);
        if (active) {
          setMetrics({ ...EMPTY_METRICS, ...response });
        }
      } catch (err) {
        if (active) {
          const message = err instanceof Error ? err.message : 'Unable to load metrics';
          setError(message);
          setMetrics(EMPTY_METRICS);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadMetrics();

    return () => {
      active = false;
    };
  }, [period]);

  const chartData = useMemo(() => {
    const previousPeriodQueries = metrics.previous_query_count;
    const queryDelta = previousPeriodQueries > 0
      ? ((metrics.query_count - previousPeriodQueries) / previousPeriodQueries) * 100
      : 0;

    return {
      labels: metrics.query_timeseries.labels,
      querySeries: metrics.query_timeseries.values,
      confidenceSeries: [
        metrics.confidence_breakdown.high,
        metrics.confidence_breakdown.medium,
        metrics.confidence_breakdown.low,
      ],
      queryDelta,
    };
  }, [metrics]);

  useEffect(() => {
    let queryChartInstance: Chart | null = null;
    let confChartInstance: Chart | null = null;
    let disposed = false;

    const initCharts = async () => {
      const { default: ChartCtor } = await import('chart.js/auto');
      if (disposed) {
        return;
      }

      if (queryChartRef.current) {
        queryChartInstance = new ChartCtor(queryChartRef.current, {
          type: 'line',
          data: {
            labels: chartData.labels,
            datasets: [{
              label: 'Queries',
              data: chartData.querySeries,
              borderColor: '#FF5925',
              backgroundColor: 'rgba(255, 89, 37, 0.1)',
              tension: 0.4,
              fill: true,
              pointRadius: 4,
              pointBackgroundColor: '#FFF',
              borderWidth: 3
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
              x: { grid: { display: false } }
            }
          }
        });
      }

      if (confidenceChartRef.current) {
        confChartInstance = new ChartCtor(confidenceChartRef.current, {
          type: 'doughnut',
          data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
              data: chartData.confidenceSeries,
              backgroundColor: ['#16A34A', '#EAB308', '#DC2626'],
              borderWidth: 0,
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: { padding: 20, font: { weight: 'bold', family: 'Inter' } }
              }
            }
            ,
            cutout: '70%'
          }
        });
      }
    };

    void initCharts();

    return () => {
      disposed = true;
      if (queryChartInstance) queryChartInstance.destroy();
      if (confChartInstance) confChartInstance.destroy();
    };
  }, [chartData]);

  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10">
        <div>
          <h1 className="text-3xl font-bold text-brand-charcoal">Performance &amp; Usage</h1>
          <p className="text-brand-grayBody mt-2">Real-time LLMOps metrics and security monitoring.</p>
        </div>
        <div className="inline-flex bg-brand-lightBg p-1 rounded-xl border border-brand-border">
          <button
            onClick={() => setPeriod('7d')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors ${
              period === '7d'
                ? 'bg-white text-brand-charcoal shadow-sm'
                : 'text-brand-grayBody hover:text-brand-charcoal'
            }`}
          >
            Last 7 Days
          </button>
          <button
            onClick={() => setPeriod('30d')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-colors ${
              period === '30d'
                ? 'bg-white text-brand-charcoal shadow-sm'
                : 'text-brand-grayBody hover:text-brand-charcoal'
            }`}
          >
            Last 30 Days
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Unable to refresh metrics: {error}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">Total Queries</span>
            <MessageSquare className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">{loading ? '...' : metrics.query_count.toLocaleString()}</h4>
          <p className={`text-[11px] font-bold mt-2 ${chartData.queryDelta >= 0 ? 'text-green-600' : 'text-red-500'}`}>
            {chartData.queryDelta >= 0 ? '↑' : '↓'} {Math.abs(chartData.queryDelta).toFixed(1)}% vs previous period
          </p>
        </div>
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">Tokens Used</span>
            <Cpu className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">{loading ? '...' : formatCompact(metrics.total_tokens)}</h4>
          <p className="text-[11px] font-bold text-brand-grayBody mt-2">Avg latency: {loading ? '...' : `${Math.round(metrics.avg_latency_ms)}ms`}</p>
        </div>
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">Security Blocks</span>
            <AlertTriangle className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">{loading ? '...' : metrics.security_blocks.toLocaleString()}</h4>
          <p className="text-[11px] font-bold text-red-500 mt-2">Policy controls active</p>
        </div>
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">HITL Escalations</span>
            <Users className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">{loading ? '...' : metrics.hitl_requests.toLocaleString()}</h4>
          <p className="text-[11px] font-bold text-brand-grayBody mt-2">Tool calls: {loading ? '...' : metrics.tool_invocations.toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        <div className="p-8 border border-brand-border rounded-3xl bg-white">
          <h4 className="text-sm font-bold text-brand-charcoal mb-6 flex items-center">
            <LineChart className="w-4 h-4 mr-2 text-brand-orange" /> Query Volume Over Time
          </h4>
          <div className="h-64 flex items-center justify-center bg-brand-lightBg/30 rounded-xl">
            <canvas ref={queryChartRef}></canvas>
          </div>
        </div>
        <div className="p-8 border border-brand-border rounded-3xl bg-white">
          <h4 className="text-sm font-bold text-brand-charcoal mb-6 flex items-center">
            <PieChart className="w-4 h-4 mr-2 text-brand-orange" /> Response Confidence Breakdown
          </h4>
          <div className="h-64 flex items-center justify-center">
            <canvas ref={confidenceChartRef}></canvas>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Metrics;
