import { UserPlus, FileUp, ShieldCheck } from 'lucide-react';

const Overview = () => {
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
            <h2 className="text-4xl font-extrabold text-brand-charcoal">42</h2>
            <div className="text-right text-[11px] text-brand-grayBody">
              <span className="block">32 Employee</span>
              <span className="block">10 Manager</span>
            </div>
          </div>
        </div>
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Documents</p>
          <div className="flex items-end justify-between">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">128</h2>
            <div className="text-right text-[11px] text-brand-grayBody">
              <span className="block">84 Public</span>
              <span className="block">44 Private</span>
            </div>
          </div>
        </div>
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Active Sessions</p>
          <div className="flex items-center space-x-4">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">14</h2>
            <div className="h-3 w-3 bg-green-500 rounded-full pulse-dot"></div>
          </div>
        </div>
        <div className="p-6 bg-brand-lightBg border border-brand-border rounded-2xl">
          <p className="text-xs font-bold text-brand-orange uppercase tracking-widest mb-2">Avg Response</p>
          <div className="flex items-end justify-between">
            <h2 className="text-4xl font-extrabold text-brand-charcoal">1.2<span className="text-lg font-normal ml-1">s</span></h2>
            <div className="text-green-600 text-xs font-bold">↓ 12%</div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-brand-charcoal mb-6">Recent Activity</h3>
        <div className="space-y-4">
          <div className="flex items-start space-x-4 p-4 border-b border-brand-border last:border-0 hover:bg-brand-lightBg/50 transition-colors rounded-xl">
            <div className="bg-blue-100 p-2 rounded-full"><UserPlus className="w-4 h-4 text-blue-600" /></div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-brand-charcoal">john@acme.com <span className="font-normal text-brand-grayBody">invited as Employee</span></p>
              <p className="text-xs text-gray-400 mt-0.5">2 hours ago</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 border-b border-brand-border last:border-0 hover:bg-brand-lightBg/50 transition-colors rounded-xl">
            <div className="bg-orange-100 p-2 rounded-full"><FileUp className="w-4 h-4 text-brand-orange" /></div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-brand-charcoal">Q3_Report.pdf <span className="font-normal text-brand-grayBody">ingested (Confidential)</span></p>
              <p className="text-xs text-gray-400 mt-0.5">5 hours ago</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 border-b border-brand-border last:border-0 hover:bg-brand-lightBg/50 transition-colors rounded-xl">
            <div className="bg-green-100 p-2 rounded-full"><ShieldCheck className="w-4 h-4 text-green-600" /></div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-brand-charcoal">HITL escalation: <span className="font-normal text-brand-grayBody">salary query escalated to Manager</span></p>
              <p className="text-xs text-gray-400 mt-0.5">2 days ago</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Overview;
