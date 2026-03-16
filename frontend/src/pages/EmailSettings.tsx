import { Check } from 'lucide-react';

const EmailSettings = () => {
  return (
    <section className="p-8 md:p-12 max-w-3xl mx-auto animate-in fade-in transition-all">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-brand-charcoal">Email Configuration</h1>
        <p className="text-brand-grayBody mt-2">Configure how your team receives invitations via Gmail.</p>
      </header>
      
      <div className="p-6 bg-green-50 border border-green-100 rounded-2xl flex items-start space-x-4 mb-10">
        <div className="bg-green-600 p-2 rounded-full mt-1">
          <Check className="w-4 h-4 text-white" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-green-800">System Ready</h4>
          <p className="text-xs text-green-700 mt-1 leading-relaxed">Invites are currently being sent from <strong>admin@acme.com</strong> using a secure Google App Password.</p>
        </div>
      </div>

      <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
        <div>
          <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Gmail Address</label>
          <input className="w-full px-4 py-3 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none text-brand-charcoal" type="email" defaultValue="admin@acme.com" />
        </div>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-xs font-bold text-brand-charcoal uppercase tracking-tight">App Password</label>
            <a className="text-[11px] font-bold text-brand-orange hover:underline" href="#">How to generate?</a>
          </div>
          <input className="w-full px-4 py-3 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none text-brand-charcoal" type="password" defaultValue="••••••••••••••••" />
          <p className="text-[11px] text-brand-grayBody mt-2">The 16-character password from Google App Passwords — NOT your normal password.</p>
        </div>
        <div className="pt-4 border-t border-brand-border flex flex-col md:flex-row gap-4">
          <button className="flex-1 bg-brand-charcoal text-white py-3 rounded-full font-bold hover:shadow-lg transition-all" type="submit">Save Changes</button>
          <button className="flex-1 bg-brand-lightBg border border-brand-border text-brand-charcoal py-3 rounded-full font-bold hover:bg-brand-border transition-all" type="button">Send Test Email</button>
        </div>
      </form>
    </section>
  );
};

export default EmailSettings;
