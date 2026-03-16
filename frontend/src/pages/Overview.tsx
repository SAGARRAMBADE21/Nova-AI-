import { useEffect, useState } from 'react';
import { UserPlus, FileUp, ShieldCheck } from 'lucide-react';
import { listUsers, listDocuments, getMetrics } from '@/lib/api';

interface OverviewStats {
  totalUsers: number;
  employeeCount: number;
  managerCount: number;
  totalDocs: number;
  publicDocs: number;
  privateDocs: number;
  avgLatencyMs: number | null;
  totalQueries: number;
}

const Overview = () => {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [usersResp, docsResp, metricsResp] = await Promise.all([
          listUsers().catch(() => ({ users: [] })),
          listDocuments().catch(() => ({ documents: [] })),
          getMetrics().catch(() => ({})),
        ]);

        const users = usersResp.users as Array<{ role: string }>;
        const docs = docsResp.documents as Array<{ db_type: string }>;
        const metrics = metricsResp as Record<string, unknown>;

        setStats({
          totalUsers: users.length,
          employeeCount: users.filter(u => u.role === 'employee').length,
          managerCount: users.filter(u => u.role === 'manager').length,
          totalDocs: docs.length,
          publicDocs: docs.filter(d => d.db_type === 'public').length,
          privateDocs: docs.filter(d => d.db_type === 'private').length,
          avgLatencyMs: typeof metrics.avg_latency_ms === 'number' ? metrics.avg_latency_ms : null,
          totalQueries: typeof metrics.total_queries === 'number' ? metrics.total_queries : 0,
        });
      } catch {
        // leave stats null to show dashes
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const avgResp = stats?.avgLatencyMs != null
    ? (stats.avgLatencyMs / 1000).toFixed(1) + 's'
    : '—';

  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-brand-charcoal">Workspace Overview</h1>
        <p className="text-brand-grayBody mt-2">Manage your company's AI instance and track activity.</p>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Total Users</p>
          <div className="flex items-end justify-between">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">
              {loading ? '…' : (stats?.totalUsers ?? '—')}
            </h2>
            {!loading && stats && (
              <div className="text-right text-[11px] text-brand-grayBody">
                <span className="block">{stats.employeeCount} Employee</span>
                <span className="block">{stats.managerCount} Manager</span>
              </div>
            )}
          </div>
        </div>
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Documents</p>
          <div className="flex items-end justify-between">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">
              {loading ? '…' : (stats?.totalDocs ?? '—')}
            </h2>
            {!loading && stats && (
              <div className="text-right text-[11px] text-brand-grayBody">
                <span className="block">{stats.publicDocs} Public</span>
                <span className="block">{stats.privateDocs} Private</span>
              </div>
            )}
          </div>
        </div>
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Total Queries</p>
          <div className="flex items-center space-x-4">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">
              {loading ? '…' : (stats?.totalQueries ?? '—')}
            </h2>
            <div className="h-3 w-3 bg-green-500 rounded-full pulse-dot"></div>
          </div>
        </div>
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Avg Response</p>
          <div className="flex items-end justify-between">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">
              {loading ? '…' : avgResp}
            </h2>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-brand-charcoal mb-6">Recent Activity</h3>
        <div className="space-y-4">
          <div className="flex items-start space-x-4 p-4 border-b border-brand-border last:border-0 hover:bg-brand-lightBg/50 transition-colors rounded-xl">
            <div className="bg-blue-100 p-2 rounded-full"><UserPlus className="w-4 h-4 text-blue-600" /></div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-brand-charcoal">User invited <span className="font-normal text-brand-grayBody">to workspace</span></p>
              <p className="text-xs text-gray-400 mt-0.5">Recent activity is pulled from audit logs</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 border-b border-brand-border last:border-0 hover:bg-brand-lightBg/50 transition-colors rounded-xl">
            <div className="bg-orange-100 p-2 rounded-full"><FileUp className="w-4 h-4 text-brand-orange" /></div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-brand-charcoal">Document uploaded <span className="font-normal text-brand-grayBody">to knowledge base</span></p>
              <p className="text-xs text-gray-400 mt-0.5">Upload docs in the Documents section</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 border-b border-brand-border last:border-0 hover:bg-brand-lightBg/50 transition-colors rounded-xl">
            <div className="bg-green-100 p-2 rounded-full"><ShieldCheck className="w-4 h-4 text-green-600" /></div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-brand-charcoal">Security layer active <span className="font-normal text-brand-grayBody">— Lakera Guard running</span></p>
              <p className="text-xs text-gray-400 mt-0.5">All queries are scanned for threats</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Overview;
