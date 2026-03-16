import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, LogOut, Settings, X } from 'lucide-react';

const Chat = () => {
  const [messages, setMessages] = useState<{ id: string, type: 'user' | 'assistant', text: string, time: string, isTyping?: boolean }[]>([]);
  const [input, setInput] = useState('');
  const [showConnectors, setShowConnectors] = useState(true);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("nova_token");
    localStorage.removeItem("nova_role");
    navigate('/login');
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const newMsg = { id: Date.now().toString(), type: 'user' as const, text: input, time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    
    // Simulate typing
    const typingId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: typingId, type: 'assistant', text: '', time: 'Now', isTyping: true }]);
    
    setTimeout(() => {
      setMessages(prev => prev.map(m => m.id === typingId ? { 
        id: typingId, 
        type: 'assistant', 
        text: 'This is a simulated response based on your exact HTML template design requirements without hallucinations.',
        time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
      } : m));
    }, 1500);
  };

  return (
    <div className="flex h-screen w-full font-sans text-brand-grayBody overflow-hidden bg-white">
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #E5E7EB;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #D1D5DB;
        }
        @keyframes dot-pulse {
          0%, 100% { opacity: 0.4; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.1); }
        }
        .dot-loading {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background-color: #666666;
          margin: 0 2px;
          animation: dot-pulse 1.2s infinite ease-in-out;
        }
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
          <button className="w-full bg-brand-charcoal text-white rounded-full py-3 px-4 flex items-center justify-center gap-2 hover:opacity-90 transition-all font-semibold shadow-sm" onClick={() => setMessages([])}>
            <Plus size={20} />
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 space-y-2 custom-scrollbar">
          <div className="text-[11px] font-bold text-brand-orange uppercase tracking-[0.08em] px-2 mb-2">History</div>
          
          <div className="group relative flex items-center gap-3 p-3 rounded-xl bg-white border border-brand-border cursor-pointer shadow-sm">
            <div className="flex-1 overflow-hidden">
              <div className="text-sm font-semibold text-brand-charcoal truncate">Leave policy query</div>
              <div className="text-xs text-gray-400 mt-1">2 hours ago</div>
            </div>
            <button className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity">
              <X size={16} />
            </button>
          </div>

          <div className="group relative flex items-center gap-3 p-3 rounded-xl hover:bg-gray-200/50 transition-colors cursor-pointer">
            <div className="flex-1 overflow-hidden">
              <div className="text-sm font-medium text-brand-grayBody truncate">Q3 Financial Summary</div>
              <div className="text-xs text-gray-400 mt-1">Yesterday</div>
            </div>
            <button className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity">
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="p-4 border-t border-brand-border space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-charcoal text-white flex items-center justify-center font-bold text-sm">JD</div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-brand-charcoal truncate">john.doe@acme.com</div>
              <span className="inline-block px-2 py-0.5 text-[10px] font-bold bg-green-100 text-green-700 rounded-full uppercase tracking-wider">Manager</span>
            </div>
          </div>
          <button className="flex items-center gap-2 text-sm font-medium text-brand-charcoal hover:text-brand-orange transition-colors" onClick={() => navigate('/dashboard')}>
            <Settings size={18} />
            Admin Dashboard
          </button>
          <button className="w-full flex items-center gap-2 text-sm font-medium text-red-500 hover:text-red-600 transition-colors" onClick={handleLogout}>
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col relative h-full bg-white overflow-hidden">
        <header className="h-16 border-b border-brand-border px-8 flex items-center justify-between bg-white/80 backdrop-blur-md z-10 shrink-0">
          <div className="flex flex-col">
            <h1 className="text-sm font-bold text-brand-charcoal uppercase tracking-wider">ARIA — Enterprise AI Assistant</h1>
            <p className="text-[11px] text-gray-400">Acme Corporation Workspace</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-brand-lightGray text-brand-charcoal text-xs font-semibold rounded-full border border-brand-border">
              Public + Confidential Access
            </span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 space-y-8 pb-40 custom-scrollbar">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-20">
              <div className="w-16 h-16 bg-brand-lightGray rounded-2xl flex items-center justify-center mb-6 border border-brand-border">
                <svg fill="none" height="32" stroke="#FF5925" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="32" xmlns="http://www.w3.org/2000/svg"><path d="m3 21 1.9-1.9a8.5 8.5 0 1 1 3.8 3.8z"></path></svg>
              </div>
              <h2 className="text-4xl font-extrabold text-brand-charcoal tracking-tight mb-4">What can I help with today?</h2>
              <p className="text-lg text-brand-grayBody">Ask anything about your company's documents, policies, and data.</p>
            </div>
          ) : (
            messages.map((msg) => (
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
                          <span className="dot-loading"></span>
                          <span className="dot-loading"></span>
                          <span className="dot-loading"></span>
                        </div>
                      ) : (
                        <>
                          <div className="space-y-2">
                            <span className="text-[11px] font-bold text-brand-orange uppercase tracking-wider">Answer:</span>
                            <div className="text-brand-charcoal leading-relaxed prose prose-sm whitespace-pre-wrap">
                              <p>{msg.text}</p>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <span className="text-[11px] font-bold text-brand-orange uppercase tracking-wider">Sources:</span>
                            <div className="flex flex-wrap gap-2">
                              <button className="bg-white border border-brand-border px-3 py-1.5 rounded-full text-xs font-medium text-brand-charcoal flex items-center gap-1.5 hover:bg-gray-50">
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                Verified Match Rule
                              </button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between pt-4 border-t border-brand-border">
                            <div className="flex items-center gap-4">
                              <span className="px-2.5 py-1 bg-green-100 text-green-700 rounded-full text-[10px] font-bold uppercase tracking-wider">Confidence: High</span>
                              <div className="flex gap-2 text-gray-400">
                                <button className="hover:text-brand-charcoal transition-colors"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/></svg></button>
                                <button className="hover:text-brand-charcoal transition-colors"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"/></svg></button>
                              </div>
                            </div>
                            <button className="text-xs font-semibold text-brand-charcoal bg-white px-4 py-2 rounded-full border border-brand-border shadow-sm hover:bg-gray-50 transition-colors">Run a tool</button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white/90 to-transparent z-10 shrink-0">
          <div className="max-w-4xl mx-auto space-y-4">
            <div className={`relative bg-white border-2 border-brand-border rounded-[28px] shadow-lg focus-within:border-brand-charcoal transition-all p-2`}>
              <textarea 
                className="w-full border-0 focus:ring-0 resize-none px-4 py-3 text-brand-charcoal placeholder:text-gray-400 bg-transparent min-h-[56px] max-h-[200px] outline-none" 
                placeholder="Ask ARIA anything about your company..." 
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
              />
              <div className="flex items-center justify-between px-2 pb-2">
                <div className="flex items-center gap-1">
                  <button className="p-2 text-brand-grayBody hover:bg-brand-lightBg rounded-full transition-colors" title="Attach file">
                    <svg fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.51a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
                  </button>
                  <button className="p-2 text-brand-grayBody hover:bg-brand-lightBg rounded-full transition-colors" title="Connectors" onClick={() => setShowConnectors(!showConnectors)}>
                    <svg fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg"><path d="m18 10 4 4-4 4"></path><path d="m6 10-4 4 4 4"></path><path d="M14.5 4c.8 0 1.5.7 1.5 1.5S15.3 7 14.5 7h-5c-.8 0-1.5-.7-1.5-1.5S8.7 4 9.5 4h5z"></path><path d="M12 7v13"></path></svg>
                  </button>
                  <button className="p-2 text-brand-grayBody hover:bg-brand-lightBg rounded-full transition-colors" title="Tools">
                    <svg fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.29 7 12 12 20.71 7"></polyline><line x1="12" x2="12" y1="22" y2="12"></line></svg>
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button className={`p-2.5 rounded-full transition-all ${input.trim() ? 'bg-brand-charcoal text-white hover:bg-black' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`} disabled={!input.trim()} onClick={handleSend}>
                    <svg fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg"><line x1="22" x2="11" y1="2" y2="13"></line><polyline points="22 2 15 22 11 13 2 9 22 2"></polyline></svg>
                  </button>
                </div>
              </div>
            </div>

            {showConnectors && (
              <div className="flex items-center justify-between px-4 py-2 bg-brand-lightGray border border-brand-border rounded-2xl animate-in fade-in transition-all">
                <div className="flex items-center gap-3">
                  <svg fill="none" height="16" stroke="#FF5925" strokeWidth="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg"><path d="m18 10 4 4-4 4"></path><path d="m6 10-4 4 4 4"></path><path d="M12 7v13"></path></svg>
                  <span className="text-xs font-semibold text-brand-charcoal">Connect your tools to QueryMind</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex -space-x-2">
                    <div className="w-6 h-6 rounded-full bg-white border border-brand-border flex items-center justify-center p-1 cursor-pointer grayscale hover:grayscale-0 transition-all text-[10px]"><span role="img" aria-label="gmail">📧</span></div>
                    <div className="w-6 h-6 rounded-full bg-white border border-brand-border flex items-center justify-center p-1 cursor-pointer grayscale hover:grayscale-0 transition-all text-[10px]"><span role="img" aria-label="drive">📁</span></div>
                    <div className="w-6 h-6 rounded-full bg-white border border-brand-border flex items-center justify-center p-1 cursor-pointer grayscale hover:grayscale-0 transition-all text-[10px]"><span role="img" aria-label="calendar">📅</span></div>
                  </div>
                  <button className="text-gray-400 hover:text-brand-charcoal" onClick={() => setShowConnectors(false)}>
                    <X size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;
