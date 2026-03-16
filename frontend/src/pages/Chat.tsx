import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, LogOut, Settings, X } from 'lucide-react';
import { sendChat } from '@/lib/api';

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

const Chat = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [showConnectors, setShowConnectors] = useState(true);
  const [isConfidential, setIsConfidential] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const userEmail   = localStorage.getItem('nova_email') ?? '';
  const userRole    = localStorage.getItem('nova_role')  ?? 'employee';
  const userCompany = localStorage.getItem('nova_company') ?? 'Your Workspace';
  const initials    = userEmail ? userEmail.slice(0, 2).toUpperCase() : 'ME';

  const activeSession = sessions.find(s => s.id === activeSessionId) ?? null;
  const messages = activeSession?.messages ?? [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const createNewSession = () => {
    const id = crypto.randomUUID();
    const session: Session = {
      id,
      title: 'New Chat',
      messages: [],
      history: [],
      createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setSessions(prev => [session, ...prev]);
    setActiveSessionId(id);
  };

  const handleLogout = () => {
    localStorage.removeItem('nova_token');
    localStorage.removeItem('nova_role');
    localStorage.removeItem('nova_company');
    localStorage.removeItem('nova_email');
    navigate('/login');
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    // Ensure there's an active session
    let sessionId = activeSessionId;
    if (!sessionId) {
      const id = crypto.randomUUID();
      const newSession: Session = {
        id,
        title: input.slice(0, 40),
        messages: [],
        history: [],
        createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(id);
      sessionId = id;
    }

    const prompt = input;
    setInput('');

    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      text: prompt,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const typingId = (Date.now() + 1).toString();
    const typingMsg: Message = {
      id: typingId,
      type: 'assistant',
      text: '',
      time: 'Now',
      isTyping: true,
    };

    // Add user + typing indicator immediately
    setSessions(prev => prev.map(s =>
      s.id === sessionId
        ? {
            ...s,
            title: s.messages.length === 0 ? prompt.slice(0, 40) : s.title,
            messages: [...s.messages, userMsg, typingMsg],
          }
        : s
    ));

    try {
      // Get current history BEFORE adding new turn
      const currentHistory = sessions.find(s => s.id === sessionId)?.history ?? [];

      const result = await sendChat({
        prompt,
        session_id: sessionId,
        history: currentHistory,
      });

      const assistantText = result.response;
      const sources: string[] = result.sources ?? [];

      // Parse confidence from response text
      const confMatch = assistantText.match(/\[conf(?:idence)?:?\s*(HIGH|MEDIUM|LOW)\]/i)
        || assistantText.match(/\*\*Confidence:\*\*\s*\[(HIGH|MEDIUM|LOW)\]/i);
      const confidence = confMatch ? confMatch[1].toUpperCase() : undefined;

      const assistantMsg: Message = {
        id: typingId,
        type: 'assistant',
        text: assistantText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources,
        confidence,
      };

      // Update session with response AND append to history
      setSessions(prev => prev.map(s =>
        s.id === sessionId
          ? {
              ...s,
              messages: s.messages.map(m => m.id === typingId ? assistantMsg : m),
              history: [
                ...s.history,
                { role: 'user', content: prompt },
                { role: 'assistant', content: assistantText },
              ],
            }
          : s
      ));
    } catch (err) {
      const errText = err instanceof Error ? err.message : 'Failed to get response.';
      setSessions(prev => prev.map(s =>
        s.id === sessionId
          ? {
              ...s,
              messages: s.messages.map(m =>
                m.id === typingId
                  ? { ...m, text: `⚠️ ${errText}`, isTyping: false }
                  : m
              ),
            }
          : s
      ));
    }
  };

  const confidenceColor = (c?: string) => {
    if (c === 'HIGH') return 'bg-green-100 text-green-700';
    if (c === 'MEDIUM') return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-600';
  };

  return (
    <div className="flex h-screen w-full font-sans text-brand-grayBody overflow-hidden bg-white">
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 10px; }
        @keyframes dot-pulse { 0%, 100% { opacity: 0.4; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.1); } }
        .dot-loading { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #666; margin: 0 2px; animation: dot-pulse 1.2s infinite ease-in-out; }
        .dot-loading:nth-child(2) { animation-delay: 0.2s; }
        .dot-loading:nth-child(3) { animation-delay: 0.4s; }
      `}</style>

      {/* Sidebar */}
      <aside className="w-72 bg-brand-lightGray border-r border-brand-border flex flex-col h-full z-20">
        <div className="p-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-orange rounded-lg flex items-center justify-center text-white font-bold">Q</div>
            <span className="text-xl font-bold text-brand-charcoal tracking-tight cursor-pointer" onClick={() => navigate('/')}>QueryMind</span>
          </div>
        </div>

        <div className="px-4 mb-6">
          <button
            className="w-full bg-brand-charcoal text-white rounded-full py-3 px-4 flex items-center justify-center gap-2 hover:opacity-90 transition-all font-semibold shadow-sm"
            onClick={createNewSession}
          >
            <Plus size={20} /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 space-y-2 custom-scrollbar">
          <div className="text-[11px] font-bold text-brand-orange uppercase tracking-[0.08em] px-2 mb-2">History</div>
          {sessions.length === 0 ? (
            <p className="text-xs text-gray-400 px-2">No chats yet. Start a new chat above.</p>
          ) : sessions.map(session => (
            <div
              key={session.id}
              className={`group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                session.id === activeSessionId
                  ? 'bg-white border border-brand-border shadow-sm'
                  : 'hover:bg-gray-200/50'
              }`}
              onClick={() => setActiveSessionId(session.id)}
            >
              <div className="flex-1 overflow-hidden">
                <div className="text-sm font-semibold text-brand-charcoal truncate">{session.title}</div>
                <div className="text-xs text-gray-400 mt-1">{session.createdAt}</div>
              </div>
              <button
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
                onClick={(e) => {
                  e.stopPropagation();
                  setSessions(prev => prev.filter(s => s.id !== session.id));
                  if (activeSessionId === session.id) setActiveSessionId(null);
                }}
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-brand-border space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-charcoal text-white flex items-center justify-center font-bold text-sm">{initials}</div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-brand-charcoal truncate">{userEmail || '—'}</div>
              <span className="inline-block px-2 py-0.5 text-[10px] font-bold bg-green-100 text-green-700 rounded-full uppercase tracking-wider">{userRole}</span>
            </div>
          </div>
          <button className="flex items-center gap-2 text-sm font-medium text-brand-charcoal hover:text-brand-orange transition-colors" onClick={() => navigate('/dashboard')}>
            <Settings size={18} /> Admin Dashboard
          </button>
          <button className="w-full flex items-center gap-2 text-sm font-medium text-red-500 hover:text-red-600 transition-colors" onClick={handleLogout}>
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col relative h-full bg-white overflow-hidden">
        <header className="h-16 border-b border-brand-border px-8 flex items-center justify-between bg-white/80 backdrop-blur-md z-10 shrink-0">
          <div>
            <h1 className="text-sm font-bold text-brand-charcoal uppercase tracking-wider">AI ASSISTANT</h1>
            <p className="text-[11px] text-gray-400">{userCompany} Workspace</p>
          </div>
          <div className="flex items-center gap-2 bg-brand-lightGray p-1 rounded-full border border-brand-border">
            <button onClick={() => setIsConfidential(false)} className={`px-3 py-1 text-xs font-semibold rounded-full transition-all ${!isConfidential ? 'bg-white shadow-sm text-brand-charcoal' : 'text-gray-400'}`}>Public</button>
            <button onClick={() => setIsConfidential(true)}  className={`px-3 py-1 text-xs font-semibold rounded-full transition-all ${isConfidential  ? 'bg-white shadow-sm text-brand-charcoal' : 'text-gray-400'}`}>Confidential</button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 space-y-8 pb-48 custom-scrollbar">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-20">
              <h2 className="text-4xl font-extrabold text-brand-charcoal tracking-tight mb-4">What can I help with today?</h2>
              <p className="text-lg text-brand-grayBody">Ask anything about your company's documents, policies, and data.</p>
            </div>
          ) : messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.type === 'user' ? (
                <div className="max-w-[80%] bg-brand-charcoal text-white px-6 py-4 rounded-[24px] rounded-tr-none shadow-sm">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                </div>
              ) : (
                <div className="max-w-[85%] w-full bg-brand-lightGray border border-brand-border rounded-[28px] rounded-tl-none overflow-hidden shadow-sm">
                  <div className="p-6 space-y-4">
                    {msg.isTyping ? (
                      <div className="flex items-center h-5">
                        <span className="dot-loading" /><span className="dot-loading" /><span className="dot-loading" />
                      </div>
                    ) : (
                      <>
                        <div className="space-y-2">
                          <span className="text-[11px] font-bold text-brand-orange uppercase tracking-wider">Answer:</span>
                          <div className="text-brand-charcoal leading-relaxed whitespace-pre-wrap text-sm">{msg.text}</div>
                        </div>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="space-y-2">
                            <span className="text-[11px] font-bold text-brand-orange uppercase tracking-wider">Sources:</span>
                            <div className="flex flex-wrap gap-2">
                              {msg.sources.map((src, i) => (
                                <span key={i} className="bg-white border border-brand-border px-3 py-1.5 rounded-full text-xs font-medium text-brand-charcoal flex items-center gap-1.5">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                  {src}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="flex items-center justify-between pt-3 border-t border-brand-border">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${confidenceColor(msg.confidence)}`}>
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

        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white/90 to-transparent z-10">
          <div className="max-w-4xl mx-auto space-y-4">
            <div className="relative bg-white border-2 border-brand-border rounded-[28px] shadow-lg focus-within:border-brand-charcoal transition-all p-2">
              <textarea
                className="w-full border-0 focus:ring-0 resize-none px-4 py-3 text-brand-charcoal placeholder:text-gray-400 bg-transparent min-h-[56px] max-h-[200px] outline-none"
                placeholder="Ask ARIA anything about your company..."
                rows={1}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              />
              <div className="flex items-center justify-end px-2 pb-2">
                <button
                  className={`p-2.5 rounded-full transition-all ${input.trim() ? 'bg-brand-charcoal text-white hover:bg-black' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                  disabled={!input.trim()}
                  onClick={handleSend}
                >
                  <svg fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24" width="20"><line x1="22" x2="11" y1="2" y2="13"/><polyline points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
              </div>
            </div>

            {showConnectors && (
              <div className="flex items-center justify-between px-4 py-2 bg-brand-lightGray border border-brand-border rounded-2xl animate-in fade-in">
                <div className="flex items-center gap-3">
                  <svg fill="none" height="16" stroke="#FF5925" strokeWidth="2" viewBox="0 0 24 24" width="16"><path d="m18 10 4 4-4 4"/><path d="m6 10-4 4 4 4"/><path d="M12 7v13"/></svg>
                  <span className="text-xs font-semibold text-brand-charcoal">Connect your tools to QueryMind</span>
                </div>
                <button className="text-gray-400 hover:text-brand-charcoal" onClick={() => setShowConnectors(false)}><X size={16} /></button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;
