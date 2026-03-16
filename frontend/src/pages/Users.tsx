import { Search } from 'lucide-react';

const Users = () => {
  return (
    <section className="p-8 md:p-12 max-w-7xl mx-auto animate-in fade-in transition-all">
      <header className="flex justify-between items-end mb-10">
        <div>
          <h1 className="text-3xl font-bold text-brand-charcoal">Team Members <span className="ml-2 text-sm font-bold bg-brand-lightBg px-3 py-1 rounded-full text-brand-grayBody border border-brand-border">42</span></h1>
          <p className="text-brand-grayBody mt-2">Manage user permissions and invite your colleagues.</p>
        </div>
      </header>

      <div className="bg-brand-lightBg p-8 rounded-[24px] border border-brand-border mb-12">
        <h3 className="text-lg font-bold text-brand-charcoal mb-4">Invite New Team Member</h3>
        <form className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end" onSubmit={(e) => e.preventDefault()}>
          <div className="md:col-span-5">
            <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Email Address</label>
            <input className="w-full px-4 py-2.5 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal focus:border-brand-charcoal outline-none transition-all" placeholder="colleague@yourcompany.com" type="email" />
          </div>
          <div className="md:col-span-4">
            <label className="block text-xs font-bold text-brand-charcoal mb-2 uppercase tracking-tight">Assign Role</label>
            <select className="w-full px-4 py-2.5 bg-white border border-brand-border rounded-xl focus:ring-2 focus:ring-brand-charcoal focus:border-brand-charcoal outline-none transition-all cursor-pointer">
              <option>Employee</option>
              <option>Manager</option>
              <option>Team Lead</option>
            </select>
          </div>
          <div className="md:col-span-3">
            <button className="w-full bg-brand-charcoal text-white py-2.5 px-6 rounded-full font-bold hover:bg-black transition-all" type="submit">
              Send Invite
            </button>
          </div>
        </form>
      </div>

      <div className="border border-brand-border rounded-2xl overflow-hidden">
        <div className="p-4 bg-brand-lightBg border-b border-brand-border flex flex-col md:flex-row gap-4 items-center">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-grayBody" />
            <input className="pl-10 pr-4 py-2 bg-white border border-brand-border rounded-lg text-sm w-full focus:ring-2 focus:ring-brand-charcoal outline-none" placeholder="Search by email..." type="text" />
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 text-xs font-bold bg-white border border-brand-border rounded-lg hover:border-brand-charcoal">All Roles</button>
            <button className="px-3 py-1.5 text-xs font-bold bg-white border border-brand-border rounded-lg hover:border-brand-charcoal">Status: All</button>
          </div>
        </div>
        <table className="w-full text-left">
          <thead className="bg-brand-lightBg text-[10px] uppercase tracking-widest font-bold text-brand-grayBody border-b border-brand-border">
            <tr>
              <th className="px-6 py-4">Email</th>
              <th className="px-6 py-4">Role</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Date Added</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-border text-sm">
            <tr className="hover:bg-brand-lightBg/30 transition-colors">
              <td className="px-6 py-4 text-brand-charcoal font-medium">sarah.lee@acme.com</td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-600">Manager</span>
              </td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-green-100 text-green-700">Active</span>
              </td>
              <td className="px-6 py-4 text-brand-grayBody">Jan 12, 2025</td>
              <td className="px-6 py-4 text-right">
                <button className="text-red-500 hover:text-red-700 font-bold">Remove</button>
              </td>
            </tr>
            <tr className="hover:bg-brand-lightBg/30 transition-colors">
              <td className="px-6 py-4 text-brand-charcoal font-medium">dave.jones@acme.com</td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-brand-grayBody">Employee</span>
              </td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-yellow-100 text-yellow-700">Invited</span>
              </td>
              <td className="px-6 py-4 text-brand-grayBody">Feb 01, 2025</td>
              <td className="px-6 py-4 text-right">
                <button className="text-red-500 hover:text-red-700 font-bold">Remove</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default Users;
