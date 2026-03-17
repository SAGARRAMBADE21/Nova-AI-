import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Zap, CheckCircle, XCircle, Loader2, Play, Link2, RefreshCw } from 'lucide-react';

// ── Official Google brand SVG icons ──────────────────────────────────────

const GmailIcon = () => (
  <svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <path fill="#EA4335" d="M6 36V18.5l18 11.25L42 18.5V36a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z"/>
    <path fill="#FBBC04" d="M6 18.5V12l18 11.25z"/>
    <path fill="#34A853" d="M42 12v6.5L24 29.75z"/>
    <path fill="#C5221F" d="M6 12l18 11.25L42 12H8a2 2 0 0 0-2 2z"/>
    <path fill="#4285F4" d="M6 12v.01L24 23.25 42 12.01V12H6z" opacity=".2"/>
  </svg>
);

const DriveIcon = () => (
  <svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <path fill="#FFC107" d="M17 6l-12 20h10l12-20z"/>
    <path fill="#1976D2" d="M31 6H17l12 20h14z"/>
    <path fill="#4CAF50" d="M5 26l6 10h26l6-10z"/>
  </svg>
);

const DocsIcon = () => (
  <svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <path fill="#4285F4" d="M30 4H12a2 2 0 0 0-2 2v36a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2V14z"/>
    <path fill="#A8C7FA" d="M30 4v10h10z"/>
    <path fill="white" d="M15 22h18v2H15zm0 5h18v2H15zm0 5h12v2H15z"/>
  </svg>
);

const SheetsIcon = () => (
  <svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <path fill="#0F9D58" d="M30 4H12a2 2 0 0 0-2 2v36a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2V14z"/>
    <path fill="#87CEAC" d="M30 4v10h10z"/>
    <path fill="white" d="M15 20h8v3H15zm10 0h8v3H25zm-10 5h8v3H15zm10 0h8v3H25zm-10 5h8v3H15zm10 0h8v3H25zm-10 5h8v3H15zm10 0h8v3H25z"/>
  </svg>
);

const CalendarIcon = () => (
  <svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <path fill="#4285F4" d="M38 6h-4V4h-2v2H16V4h-2v2h-4a2 2 0 0 0-2 2v32a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2z"/>
    <path fill="white" d="M10 14h28v4H10z"/>
    <path fill="white" d="M10 14h28v26H10z" opacity=".1"/>
    <rect fill="white" x="14" y="20" width="6" height="5" rx="1"/>
    <rect fill="white" x="21" y="20" width="6" height="5" rx="1"/>
    <rect fill="white" x="28" y="20" width="6" height="5" rx="1"/>
    <rect fill="white" x="14" y="27" width="6" height="5" rx="1"/>
    <rect fill="white" x="21" y="27" width="6" height="5" rx="1"/>
    <rect fill="#EA4335" x="28" y="27" width="6" height="5" rx="1"/>
  </svg>
);

const MeetIcon = () => (
  <svg viewBox="0 0 48 48" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
    <path fill="#00897B" d="M8 14a2 2 0 0 1 2-2h22a2 2 0 0 1 2 2v20a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2z"/>
    <path fill="#00BFA5" d="M34 20l8-6v20l-8-6z"/>
    <circle fill="white" cx="21" cy="20" r="4"/>
    <path fill="white" d="M13 32c0-4.4 3.6-8 8-8s8 3.6 8 8H13z"/>
  </svg>
);

const WorkspaceLogo = () => (
  <svg viewBox="0 0 48 48" width="40" height="40" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" rx="10" fill="#4285F4"/>
    <path fill="white" d="M24 10c-7.7 0-14 6.3-14 14s6.3 14 14 14 14-6.3 14-14S31.7 10 24 10zm0 24c-5.5 0-10-4.5-10-10S18.5 14 24 14s10 4.5 10 10-4.5 10-10 10zm0-16c-3.3 0-6 2.7-6 6s2.7 6 6 6 6-2.7 6-6-2.7-6-6-6z"/>
  </svg>
);

// ── Tool metadata ─────────────────────────────────────────────────────────

interface ToolMeta { IconComponent: React.FC; label: string; bg: string; accent: string }

const toolMeta: Record<string, ToolMeta> = {
  gmail:           { IconComponent: GmailIcon,    label: 'Gmail',           bg: 'bg-red-50',    accent: 'border-red-200' },
  google_drive:    { IconComponent: DriveIcon,    label: 'Google Drive',    bg: 'bg-blue-50',   accent: 'border-blue-200' },
  google_docs:     { IconComponent: DocsIcon,     label: 'Google Docs',     bg: 'bg-indigo-50', accent: 'border-indigo-200' },
  google_sheets:   { IconComponent: SheetsIcon,   label: 'Google Sheets',   bg: 'bg-green-50',  accent: 'border-green-200' },
  google_calendar: { IconComponent: CalendarIcon, label: 'Google Calendar', bg: 'bg-amber-50',  accent: 'border-amber-200' },
  google_meet:     { IconComponent: MeetIcon,     label: 'Google Meet',     bg: 'bg-teal-50',   accent: 'border-teal-200' },
};

// ── Types ─────────────────────────────────────────────────────────────────

interface ToolAction { name: string; description: string }
interface Tool       { plugin: string; actions: ToolAction[] }
interface HealthStatus { [key: string]: string }

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

// ── Component ─────────────────────────────────────────────────────────────

const Tools = () => {
  const [searchParams] = useSearchParams();
  const [tools, setTools]           = useState<Tool[]>([]);
  const [health, setHealth]         = useState<HealthStatus>({});
  const [loading, setLoading]       = useState(true);
  const [healthLoading, setHealthLoading]   = useState(false);
  const [connectLoading, setConnectLoading] = useState(false);
  const [isConnected, setIsConnected]       = useState<boolean | null>(null);
  const [error, setError]           = useState('');
  const [executing, setExecuting]   = useState<string | null>(null);
  const [execResult, setExecResult] = useState<Record<string, { success: boolean; message: string }>>({});
  const [successBanner, setSuccessBanner] = useState(false);

  const getHeaders = useCallback((): Record<string, string> => {
    const token = localStorage.getItem('nova_token') ?? '';
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  }, []);

  const checkConnectionStatus = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/tools/connection-status`, { headers: getHeaders() });
      if (res.ok) { const d = await res.json(); setIsConnected(d.connected); }
    } catch { /* silent */ }
  }, [getHeaders]);

  useEffect(() => {
    if (searchParams.get('connected') === '1') {
      setSuccessBanner(true);
      setTimeout(() => setSuccessBanner(false), 6000);
    }
    const fetchTools = async () => {
      try {
        const res = await fetch(`${BASE}/tools`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to load tools');
        const data = await res.json();
        setTools(data.tools ?? []);
      } catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
      finally     { setLoading(false); }
    };
    fetchTools();
    checkConnectionStatus();
  }, [getHeaders, checkConnectionStatus, searchParams]);

  const handleConnectGoogle = async () => {
    setConnectLoading(true);
    try {
      const res = await fetch(`${BASE}/tools/connect/google`, { headers: getHeaders() });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? 'Error'); }
      const data = await res.json();
      window.location.href = data.auth_url;
    } catch (e) { alert(e instanceof Error ? e.message : 'Failed'); }
    finally     { setConnectLoading(false); }
  };

  const handleDisconnect = async () => {
    if (!confirm('Disconnect Google Workspace?')) return;
    setConnectLoading(true);
    try {
      const res = await fetch(`${BASE}/tools/disconnect/google`, {
        method: 'POST',
        headers: getHeaders(),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail ?? 'Failed to disconnect');
      await checkConnectionStatus();
      alert('Google Workspace disconnected.');
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to disconnect');
    } finally {
      setConnectLoading(false);
    }
  };

  const checkHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await fetch(`${BASE}/tools/health`, { headers: getHeaders() });
      if (!res.ok) throw new Error('Permission denied');
      const data = await res.json();
      setHealth(data.health ?? {});
    } catch (e) { alert(e instanceof Error ? e.message : 'Health check failed'); }
    finally     { setHealthLoading(false); }
  };

  const executeAction = async (plugin: string, action: string) => {
    const key = `${plugin}.${action}`;
    setExecuting(key);
    try {
      const res = await fetch(`${BASE}/tools/execute`, {
        method: 'POST', headers: getHeaders(),
        body: JSON.stringify({ plugin, action, params: {} }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? 'Execution failed');
      setExecResult(prev => ({ ...prev, [key]: { success: data.success, message: data.message } }));
    } catch (e) {
      setExecResult(prev => ({ ...prev, [key]: { success: false, message: e instanceof Error ? e.message : 'Failed' } }));
    } finally { setExecuting(null); }
  };

  const healthBadge = (name: string) => {
    const s = health[name];
    if (!s) return null;
    return s === 'healthy'
      ? <span className="flex items-center gap-1 text-green-600 text-[10px] font-bold"><CheckCircle size={11}/> Healthy</span>
      : <span className="flex items-center gap-1 text-red-500 text-[10px] font-bold"><XCircle size={11}/> {s}</span>;
  };

  return (
    <section className="p-8 md:p-10 max-w-7xl mx-auto">

      {/* OAuth success banner */}
      {successBanner && (
        <div className="mb-6 flex items-center gap-3 p-4 bg-green-50 border border-green-300 rounded-2xl text-green-800 font-semibold text-sm">
          <CheckCircle size={20} className="text-green-600 shrink-0" />
          🎉 Google Workspace connected successfully! All tools are now active.
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-brand-charcoal flex items-center gap-3">
            <Zap className="text-brand-orange" size={24} /> Integrations & Tools
          </h1>
          <p className="text-brand-grayBody mt-1 text-sm">Manage your Google Workspace integrations.</p>
        </div>
        <button
          className="flex items-center gap-2 bg-white border border-brand-border text-brand-charcoal py-2 px-4 rounded-full font-semibold hover:bg-gray-50 text-sm transition-all disabled:opacity-50"
          onClick={checkHealth} disabled={healthLoading}
        >
          {healthLoading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
          Health Check
        </button>
      </div>

      {/* ── Google Workspace Connect Card ── */}
      <div className={`mb-8 p-6 rounded-2xl border-2 flex flex-col sm:flex-row items-start sm:items-center gap-5 transition-all ${
        isConnected ? 'bg-green-50 border-green-300' : 'bg-gradient-to-br from-slate-50 to-blue-50 border-blue-200'
      }`}>
        {/* Google G icon cluster */}
        <div className="flex items-center shrink-0">
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 flex items-center justify-center">
              <WorkspaceLogo />
            </div>
            {/* Orbiting mini-icons */}
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-white rounded-full shadow-sm flex items-center justify-center">
              <svg viewBox="0 0 12 12" width="12" height="12"><circle cx="6" cy="6" r="6" fill="#EA4335"/></svg>
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-white rounded-full shadow-sm flex items-center justify-center">
              <svg viewBox="0 0 12 12" width="12" height="12"><circle cx="6" cy="6" r="6" fill="#0F9D58"/></svg>
            </div>
          </div>
        </div>

        <div className="flex-1">
          <h2 className="text-base font-bold text-brand-charcoal">
            {isConnected ? '✅ Google Workspace Connected' : 'Connect Google Workspace'}
          </h2>
          <p className="text-sm text-brand-grayBody mt-1">
            {isConnected
              ? 'Gmail, Drive, Docs, Sheets, Calendar and Meet are active and ready.'
              : 'Authorise Nova AI to access your Google Workspace apps in one click.'}
          </p>
          {/* Mini icon row */}
          <div className="flex items-center gap-2 mt-3">
            {[GmailIcon, DriveIcon, DocsIcon, SheetsIcon, CalendarIcon, MeetIcon].map((Icon, i) => (
              <div key={i} className={`w-7 h-7 bg-white rounded-lg shadow-sm border border-gray-100 flex items-center justify-center transition-all ${isConnected ? 'opacity-100' : 'opacity-50 grayscale'}`}>
                <Icon />
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-2 shrink-0 flex-wrap">
          {isConnected ? (
            <>
              <button
                className="flex items-center gap-2 bg-white border border-green-300 text-green-700 py-2 px-4 rounded-full font-bold text-sm hover:bg-green-50 transition-all"
                onClick={checkConnectionStatus}
              >
                <RefreshCw size={13} /> Refresh
              </button>
              <button
                className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-500 py-2 px-4 rounded-full font-bold text-sm hover:bg-red-100 transition-all disabled:opacity-50"
                onClick={handleDisconnect}
                disabled={connectLoading}
              >
                Disconnect
              </button>
            </>
          ) : (
            <button
              className="flex items-center gap-2 bg-[#4285F4] text-white py-2.5 px-6 rounded-full font-bold text-sm hover:bg-blue-600 transition-all shadow-md disabled:opacity-50"
              onClick={handleConnectGoogle} disabled={connectLoading}
            >
              {connectLoading
                ? <><Loader2 size={14} className="animate-spin" /> Redirecting...</>
                : <><Link2 size={14} /> Connect Google Workspace</>
              }
            </button>
          )}
        </div>
      </div>

      {/* ── Plugin Cards Grid ── */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-brand-grayBody text-sm">
          <Loader2 className="animate-spin mr-3" size={18} /> Loading plugins...
        </div>
      ) : error ? (
        <div className="p-8 text-center text-red-500 text-sm">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {tools.map((tool) => {
            const meta = toolMeta[tool.plugin];
            const IconComp = meta?.IconComponent;
            return (
              <div key={tool.plugin} className="bg-white border border-brand-border rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5">
                {/* Card header with gradient */}
                <div className={`p-5 border-b border-brand-border flex items-center justify-between ${meta?.bg ?? 'bg-gray-50'} ${meta?.accent ?? 'border-gray-200'}`}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center border border-white/80">
                      {IconComp ? <IconComp /> : <span className="text-xl">🔧</span>}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-brand-charcoal">{meta?.label ?? tool.plugin.replace(/_/g, ' ')}</h3>
                      <p className="text-[11px] text-brand-grayBody">{tool.actions?.length ?? 0} actions</p>
                    </div>
                  </div>
                  {healthBadge(tool.plugin) || (
                    isConnected
                      ? <span className="text-[10px] font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">● Live</span>
                      : <span className="text-[10px] font-bold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">○ Offline</span>
                  )}
                </div>

                {/* Actions list */}
                <div className="p-4 space-y-1">
                  {(tool.actions ?? []).length === 0 ? (
                    <p className="text-xs text-gray-400 py-2">No actions available.</p>
                  ) : (tool.actions ?? []).slice(0, 5).map((action) => {
                    const key = `${tool.plugin}.${action.name}`;
                    const result = execResult[key];
                    return (
                      <div key={action.name} className="flex items-center justify-between py-1.5 border-b border-brand-border/30 last:border-0">
                        <div className="flex-1 min-w-0 mr-3">
                          <p className="text-xs font-semibold text-brand-charcoal capitalize">{action.name.replace(/_/g, ' ')}</p>
                          {result && (
                            <p className={`text-[10px] mt-0.5 ${result.success ? 'text-green-600' : 'text-red-500'}`}>
                              {result.success ? '✓' : '✗'} {result.message}
                            </p>
                          )}
                        </div>
                        <button
                          className="flex items-center gap-1 text-[10px] font-bold bg-brand-charcoal text-white px-3 py-1.5 rounded-full hover:bg-black transition-all disabled:opacity-30 shrink-0"
                          onClick={() => executeAction(tool.plugin, action.name)}
                          disabled={executing === key || !isConnected}
                          title={!isConnected ? 'Connect Google Workspace first' : `Run ${action.name}`}
                        >
                          {executing === key ? <Loader2 size={10} className="animate-spin" /> : <Play size={10} />}
                          Run
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Setup guide — only when not connected */}
      {!isConnected && (
        <div className="mt-8 p-6 bg-amber-50 border border-amber-200 rounded-2xl">
          <h3 className="text-sm font-bold text-amber-800 mb-2">🔑 How to set up Google Workspace OAuth</h3>
          <ol className="text-xs text-amber-700 space-y-1.5 list-decimal list-inside">
            <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" className="underline font-bold">Google Cloud Console</a> and create or select a project</li>
            <li>Enable: Gmail API, Drive API, Docs API, Sheets API, Calendar API</li>
            <li>Go to <b>APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID</b></li>
            <li>Add redirect URI: <code className="bg-amber-100 px-1 rounded">http://localhost:8000/tools/callback/google</code></li>
            <li>Download JSON → save as <code className="bg-amber-100 px-1 rounded">enterprise_ai/credentials/google_credentials.json</code></li>
            <li>Click <b>Connect Google Workspace</b> above</li>
          </ol>
        </div>
      )}
    </section>
  );
};

export default Tools;
