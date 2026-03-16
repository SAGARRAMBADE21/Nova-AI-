import { FileText, ShieldCheck, UploadCloud } from 'lucide-react';

const Documents = () => {
  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-brand-charcoal">Knowledge Base</h1>
        <p className="text-brand-grayBody mt-2">Upload and manage the documents that power your AI.</p>
      </header>
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div className="lg:col-span-5 space-y-8">
          <div className="border-2 border-dashed border-brand-border rounded-3xl p-10 text-center hover:border-brand-orange transition-colors cursor-pointer group">
            <div className="bg-brand-lightBg w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
              <UploadCloud className="text-brand-orange w-8 h-8" />
            </div>
            <h4 className="text-brand-charcoal font-bold">Upload Document</h4>
            <p className="text-sm text-brand-grayBody mt-2 leading-relaxed">Drag &amp; drop files here, or click to browse.<br/><span className="text-xs font-semibold">PDF, DOCX, XLSX, TXT, JSON, MD</span></p>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Category</label>
              <input className="w-full px-4 py-2.5 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none" placeholder="e.g. HR, Finance, IT" type="text" />
            </div>
            <div className="p-4 bg-brand-lightBg rounded-2xl border border-brand-border">
              <label className="block text-xs font-bold text-brand-charcoal mb-4 uppercase tracking-tight">Access Control</label>
              <div className="space-y-3">
                <label className="flex items-start space-x-3 cursor-pointer">
                  <input className="mt-1 text-brand-charcoal focus:ring-brand-charcoal" name="db_type" type="radio" defaultChecked />
                  <div>
                    <span className="block text-sm font-bold text-brand-charcoal">Public Database</span>
                    <span className="block text-xs text-brand-grayBody">Visible to all employees</span>
                  </div>
                </label>
                <label className="flex items-start space-x-3 cursor-pointer">
                  <input className="mt-1 text-brand-charcoal focus:ring-brand-charcoal" name="db_type" type="radio" />
                  <div>
                    <span className="block text-sm font-bold text-brand-charcoal">Confidential Database</span>
                    <span className="block text-xs text-brand-grayBody">Managers &amp; Admins only</span>
                  </div>
                </label>
              </div>
            </div>
            <button className="w-full bg-brand-charcoal text-white py-3.5 rounded-full font-bold hover:shadow-lg transition-all active:scale-95">
              Upload &amp; Ingest Document
            </button>
          </div>
        </div>
        
        <div className="lg:col-span-7">
          <div className="border border-brand-border rounded-2xl overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-brand-lightBg text-[10px] uppercase tracking-widest font-bold text-brand-grayBody border-b border-brand-border">
                <tr>
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4">Access</th>
                  <th className="px-6 py-4">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border text-sm">
                <tr className="hover:bg-brand-lightBg/30">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 text-brand-grayBody mr-3" />
                      <span className="font-medium text-brand-charcoal">Employee_Handbook_2024.pdf</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded">Public</span>
                  </td>
                  <td className="px-6 py-4 text-brand-grayBody text-xs">Dec 15, 2024</td>
                </tr>
                <tr className="hover:bg-brand-lightBg/30">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <ShieldCheck className="w-4 h-4 text-brand-grayBody mr-3" />
                      <span className="font-medium text-brand-charcoal">Payroll_Structure_Q4.xlsx</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-bold text-brand-orange bg-orange-50 px-2 py-0.5 rounded">Confidential</span>
                  </td>
                  <td className="px-6 py-4 text-brand-grayBody text-xs">Jan 05, 2025</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Documents;
