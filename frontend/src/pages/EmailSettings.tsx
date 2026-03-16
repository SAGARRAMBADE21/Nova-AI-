import { useState } from 'react';
import { Check } from 'lucide-react';
import { setEmailConfig } from '@/lib/api';

const EmailSettings = () => {
  const [senderEmail, setSenderEmail] = useState('');
  const [appPassword, setAppPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg('');
    try {
      const res = await setEmailConfig({ sender_email: senderEmail, sender_password: appPassword });
      setMsg(`✓ ${res.message}`);
      setSuccess(true);
    } catch (err) {
      setMsg(`✕ ${err instanceof Error ? err.message : 'Failed to save email config.'}`);
      setSuccess(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="p-8 md:p-12 max-w-3xl mx-auto animate-in fade-in transition-all">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-brand-charcoal">Email Configuration</h1>
        <p className="text-brand-grayBody mt-2">Configure how your team receives invitations via Gmail.</p>
      </header>
      
      {success && (
        <div className="p-6 bg-green-50 border border-green-100 rounded-2xl flex items-start space-x-4 mb-10">
          <div className="bg-green-600 p-2 rounded-full mt-1">
            <Check className="w-4 h-4 text-white" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-green-800">Email Configured!</h4>
            <p className="text-xs text-green-700 mt-1">Invites will now be sent from <strong>{senderEmail}</strong>.</p>
          </div>
        </div>
      )}

      <form className="space-y-6" onSubmit={handleSubmit}>
        <div>
          <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Gmail Address</label>
          <input
            className="w-full px-4 py-3 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none text-brand-charcoal"
            type="email"
            required
            placeholder="admin@yourcompany.com"
            value={senderEmail}
            onChange={e => setSenderEmail(e.target.value)}
          />
        </div>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-xs font-bold text-brand-charcoal uppercase tracking-tight">App Password</label>
            <a
              className="text-[11px] font-bold text-brand-orange hover:underline"
              href="https://myaccount.google.com/apppasswords"
              target="_blank"
              rel="noreferrer"
            >
              How to generate?
            </a>
          </div>
          <input
            className="w-full px-4 py-3 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none text-brand-charcoal"
            type="password"
            required
            placeholder="16-character Google App Password"
            value={appPassword}
            onChange={e => setAppPassword(e.target.value)}
          />
          <p className="text-[11px] text-brand-grayBody mt-2">The 16-character password from Google App Passwords — NOT your normal password.</p>
        </div>

        {msg && (
          <p className={`text-sm font-semibold ${msg.startsWith('✓') ? 'text-green-600' : 'text-red-500'}`}>{msg}</p>
        )}

        <div className="pt-4 border-t border-brand-border flex flex-col md:flex-row gap-4">
          <button
            className="flex-1 bg-brand-charcoal text-white py-3 rounded-full font-bold hover:shadow-lg transition-all disabled:opacity-50"
            type="submit"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </section>
  );
};

export default EmailSettings;
