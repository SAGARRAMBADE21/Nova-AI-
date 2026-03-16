import { useEffect, useRef } from 'react';
import { MessageSquare, Cpu, AlertTriangle, Users, LineChart, PieChart } from 'lucide-react';
import type Chart from 'chart.js/auto';

const Metrics = () => {
  const queryChartRef = useRef<HTMLCanvasElement>(null);
  const confidenceChartRef = useRef<HTMLCanvasElement>(null);

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
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
              label: 'Queries',
              data: [120, 190, 150, 220, 310, 80, 60],
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
              data: [75, 18, 7],
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
  }, []);

  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-10">
        <div>
          <h1 className="text-3xl font-bold text-brand-charcoal">Performance &amp; Usage</h1>
          <p className="text-brand-grayBody mt-2">Real-time LLMOps metrics and security monitoring.</p>
        </div>
        <div className="inline-flex bg-brand-lightBg p-1 rounded-xl border border-brand-border">
          <button className="px-4 py-2 text-xs font-bold bg-white text-brand-charcoal rounded-lg shadow-sm">Last 7 Days</button>
          <button className="px-4 py-2 text-xs font-bold text-brand-grayBody hover:text-brand-charcoal transition-colors">Last 30 Days</button>
        </div>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">Total Queries</span>
            <MessageSquare className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">1,402</h4>
          <p className="text-[11px] font-bold text-green-600 mt-2">↑ 8.4% vs last week</p>
        </div>
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">Tokens Used</span>
            <Cpu className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">842K</h4>
          <p className="text-[11px] font-bold text-brand-grayBody mt-2">GPT-4o Model</p>
        </div>
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">Security Blocks</span>
            <AlertTriangle className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">24</h4>
          <p className="text-[11px] font-bold text-red-500 mt-2">Lakera Guard active</p>
        </div>
        <div className="bg-brand-lightBg border border-brand-border p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase text-brand-grayBody tracking-wider">HITL Escalations</span>
            <Users className="w-4 h-4 text-brand-orange" />
          </div>
          <h4 className="text-3xl font-extrabold text-brand-charcoal">5</h4>
          <p className="text-[11px] font-bold text-brand-grayBody mt-2">Avg SLA: 22m</p>
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
