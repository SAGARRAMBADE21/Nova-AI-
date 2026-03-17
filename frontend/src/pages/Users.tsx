import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { listUsers, inviteUser } from '@/lib/api';

interface User {
  email: string;
  role: string;
  status: string;
  invited_at?: string;
}

const roleColors: Record<string, string> = {
  admin:     'bg-red-50 text-red-600',
  manager:   'bg-blue-50 text-blue-600',
  team_lead: 'bg-purple-50 text-purple-600',
  employee:  'bg-gray-100 text-brand-grayBody',
};

const statusColors: Record<string, string> = {
  active:   'bg-green-100 text-green-700',
  invited:  'bg-yellow-100 text-yellow-700',
  inactive: 'bg-gray-100 text-gray-500',
};

const Users = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('employee');
  const [inviting, setInviting] = useState(false);
  const [inviteMsg, setInviteMsg] = useState('');
  const [emailStatus, setEmailStatus] = useState('');

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await listUsers();
      setUsers(data.users as unknown as User[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviting(true);
    setInviteMsg('');
    setEmailStatus('');
    try {
      const res = await inviteUser({ email: inviteEmail, role: inviteRole });
      setInviteMsg(`✓ ${res.message ?? 'Invite created successfully.'}`);
      // Show email delivery status separately
      if (res.invite_email === 'sent') {
        setEmailStatus('📧 Invite email sent successfully.');
      } else if (res.invite_email?.startsWith('skipped')) {
        setEmailStatus('⚠️ Email not sent — Gmail not configured. Go to Email Settings to set it up.');
      } else {
        setEmailStatus(`ℹ️ Email: ${res.invite_email}`);
      }
      setInviteEmail('');
      fetchUsers();
    } catch (err) {
      setInviteMsg(`✕ ${err instanceof Error ? err.message : 'Invite failed'}`);
      setEmailStatus('');
    } finally {
      setInviting(false);
    }
  };

  const filtered = users.filter(u =>
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="flex justify-between items-end mb-10">
        <div>
          <h1 className="text-3xl font-bold text-brand-charcoal">
            Team Members{' '}
            <span className="ml-2 text-sm font-bold bg-brand-lightBg px-3 py-1 rounded-full text-brand-grayBody border border-brand-border">
              {users.length}
            </span>
          </h1>
          <p className="text-brand-grayBody mt-2">Manage user permissions and invite your colleagues.</p>
        </div>
      </header>

      {/* Invite Form */}
      <div className="bg-brand-lightBg p-8 rounded-[24px] border border-brand-border mb-12">
        <h3 className="text-lg font-bold text-brand-charcoal mb-4">Invite New Team Member</h3>
        <form className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end" onSubmit={handleInvite}>
          <div className="md:col-span-5">
            <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Email Address</label>
            <input
              className="w-full px-4 py-2.5 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal focus:border-brand-charcoal outline-none transition-all"
              placeholder="colleague@yourcompany.com"
              type="email"
              required
              value={inviteEmail}
              onChange={e => setInviteEmail(e.target.value)}
            />
          </div>
          <div className="md:col-span-4">
            <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Assign Role</label>
            <select
              className="w-full px-4 py-2.5 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal outline-none transition-all cursor-pointer"
              value={inviteRole}
              onChange={e => setInviteRole(e.target.value)}
            >
              <option value="employee">Employee</option>
              <option value="manager">Manager</option>
              <option value="team_lead">Team Lead</option>
            </select>
          </div>
          <div className="md:col-span-3">
            <button
              className="w-full bg-brand-charcoal text-white py-2.5 px-6 rounded-full font-bold hover:bg-black transition-all disabled:opacity-50"
              type="submit"
              disabled={inviting}
            >
              {inviting ? 'Sending...' : 'Send Invite'}
            </button>
          </div>
        </form>
        {inviteMsg && (
          <p className={`mt-3 text-sm font-semibold ${inviteMsg.startsWith('✓') ? 'text-green-600' : 'text-red-500'}`}>
            {inviteMsg}
          </p>
        )}
        {emailStatus && (
          <p className={`mt-1 text-xs font-medium ${
            emailStatus.startsWith('📧') ? 'text-green-600' :
            emailStatus.startsWith('⚠️') ? 'text-amber-600' : 'text-blue-600'
          }`}>
            {emailStatus}
            {emailStatus.startsWith('⚠️') && (
              <a href="/dashboard/email-settings" className="ml-2 underline font-bold">→ Email Settings</a>
            )}
          </p>
        )}
      </div>

      {/* Users Table */}
      <div className="border border-brand-border rounded-2xl overflow-hidden">
        <div className="p-4 bg-brand-lightBg border-b border-brand-border flex flex-col md:flex-row gap-4 items-center">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-grayBody" />
            <input
              className="pl-10 pr-4 py-2 bg-white border border-brand-border rounded-lg text-sm w-full focus:ring-2 focus:ring-brand-charcoal outline-none"
              placeholder="Search by email..."
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-brand-grayBody">Loading users from MongoDB…</div>
        ) : error ? (
          <div className="p-12 text-center text-red-500">{error}</div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-brand-lightBg text-[10px] uppercase tracking-widest font-bold text-brand-grayBody border-b border-brand-border">
              <tr>
                <th className="px-6 py-4">Email</th>
                <th className="px-6 py-4">Role</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border text-sm">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-10 text-center text-brand-grayBody">No users found.</td>
                </tr>
              ) : filtered.map(u => (
                <tr key={u.email} className="hover:bg-brand-lightBg/30 transition-colors">
                  <td className="px-6 py-4 text-brand-charcoal font-medium">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${roleColors[u.role] ?? 'bg-gray-100 text-gray-600'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold ${statusColors[u.status] ?? 'bg-gray-100 text-gray-500'}`}>
                      {u.status ?? 'active'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
};

export default Users;
