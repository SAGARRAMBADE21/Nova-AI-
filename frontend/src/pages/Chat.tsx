import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, LogOut, Settings, X, ChevronDown, ChevronUp, Link2, Loader2 } from 'lucide-react';
import { sendChat } from '@/lib/api';

// ── Google brand SVG icons ────────────────────────────────────────────────

const GmailIcon = () => (
  <svg viewBox="0 0 48 48" width="18" height="18"><path fill="#EA4335" d="M6 36V18.5l18 11.25L42 18.5V36a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z"/><path fill="#FBBC04" d="M6 18.5V12l18 11.25z"/><path fill="#34A853" d="M42 12v6.5L24 29.75z"/><path fill="#C5221F" d="M6 12l18 11.25L42 12H8a2 2 0 0 0-2 2z"/></svg>
);
const DriveIcon = () => (
  <svg viewBox="0 0 48 48" width="18" height="18"><path fill="#FFC107" d="M17 6l-12 20h10l12-20z"/><path fill="#1976D2" d="M31 6H17l12 20h14z"/><path fill="#4CAF50" d="M5 26l6 10h26l6-10z"/></svg>
);
const DocsIcon = () => (
  <svg viewBox="0 0 48 48" width="18" height="18"><path fill="#4285F4" d="M30 4H12a2 2 0 0 0-2 2v36a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2V14z"/><path fill="#A8C7FA" d="M30 4v10h10z"/><path fill="white" d="M15 22h18v2H15zm0 5h18v2H15zm0 5h12v2H15z"/></svg>
);
const SheetsIcon = () => (
  <svg viewBox="0 0 48 48" width="18" height="18"><path fill="#0F9D58" d="M30 4H12a2 2 0 0 0-2 2v36a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2V14z"/><path fill="#87CEAC" d="M30 4v10h10z"/><path fill="white" d="M15 20h8v3H15zm10 0h8v3H25zm-10 5h8v3H15zm10 0h8v3H25zm-10 5h8v3H15zm10 0h8v3H25z"/></svg>
);
const CalendarIcon = () => (
  <svg viewBox="0 0 48 48" width="18" height="18"><path fill="#4285F4" d="M38 6h-4V4h-2v2H16V4h-2v2h-4a2 2 0 0 0-2 2v32a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2z"/><path fill="white" d="M10 14h28v4H10z"/><rect fill="white" x="14" y="20" width="6" height="5" rx="1"/><rect fill="white" x="21" y="20" width="6" height="5" rx="1"/><rect fill="white" x="28" y="20" width="6" height="5" rx="1"/><rect fill="white" x="14" y="27" width="6" height="5" rx="1"/><rect fill="white" x="21" y="27" width="6" height="5" rx="1"/><rect fill="#EA4335" x="28" y="27" width="6" height="5" rx="1"/></svg>
);
const MeetIcon = () => (
  <svg viewBox="0 0 48 48" width="18" height="18"><path fill="#00897B" d="M8 14a2 2 0 0 1 2-2h22a2 2 0 0 1 2 2v20a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2z"/><path fill="#00BFA5" d="M34 20l8-6v20l-8-6z"/><circle fill="white" cx="21" cy="20" r="4"/><path fill="white" d="M13 32c0-4.4 3.6-8 8-8s8 3.6 8 8H13z"/></svg>
);

const CONNECTORS = [
  { key: 'gmail',           label: 'Gmail',           Icon: GmailIcon },
  { key: 'google_drive',    label: 'Drive',           Icon: DriveIcon },
  { key: 'google_docs',     label: 'Docs',            Icon: DocsIcon },
  { key: 'google_sheets',   label: 'Sheets',          Icon: SheetsIcon },
  { key: 'google_calendar', label: 'Calendar',        Icon: CalendarIcon },
  { key: 'google_meet',     label: 'Meet',            Icon: MeetIcon },
];

// ── Types ────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  time: string;
  isTyping?: boolean;
  sources?: string[];
  confidence?: string;
}

interface Session {
  id: string;
  title: string;
  messages: Message[];
  history: { role: string; content: string }[];
  createdAt: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001';

const confidenceColor = (c?: string) => {
  if (c === 'HIGH')   return 'bg-green-100 text-green-700';
  if (c === 'MEDIUM') return 'bg-yellow-100 text-yellow-700';
  if (c === 'LOW')    return 'bg-red-100 text-red-700';
  return 'bg-gray-100 text-gray-500';
};

// Lightweight markdown renderer — handles bold, italic, inline code, headers, bullets
const renderMarkdown = (text: string) => {
  const lines = text.split('\n');
  return lines.map((line, i) => {
    // Headers
    if (line.startsWith('### ')) return <h3 key={i} className="font-bold text-sm text-brand-charcoal mt-2 mb-0.5">{line.slice(4)}</h3>;
    if (line.startsWith('## '))  return <h2 key={i} className="font-bold text-base text-brand-charcoal mt-3 mb-1">{line.slice(3)}</h2>;
    if (line.startsWith('# '))   return <h1 key={i} className="font-bold text-lg text-brand-charcoal mt-3 mb-1">{line.slice(2)}</h1>;
    // Bullet points
    if (line.startsWith('- ') || line.startsWith('* ')) {
      return <li key={i} className="ml-4 list-disc text-brand-charcoal text-sm leading-relaxed">{inlineMarkdown(line.slice(2))}</li>;
    }
    if (/^\d+\.\s/.test(line)) {
      return <li key={i} className="ml-4 list-decimal text-brand-charcoal text-sm leading-relaxed">{inlineMarkdown(line.replace(/^\d+\.\s/, ''))}</li>;
    }
    // Horizontal rule
    if (line.startsWith('---')) return <hr key={i} className="border-brand-border my-2" />;
    // Empty line
    if (line.trim() === '') return <div key={i} className="h-1" />;
    // Normal paragraph
    return <p key={i} className="text-brand-charcoal text-sm leading-relaxed">{inlineMarkdown(line)}</p>;
  });
};

const inlineMarkdown = (text: string): React.ReactNode => {
  // Split on bold (**text**), italic (*text*), inline code (`code`)
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-bold text-brand-charcoal">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i} className="italic">{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="bg-gray-100 text-brand-orange px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
    }
    return part;
  });
};

// ── Storage keys (user-scoped local cache only) ──────────────────────────

// IMPORTANT: key is scoped to the logged-in user's email so different users
// on the same browser never share sessions. The source of truth is MongoDB.
const getStorageKey = (email: string) =>
  email ? `nova_chat_sessions_${email}` : 'nova_chat_sessions_guest';
const getActiveKey  = (email: string) =>
  email ? `nova_chat_active_${email}` : 'nova_chat_active_guest';

const Chat = () => {
  const navigate = useNavigate();
  const userEmail   = localStorage.getItem('nova_email')   ?? '';
  const userRole    = localStorage.getItem('nova_role')    ?? 'employee';
  const userCompany = localStorage.getItem('nova_company') ?? 'Your Workspace';
  const token       = localStorage.getItem('nova_token')   ?? '';
  const initials    = userEmail ? userEmail.slice(0, 2).toUpperCase() : 'ME';

  // Wipe the old SHARED localStorage key to prevent data leaks from before this fix
  useEffect(() => {
    localStorage.removeItem('nova_chat_sessions');
    localStorage.removeItem('nova_chat_active_session');
  }, []);

  const SESSIONS_KEY = getStorageKey(userEmail);
  const ACTIVE_KEY   = getActiveKey(userEmail);

  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(
    () => localStorage.getItem(ACTIVE_KEY) ?? null
  );
  const [input, setInput]               = useState('');
  const [isConfidential, setIsConfidential] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Connectors state
  const [connectorsOpen, setConnectorsOpen] = useState(true);
  const [isConnected, setIsConnected]       = useState<boolean | null>(null);
  const [connecting, setConnecting]         = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find(s => s.id === activeSessionId) ?? null;
  const messages      = activeSession?.messages ?? [];

  const getHeaders = useCallback((): Record<string, string> => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token]);

  // ── Load sessions from MongoDB on mount ──────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoadingHistory(true);
      try {
        const res = await fetch(`${BASE}/chat-sessions`, { headers: getHeaders() });
        if (res.ok) {
          const data = await res.json();
          const fetched: Session[] = (data.sessions ?? []).map((s: any) => ({
            id:        s.session_id,
            title:     s.title,
            messages:  s.messages ?? [],
            history:   s.history  ?? [],
            createdAt: s.updated_at ? new Date(s.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
          }));
          setSessions(fetched);
          // Also cache locally per-user
          localStorage.setItem(SESSIONS_KEY, JSON.stringify(fetched));
        } else {
          // Fallback: use per-user local cache if API fails
          const cached = localStorage.getItem(SESSIONS_KEY);
          if (cached) setSessions(JSON.parse(cached));
        }
      } catch {
        const cached = localStorage.getItem(SESSIONS_KEY);
        if (cached) setSessions(JSON.parse(cached));
      } finally {
        setLoadingHistory(false);
      }
    };
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // ── Save a single session to MongoDB ─────────────────────────────────────
  const persistSession = useCallback(async (session: Session) => {
    try {
      await fetch(`${BASE}/chat-sessions`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          session_id: session.id,
          title:      session.title,
          messages:   session.messages,
          history:    session.history,
        }),
      });
    } catch { /* silent — local state is still correct */ }
  }, [getHeaders]);

  // Check Google connection status on mount
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${BASE}/tools/connection-status`, { headers: getHeaders() });
        if (res.ok) { const d = await res.json(); setIsConnected(d.connected); }
      } catch { /* silent */ }
    };
    check();
  }, [getHeaders]);

  // ── Update per-user local cache when sessions change ─────────────────────
  useEffect(() => {
    if (!loadingHistory)
      localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  }, [sessions, SESSIONS_KEY, loadingHistory]);

  useEffect(() => {
    if (activeSessionId) localStorage.setItem(ACTIVE_KEY, activeSessionId);
    else localStorage.removeItem(ACTIVE_KEY);
  }, [activeSessionId, ACTIVE_KEY]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const createNewSession = () => {
    const id = crypto.randomUUID();
    const session: Session = {
      id, title: 'New Chat', messages: [], history: [],
      createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setSessions(prev => [session, ...prev]);
    setActiveSessionId(id);
  };

  const handleLogout = () => {
    // Clear only this user's keys, not others'
    [SESSIONS_KEY, ACTIVE_KEY, 'nova_token','nova_role','nova_company','nova_email'].forEach(k => localStorage.removeItem(k));
    navigate('/login');
  };

  const handleConnectGoogle = async () => {
    setConnecting(true);
    try {
      const res = await fetch(`${BASE}/tools/connect/google`, { headers: getHeaders() });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? 'Error'); }
      const data = await res.json();
      window.location.href = data.auth_url;
    } catch (e) { alert(e instanceof Error ? e.message : 'Failed to connect'); }
    finally { setConnecting(false); }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      const id = crypto.randomUUID();
      const newSession: Session = {
        id, title: input.slice(0, 40), messages: [], history: [],
        createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(id);
      sessionId = id;
    }

    const prompt = input;
    setInput('');

    const userMsg: Message = {
      id: Date.now().toString(), type: 'user', text: prompt,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    const typingId = (Date.now() + 1).toString();
    const typingMsg: Message = { id: typingId, type: 'assistant', text: '', time: 'Now', isTyping: true };

    let currentHistory: { role: string; content: string }[] = [];
    let updatedSession: Session | null = null;
    setSessions(prev => prev.map(s => {
      if (s.id !== sessionId) return s;
      if (s.messages.length === 0 && s.title === 'New Chat') s = { ...s, title: prompt.slice(0, 40) };
      currentHistory = s.history;
      return { ...s, messages: [...s.messages, userMsg, typingMsg] };
    }));

    try {
      const result = await sendChat({
        prompt,
        session_id: sessionId!,
        history: currentHistory,
      });

      const assistantText = result.response;
      const sources: string[] = result.sources ?? [];
      const confMatch = assistantText.match(/\[conf(?:idence)?:?\s*(HIGH|MEDIUM|LOW)]\]/i)
        || assistantText.match(/\*\*Confidence:\*\*\s*\[(HIGH|MEDIUM|LOW)]/i);
      const confidence = confMatch?.[1]?.toUpperCase() ?? 'MEDIUM';
      const cleanText  = assistantText.replace(/\[conf(?:idence)?:?\s*(HIGH|MEDIUM|LOW)]\]/gi, '').trim();

      const newHistory = [
        ...currentHistory,
        { role: 'user',      content: prompt },
        { role: 'assistant', content: assistantText },
      ].slice(-20);

      setSessions(prev => prev.map(s => {
        if (s.id !== sessionId) return s;
        const msgs = s.messages.filter(m => m.id !== typingId);
        const assistantMsg: Message = {
          id: (Date.now() + 2).toString(), type: 'assistant',
          text: cleanText, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          sources, confidence,
        };
        updatedSession = { ...s, messages: [...msgs, assistantMsg], history: newHistory };
        return updatedSession;
      }));

      // Persist to MongoDB after update
      if (updatedSession) persistSession(updatedSession);

    } catch (err) {
      setSessions(prev => prev.map(s => {
        if (s.id !== sessionId) return s;
        const msgs = s.messages.filter(m => m.id !== typingId);
        return { ...s, messages: [...msgs, {
          id: (Date.now() + 2).toString(), type: 'assistant',
          text: 'Sorry, something went wrong. Please try again.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }]};
      }));
    }
  };

  return (
    <div className="h-screen flex bg-white font-sans text-brand-grayBody overflow-hidden">
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 10px; }
        @keyframes blink { 0%,80%,100% { opacity: 0; } 40% { opacity: 1; } }
        .dot-loading { display: inline-block; width: 6px; height: 6px; background: #FF5925; border-radius: 50%; margin: 0 2px; animation: blink 1.4s infinite both; }
        .dot-loading:nth-child(2) { animation-delay: 0.2s; }
        .dot-loading:nth-child(3) { animation-delay: 0.4s; }
      `}</style>

      {/* ── LEFT SIDEBAR ── */}
      <aside className="w-72 flex-shrink-0 bg-[#F7F7F5] border-r border-brand-border flex flex-col h-full">

        {/* Logo */}
        <div className="h-14 flex items-center px-5 border-b border-brand-border">
          <span className="text-brand-charcoal font-extrabold text-lg tracking-tight">QueryMind</span>
          <span className="ml-2 text-[10px] font-bold text-brand-orange bg-orange-50 px-1.5 py-0.5 rounded-full uppercase">AI</span>
        </div>

        {/* New Chat */}
        <div className="px-4 py-3">
          <button
            className="w-full bg-brand-charcoal text-white rounded-full py-2.5 px-4 flex items-center justify-center gap-2 hover:opacity-90 transition-all font-semibold shadow-sm text-sm"
            onClick={createNewSession}
          >
            <Plus size={16} /> New Chat
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-3 custom-scrollbar">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-2 py-2">Chats</div>
          {loadingHistory ? (
            <p className="text-xs text-gray-400 px-2 flex items-center gap-1"><Loader2 size={11} className="animate-spin" /> Loading chats...</p>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-gray-400 px-2">No chats yet.</p>
          ) : sessions.map(session => (
            <div
              key={session.id}
              className={`group relative flex items-center gap-2 p-2.5 rounded-xl cursor-pointer transition-colors mb-1 ${
                session.id === activeSessionId ? 'bg-white border border-brand-border shadow-sm' : 'hover:bg-gray-200/50'
              }`}
              onClick={() => setActiveSessionId(session.id)}
            >
              <div className="flex-1 overflow-hidden">
                <div className="text-xs font-semibold text-brand-charcoal truncate">{session.title}</div>
                <div className="text-[10px] text-gray-400">{session.createdAt}</div>
              </div>
              <button
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity shrink-0"
                onClick={async e => {
                  e.stopPropagation();
                  // Delete from MongoDB
                  try {
                    await fetch(`${BASE}/chat-sessions/${session.id}`, {
                      method: 'DELETE', headers: getHeaders()
                    });
                  } catch { /* silent */ }
                  setSessions(prev => prev.filter(s => s.id !== session.id));
                  if (activeSessionId === session.id) setActiveSessionId(null);
                }}
              >
                <X size={13} />
              </button>
            </div>
          ))}
        </div>

        {/* ── CONNECTORS PANEL (Manus-style) ── */}
        <div className="border-t border-brand-border">
          <button
            className="w-full flex items-center justify-between px-4 py-3 text-xs font-bold text-brand-charcoal uppercase tracking-widest hover:bg-gray-100 transition-colors"
            onClick={() => setConnectorsOpen(o => !o)}
          >
            <div className="flex items-center gap-2">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#FF5925" strokeWidth="2.5"><path d="m18 10 4 4-4 4"/><path d="m6 10-4 4 4 4"/><path d="M12 7v13"/></svg>
              Connectors
            </div>
            {connectorsOpen ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
          </button>

          {connectorsOpen && (
            <div className="px-3 pb-3 space-y-0.5">
              {/* Connection status row */}
              <div className="flex items-center justify-between px-2 py-2 mb-1">
                <span className="text-[10px] text-gray-500 font-medium">Google Workspace</span>
                {isConnected === null ? (
                  <span className="text-[10px] text-gray-400">Checking...</span>
                ) : isConnected ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-green-600">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full inline-block" /> Connected
                  </span>
                ) : (
                  <button
                    className="flex items-center gap-1 text-[10px] font-bold text-blue-600 hover:text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full transition-all disabled:opacity-50"
                    onClick={handleConnectGoogle}
                    disabled={connecting}
                  >
                    {connecting ? <Loader2 size={9} className="animate-spin" /> : <Link2 size={9} />}
                    Connect
                  </button>
                )}
              </div>

              {/* Tool icons grid */}
              <div className="grid grid-cols-3 gap-1.5">
                {CONNECTORS.map(({ key, label, Icon }) => (
                  <div
                    key={key}
                    className={`flex flex-col items-center gap-1 p-2 rounded-xl border transition-all cursor-default ${
                      isConnected
                        ? 'bg-white border-brand-border shadow-sm'
                        : 'bg-gray-50 border-gray-100 opacity-40 grayscale'
                    }`}
                    title={isConnected ? `${label} — Active` : `${label} — Connect Google Workspace to enable`}
                  >
                    <Icon />
                    <span className="text-[9px] font-semibold text-brand-charcoal">{label}</span>
                  </div>
                ))}
              </div>

              {!isConnected && (
                <p className="text-[9px] text-gray-400 text-center pt-1">Connect to enable Google tools</p>
              )}
            </div>
          )}
        </div>

        {/* User footer */}
        <div className="p-3 border-t border-brand-border space-y-2">
          <div className="flex items-center gap-2.5 px-1">
            <div className="w-8 h-8 rounded-full bg-brand-charcoal text-white flex items-center justify-center font-bold text-xs shrink-0">{initials}</div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-brand-charcoal truncate">{userEmail || '—'}</div>
              <span className="inline-block px-1.5 py-0.5 text-[9px] font-bold bg-green-100 text-green-700 rounded-full uppercase">{userRole}</span>
            </div>
          </div>
          <div className="flex gap-1">
            {userRole === 'admin' && (
              <button className="flex-1 flex items-center justify-center gap-1.5 text-[11px] font-medium text-brand-charcoal hover:text-brand-orange transition-colors py-1.5 rounded-lg hover:bg-white" onClick={() => navigate('/dashboard')}>
                <Settings size={13} /> Dashboard
              </button>
            )}
            <button className="flex-1 flex items-center justify-center gap-1.5 text-[11px] font-medium text-red-500 hover:text-red-600 transition-colors py-1.5 rounded-lg hover:bg-red-50" onClick={handleLogout}>
              <LogOut size={13} /> Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* ── MAIN CHAT AREA ── */}
      <main className="flex-1 flex flex-col relative h-full bg-white overflow-hidden">
        {/* Header */}
        <header className="h-14 border-b border-brand-border px-6 flex items-center justify-between bg-white z-10 shrink-0">
          <div>
            <h1 className="text-sm font-bold text-brand-charcoal">AI ASSISTANT</h1>
            <p className="text-[10px] text-gray-400">{userCompany}</p>
          </div>
          {userRole !== 'employee' && (
            <div className="flex items-center gap-1.5 bg-gray-100 p-1 rounded-full border border-brand-border">
              <button onClick={() => setIsConfidential(false)} className={`px-3 py-1 text-[11px] font-semibold rounded-full transition-all ${!isConfidential ? 'bg-white shadow-sm text-brand-charcoal' : 'text-gray-400'}`}>Public</button>
              <button onClick={() => setIsConfidential(true)}  className={`px-3 py-1 text-[11px] font-semibold rounded-full transition-all ${ isConfidential ? 'bg-white shadow-sm text-brand-charcoal' : 'text-gray-400'}`}>Confidential</button>
            </div>
          )}

        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 pb-44 custom-scrollbar">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-20">
              <h2 className="text-4xl font-extrabold text-brand-charcoal tracking-tight mb-4">What can I help with?</h2>
              <p className="text-brand-grayBody text-base">Ask anything about your company's documents, policies, or data.</p>
              {isConnected && (
                <div className="mt-6 flex items-center gap-2 text-xs text-green-600 bg-green-50 border border-green-200 rounded-full px-4 py-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full" />
                  Google Workspace connected — I can access Gmail, Drive, Docs, Sheets, Calendar & Meet
                </div>
              )}
            </div>
          ) : messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.type === 'user' ? (
                <div className="max-w-[80%] bg-brand-charcoal text-white px-5 py-3.5 rounded-[20px] rounded-tr-none shadow-sm">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                </div>
              ) : (
                <div className="max-w-[85%] w-full bg-[#F7F7F5] border border-brand-border rounded-[24px] rounded-tl-none overflow-hidden shadow-sm">
                  <div className="p-5 space-y-3">
                    {msg.isTyping ? (
                      <div className="flex items-center h-5">
                        <span className="dot-loading" /><span className="dot-loading" /><span className="dot-loading" />
                      </div>
                    ) : (
                      <>
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-bold text-brand-orange uppercase tracking-wider">Answer</span>
                          <div className="text-brand-charcoal leading-relaxed text-sm space-y-0.5">{renderMarkdown(msg.text)}</div>
                        </div>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="space-y-1.5">
                            <span className="text-[10px] font-bold text-brand-orange uppercase tracking-wider">Sources</span>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.sources.map((src, i) => (
                                <span key={i} className="bg-white border border-brand-border px-2.5 py-1 rounded-full text-[11px] font-medium text-brand-charcoal flex items-center gap-1">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                  {src}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="flex items-center pt-2 border-t border-brand-border/50">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${confidenceColor(msg.confidence)}`}>
                            Confidence: {msg.confidence ?? 'N/A'}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="absolute bottom-0 left-0 right-0 p-5 bg-gradient-to-t from-white via-white/95 to-transparent z-10">
          <div className="max-w-3xl mx-auto">
            <div className="relative bg-white border-2 border-brand-border rounded-[24px] shadow-lg focus-within:border-brand-charcoal transition-all p-2">
              <textarea
                className="w-full border-0 focus:ring-0 resize-none px-4 py-3 placeholder:text-gray-400 bg-transparent min-h-[52px] max-h-[180px] outline-none text-sm"
                style={{ color: '#1A1A1A', caretColor: '#1A1A1A' }}
                placeholder={isConnected ? "Ask ARIA anything — or ask it to search Gmail, Drive, Docs..." : "Ask ARIA anything about your company..."}
                rows={1}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              />
              <div className="flex items-center justify-between px-2 pb-1.5">
                {/* Active connectors mini-row */}
                {isConnected && (
                  <div className="flex items-center gap-1">
                    {CONNECTORS.map(({ key, Icon }) => (
                      <div key={key} className="w-5 h-5 flex items-center justify-center rounded opacity-70 hover:opacity-100 transition-opacity" title={key}>
                        <Icon />
                      </div>
                    ))}
                  </div>
                )}
                {!isConnected && <div />}
                <button
                  className={`p-2 rounded-full transition-all ${input.trim() ? 'bg-brand-charcoal text-white hover:bg-black' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                  disabled={!input.trim()}
                  onClick={handleSend}
                >
                  <svg fill="none" height="18" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24" width="18"><line x1="22" x2="11" y1="2" y2="13"/><polyline points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;
