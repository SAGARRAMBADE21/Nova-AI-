import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Users, FileText, Mail, BarChart3, 
  MessageSquare, LogOut 
} from 'lucide-react';

const Layout = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("nova_token");
    localStorage.removeItem("nova_role");
    navigate('/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) => 
    `w-full flex items-center px-3 py-2.5 text-sm font-semibold rounded-lg transition-colors group ${
      isActive 
        ? 'sidebar-active' 
        : 'text-brand-grayBody hover:text-brand-charcoal'
    }`;

  return (
    <div className="h-screen flex bg-white font-sans text-brand-grayBody overflow-hidden">
      <style>{`
        .sidebar-active { 
          border-left: 2px solid #FF5925; 
          background-color: #EBEBEB; 
          color: #1A1A1A !important; 
        }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 10px; }
        @keyframes pulse-green {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.7); }
          70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(22, 163, 74, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
        }
        .pulse-dot { animation: pulse-green 2s infinite; }
      `}</style>

      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-brand-lightBg border-r border-brand-border flex flex-col h-full z-30">
        <div className="h-16 flex items-center px-6 border-b border-brand-border cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/')}>
          <span className="text-brand-charcoal font-extrabold text-xl tracking-tight">QueryMind</span>
        </div>
        
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
          <NavLink to="/dashboard/overview" className={navLinkClass}>
            <LayoutDashboard className="mr-3 h-5 w-5" /> Overview
          </NavLink>
          <NavLink to="/dashboard/users" className={navLinkClass}>
            <Users className="mr-3 h-5 w-5" /> Users
          </NavLink>
          <NavLink to="/dashboard/documents" className={navLinkClass}>
            <FileText className="mr-3 h-5 w-5" /> Documents
          </NavLink>
          <NavLink to="/dashboard/email-settings" className={navLinkClass}>
            <Mail className="mr-3 h-5 w-5" /> Email Settings
          </NavLink>
          <NavLink to="/dashboard/metrics" className={navLinkClass}>
            <BarChart3 className="mr-3 h-5 w-5" /> Metrics
          </NavLink>
        </nav>

        <div className="p-4 border-t border-brand-border space-y-4">
          <button className="flex items-center text-sm font-semibold text-brand-orange hover:text-brand-orangeHover px-2 transition-colors" onClick={() => navigate('/chat')}>
            <MessageSquare className="mr-3 h-5 w-5" /> Go to Chat
          </button>
          <div className="flex items-center space-x-3 px-2">
            <div className="h-9 w-9 rounded-full bg-brand-charcoal text-white flex items-center justify-center text-sm font-bold">JD</div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-brand-charcoal truncate">admin@acme.com</p>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-orange-100 text-brand-orange">Admin</span>
            </div>
          </div>
          <button className="w-full text-left flex items-center px-2 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors" onClick={handleLogout}>
            <LogOut className="mr-3 h-5 w-5" /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative custom-scrollbar bg-white">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
