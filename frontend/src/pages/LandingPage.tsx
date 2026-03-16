import { useState } from 'react';
import * as Sortable from "@/components/ui/sortable";
import { useNavigate } from 'react-router-dom';
import { joinWorkspace } from '@/lib/api';

const LandingPage = () => {
  const [capabilities, setCapabilities] = useState([
    {
      id: "rbac",
      title: "Role-Based Access Control",
      desc: "4 roles: Employee, Team Lead, Manager, Admin. Every answer is scoped to what the user is permitted to read.",
      icon: <svg className="w-4 h-4 text-[#FF5925]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
    },
    {
      id: "trained",
      title: "Trained on Your Documents",
      desc: "Upload PDF, DOCX, XLSX, and more. Vectorized indexing ensures ARIA only answers from your company's data.",
      icon: <svg className="w-4 h-4 text-[#FF5925]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
    },
    {
      id: "google",
      title: "Google Workspace Integrations",
      desc: "Send emails via Gmail, create Calendar events, and update Sheets—all from one chat interface.",
      icon: <svg className="w-4 h-4 text-[#FF5925]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
    },
    {
      id: "lakera",
      title: "3-Layer Lakera Guard",
      desc: "Industry-standard security scans user inputs, retrieved docs, and AI outputs to prevent prompt injections.",
      icon: <svg className="w-4 h-4 text-[#FF5925]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
    },
    {
      id: "hitl",
      title: "Human-in-the-Loop",
      desc: "High-risk queries are paused and escalated automatically to Leads or Managers for a 30-minute SLA review.",
      icon: <svg className="w-4 h-4 text-[#FF5925]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
    },
    {
      id: "llmops",
      title: "Admin LLMOps Metrics",
      desc: "Track queries, token usage, security blocks, and response latency through a comprehensive dashboard.",
      icon: <svg className="w-4 h-4 text-[#FF5925]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
    }
  ]);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loginForm, setLoginForm] = useState({ join_code: '', email: '', password: '' });
  const navigate = useNavigate();

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError('');

    try {
      const result = await joinWorkspace({
        join_code: loginForm.join_code.trim().toUpperCase(),
        email:     loginForm.email.trim().toLowerCase(),
        password:  loginForm.password,
      });
      localStorage.setItem('nova_token',   result.token);
      localStorage.setItem('nova_role',    result.role);
      localStorage.setItem('nova_company', result.company_name);
      navigate('/dashboard');
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Login failed.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <>
      <style>{`
        .hero-heading {
          font-size: clamp(2.5rem, 5vw, 4rem);
          line-height: 1.1;
          font-weight: 800;
          color: #1A1A1A;
        }
        .section-label {
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #FF5925;
        }
        .glass-nav {
          background: rgba(255, 255, 255, 0.92);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid #E5E7EB;
        }
        .ribbon-top-right {
          position: absolute;
          top: -50px;
          right: -100px;
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, rgba(255,89,37,0.15) 0%, rgba(255,179,71,0.05) 100%);
          filter: blur(60px);
          z-index: -1;
          border-radius: 50%;
          transform: rotate(-15deg);
        }
        .ribbon-decoration {
          background: linear-gradient(135deg, #FF5925 0%, #FFB347 100%);
          opacity: 0.1;
          filter: blur(40px);
          border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
        }
        .browser-mockup {
          box-shadow: 0 8px 48px rgba(0,0,0,0.10);
          border: 1px solid #E5E7EB;
        }
        .login-dropdown {
          transform-origin: top;
          animation: slideDown 0.2s ease-out forwards;
        }
        @keyframes slideDown {
          from { transform: scaleY(0); opacity: 0; }
          to { transform: scaleY(1); opacity: 1; }
        }
        .card-hover:hover {
          transform: translateY(-4px);
          box-shadow: 0 4px 20px rgba(0,0,0,0.08);
          transition: all 0.3s ease;
        }
      `}</style>

      {/* BEGIN: Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-nav h-16 flex items-center">
        <div className="max-w-7xl mx-auto px-6 w-full flex justify-between items-center">
          {/* Logo */}
          <a className="text-brand-charcoal font-extrabold text-xl tracking-tight" href="#hero">QueryMind</a>
          
          {/* Nav Links */}
          <div className="hidden md:flex items-center space-x-8">
            <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="#features">Features</a>
            <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="#how-it-works">How It Works</a>
            <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="#security">Security</a>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-4 relative">
            <button 
              className="text-sm font-semibold text-brand-charcoal px-4 py-2 hover:opacity-70"
              onClick={() => setIsLoginOpen(!isLoginOpen)}
            >
              Sign In
            </button>
            <button 
              className="bg-brand-charcoal text-white text-sm font-semibold px-6 py-2.5 rounded-button hover:bg-black transition-all"
              onClick={() => navigate('/onboard')}
            >
              Create Workspace
            </button>

            {/* BEGIN: Login Dropdown Panel */}
            {isLoginOpen && (
              <div className="login-dropdown absolute top-14 right-0 w-80 bg-white border border-brand-border rounded-2xl shadow-2xl p-6 z-50">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-brand-charcoal font-bold">Sign In to QueryMind</h3>
                  <button 
                    className="text-gray-400 hover:text-brand-charcoal text-xl"
                    onClick={() => setIsLoginOpen(false)}
                  >
                    ×
                  </button>
                </div>
                <form className="space-y-4" onSubmit={handleLoginSubmit}>
                  <div>
                    <label className="block text-[13px] font-semibold text-brand-charcoal mb-1">Company Join Code</label>
                    <input
                      className="w-full rounded-xl border-brand-border text-sm focus:ring-brand-charcoal focus:border-brand-charcoal uppercase"
                      placeholder="e.g. ACMEXK7P12"
                      required
                      type="text"
                      value={loginForm.join_code}
                      onChange={e => setLoginForm(f => ({ ...f, join_code: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="block text-[13px] font-semibold text-brand-charcoal mb-1">Email Address</label>
                    <input
                      className="w-full rounded-xl border-brand-border text-sm focus:ring-brand-charcoal focus:border-brand-charcoal"
                      placeholder="your@company.com"
                      required
                      type="email"
                      value={loginForm.email}
                      onChange={e => setLoginForm(f => ({ ...f, email: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="block text-[13px] font-semibold text-brand-charcoal mb-1">Password</label>
                    <div className="relative">
                      <input
                        className="w-full rounded-xl border-brand-border text-sm focus:ring-brand-charcoal focus:border-brand-charcoal"
                        placeholder="Password"
                        required
                        type="password"
                        value={loginForm.password}
                        onChange={e => setLoginForm(f => ({ ...f, password: e.target.value }))}
                      />
                    </div>
                  </div>
                  <div className="flex items-center">
                    <input className="rounded border-gray-300 text-brand-charcoal focus:ring-brand-charcoal h-4 w-4" id="rememberMe" type="checkbox"/>
                    <label className="ml-2 text-xs text-brand-grayBody" htmlFor="rememberMe">Remember me</label>
                  </div>
                  <button 
                    className="w-full bg-brand-charcoal text-white py-2.5 rounded-button text-sm font-bold hover:bg-black transition-all flex items-center justify-center gap-2" 
                    type="submit"
                    disabled={isLoggingIn}
                  >
                    {isLoggingIn ? (
                      <>
                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Verifying...</span>
                      </>
                    ) : 'Sign In'}
                  </button>
                  {loginError && (
                    <div className="text-red-600 text-[11px] font-medium mt-2">{loginError}</div>
                  )}
                </form>
                <div className="mt-6 pt-4 border-t border-brand-border text-[12px] space-y-2">
                  <p className="text-gray-400">First time? <button className="text-brand-orange font-semibold" onClick={() => navigate('/register')}>Register account</button></p>
                  <p className="text-gray-400">New company? <button className="text-brand-orange font-semibold" onClick={() => navigate('/onboard')}>Create workspace</button></p>
                  <p className="mt-4 text-[10px] text-gray-400 text-center uppercase tracking-widest">Session expires after 12 hours</p>
                </div>
              </div>
            )}
            {/* END: Login Dropdown Panel */}
          </div>
        </div>
      </nav>

      {/* BEGIN: Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden bg-white" id="hero">
        <div className="max-w-7xl mx-auto px-6 relative z-10 flex flex-col justify-center min-h-[60vh]">
          <div className="max-w-3xl">
            {/* Gitbook-style pill */}
            <div className="inline-flex items-center space-x-2 px-3 py-1.5 mb-8 bg-gray-50 border border-gray-200 rounded-full text-sm font-medium text-brand-charcoal shadow-sm">
              <span className="bg-[#FF5925] text-white px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase">New</span>
              <span>Introducing: QueryMind Agent</span>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
            
            {/* Massive Heading */}
            <h1 className="text-[56px] md:text-[72px] font-medium text-[#1A1A1A] leading-[1.05] tracking-tight mb-6">
              The AI-native<br />
              documentation platform
            </h1>
            
            {/* Subheading */}
            <p className="text-[20px] text-[#555555] mb-10 leading-relaxed font-normal max-w-2xl">
              Transform your documentation into a connected knowledge system —<br />
              one that learns, optimizes, and improves itself intelligently
            </p>
            
            {/* Buttons */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
              <button 
                className="bg-[#1A1A1A] text-white px-6 py-3.5 rounded-full font-medium hover:bg-black transition-all flex items-center justify-between group min-w-[160px]"
                onClick={() => navigate('/onboard')}
              >
                Start for free
                <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </button>
              <button className="bg-[#F3F4F6] text-[#1A1A1A] px-6 py-3.5 rounded-full font-medium hover:bg-[#E5E7EB] transition-all">
                Talk to us
              </button>
            </div>
          </div>
        </div>

        {/* Abstract Corner Graphic */}
        <div className="absolute -bottom-40 -right-20 w-[800px] h-[800px] z-0 pointer-events-none opacity-20 hidden lg:block">
          <div className="w-full h-full rounded-full border-[60px] border-[#FF5925] absolute blur-3xl"></div>
          <div className="w-full h-full rounded-full border-[30px] border-[#FF8C00] absolute blur-2xl top-10 right-10"></div>
        </div>
      </section>



      {/* BEGIN: Features Grid */}
      <section className="py-24 bg-white" id="features">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="section-label">Capabilities</span>
            <h2 className="text-4xl font-bold text-brand-charcoal mt-2 mb-4">Everything your team needs</h2>
            <p className="text-lg text-brand-grayBody">One AI assistant that works across every role in your company.</p>
          </div>
          <Sortable.Root
            value={capabilities}
            onValueChange={setCapabilities}
            getItemValue={(item: { id: string }) => item.id}
            orientation="mixed"
          >
            <Sortable.Content className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {capabilities.map((cap) => (
                <Sortable.Item key={cap.id} value={cap.id} asChild asHandle>
                  <div className="bg-[#F8F9FA] p-8 rounded-2xl border border-gray-100 hover:shadow-sm transition-all group bg-white hover:border-[#FF5925] cursor-grab active:cursor-grabbing hover:-translate-y-1 relative z-10 hover:z-20">
                    <div className="w-10 h-10 bg-white rounded-lg border border-gray-100 flex items-center justify-center mb-6 shadow-[0_2px_8px_-4px_rgba(0,0,0,0.1)] group-hover:scale-105 transition-transform pointer-events-none">
                      {cap.icon}
                    </div>
                    <h3 className="text-base font-semibold text-[#1A1A1A] mb-3 pointer-events-none">{cap.title}</h3>
                    <p className="text-[14px] text-[#666666] leading-relaxed pointer-events-none">{cap.desc}</p>
                  </div>
                </Sortable.Item>
              ))}
            </Sortable.Content>
            
            <Sortable.Overlay>
              <div className="bg-[#F8F9FA] p-8 rounded-2xl border-2 border-[#FF5925] shadow-xl w-full h-full opacity-80 scale-105 cursor-grabbing mix-blend-multiply"></div>
            </Sortable.Overlay>
          </Sortable.Root>
        </div>
      </section>

      {/* BEGIN: How It Works */}
      <section className="py-24 bg-brand-lightBg" id="how-it-works">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <span className="section-label">Onboarding</span>
            <h2 className="text-4xl font-bold text-brand-charcoal mt-2 mb-4">Up and running in minutes</h2>
          </div>
          <div className="relative grid grid-cols-1 md:grid-cols-4 gap-12">
            <div className="relative">
              <div className="text-[80px] font-extrabold text-white absolute -top-12 -left-4 select-none pointer-events-none opacity-50">1</div>
              <div className="relative z-10">
                <h4 className="text-lg font-bold text-brand-charcoal mb-3">Create Workspace</h4>
                <p className="text-sm text-brand-grayBody leading-relaxed">Register your company. You instantly get a unique Join Code for your team.</p>
              </div>
            </div>
            <div className="relative">
              <div className="text-[80px] font-extrabold text-white absolute -top-12 -left-4 select-none pointer-events-none opacity-50">2</div>
              <div className="relative z-10">
                <h4 className="text-lg font-bold text-brand-charcoal mb-3">Upload Documents</h4>
                <p className="text-sm text-brand-grayBody leading-relaxed">Upload PDFs and mark them as Public or Confidential based on sensitivity.</p>
              </div>
            </div>
            <div className="relative">
              <div className="text-[80px] font-extrabold text-white absolute -top-12 -left-4 select-none pointer-events-none opacity-50">3</div>
              <div className="relative z-10">
                <h4 className="text-lg font-bold text-brand-charcoal mb-3">Invite Your Team</h4>
                <p className="text-sm text-brand-grayBody leading-relaxed">Add employees and managers. They receive an invite with the Join Code.</p>
              </div>
            </div>
            <div className="relative">
              <div className="text-[80px] font-extrabold text-white absolute -top-12 -left-4 select-none pointer-events-none opacity-50">4</div>
              <div className="relative z-10">
                <h4 className="text-lg font-bold text-brand-charcoal mb-3">Team Uses ARIA</h4>
                <p className="text-sm text-brand-grayBody leading-relaxed">Staff get instant answers from your internal knowledge base securely.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* BEGIN: Security Section */}
      <section className="py-24 bg-white overflow-hidden" id="security">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            <div className="lg:w-1/2">
              <span className="section-label">Security</span>
              <h2 className="text-4xl font-bold text-brand-charcoal mt-2 mb-8">Built security-first — not as an afterthought</h2>
              <p className="text-lg text-brand-grayBody mb-8">QueryMind applies Lakera Guard at 3 checkpoints on every single request:</p>
              <ul className="space-y-4 mb-10">
                <li className="flex items-start">
                  <span className="bg-green-100 p-1 rounded-full mr-3 mt-1"><svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"></path></svg></span>
                  <span className="text-brand-charcoal font-semibold">Input Scan — <span className="font-normal text-brand-grayBody">Every user message scanned before reaching the AI.</span></span>
                </li>
                <li className="flex items-start">
                  <span className="bg-green-100 p-1 rounded-full mr-3 mt-1"><svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"></path></svg></span>
                  <span className="text-brand-charcoal font-semibold">Document Scan — <span className="font-normal text-brand-grayBody">Retrieved chunks checked before prompt injection.</span></span>
                </li>
                <li className="flex items-start">
                  <span className="bg-green-100 p-1 rounded-full mr-3 mt-1"><svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"></path></svg></span>
                  <span className="text-brand-charcoal font-semibold">Output Scan — <span className="font-normal text-brand-grayBody">Every AI response scanned before delivery.</span></span>
                </li>
              </ul>
              <div className="flex flex-wrap gap-3">
                <span className="px-4 py-2 bg-brand-lightBg rounded-full text-xs font-bold text-brand-charcoal border border-brand-border">Role-Based Access</span>
                <span className="px-4 py-2 bg-brand-lightBg rounded-full text-xs font-bold text-brand-charcoal border border-brand-border">Prompt Injection Protection</span>
                <span className="px-4 py-2 bg-brand-lightBg rounded-full text-xs font-bold text-brand-charcoal border border-brand-border">PII Redaction</span>
                <span className="px-4 py-2 bg-brand-lightBg rounded-full text-xs font-bold text-brand-charcoal border border-brand-border">Human-in-the-Loop</span>
              </div>
            </div>
            <div className="lg:w-1/2 w-full">
              <div className="bg-brand-charcoal p-10 rounded-card text-white relative">
                <div className="absolute inset-0 ribbon-decoration opacity-10"></div>
                <div className="flex flex-col items-center space-y-6 relative z-10 text-[10px] sm:text-xs font-bold tracking-widest uppercase">
                  <div className="bg-white/10 p-3 rounded-lg border border-white/20 w-full text-center">User Input</div>
                  <svg className="w-4 h-4 text-brand-orange" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11V5H9v2H7v2h2v2h2V9h2V7h-2z"></path></svg>
                  <div className="bg-brand-orange text-white p-3 rounded-lg w-full text-center">Lakera Scan #1</div>
                  <div className="bg-white/10 p-3 rounded-lg border border-white/20 w-full text-center">MongoDB RAG</div>
                  <div className="bg-brand-orange text-white p-3 rounded-lg w-full text-center">Lakera Scan #2</div>
                  <div className="bg-white/10 p-3 rounded-lg border border-white/20 w-full text-center">GPT-4 Inference</div>
                  <div className="bg-brand-orange text-white p-3 rounded-lg w-full text-center">Lakera Scan #3</div>
                  <div className="bg-green-500 text-white p-3 rounded-lg w-full text-center shadow-lg shadow-green-500/20">ARIA Response</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* BEGIN: Final CTA Banner */}
      <section className="py-24 bg-brand-charcoal text-white relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-4xl font-bold mb-6">Give your team an AI assistant that actually knows your company</h2>
          <p className="text-lg text-white/70 mb-10">Set up in 2 minutes. No credit card required.</p>
          <button className="inline-block bg-brand-orange text-white px-10 py-4 rounded-button font-bold text-lg hover:bg-brand-orangeHover transition-all" onClick={() => navigate('/onboard')}>Create Your Workspace Free</button>
        </div>
        <div className="ribbon-decoration absolute -bottom-20 -right-20 w-96 h-96 bg-brand-orange opacity-20"></div>
        <div className="ribbon-decoration absolute -top-20 -left-20 w-96 h-96 bg-[#FFB347] opacity-20"></div>
      </section>

      {/* BEGIN: Footer */}
      <footer className="bg-white pt-20 pb-10 border-t border-brand-border">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
          <div className="col-span-1 md:col-span-1">
            <a className="text-brand-charcoal font-extrabold text-2xl tracking-tight" href="#hero">QueryMind</a>
            <p className="mt-4 text-sm text-brand-grayBody">The enterprise AI assistant built on your data.</p>
          </div>
          <div>
            <h5 className="text-brand-charcoal font-bold text-sm mb-6 uppercase tracking-wider">Product</h5>
            <ul className="space-y-4 text-sm">
              <li><a className="text-brand-grayBody hover:text-brand-charcoal transition-colors" href="#features">Features</a></li>
              <li><a className="text-brand-grayBody hover:text-brand-charcoal transition-colors" href="#how-it-works">How It Works</a></li>
              <li><a className="text-brand-grayBody hover:text-brand-charcoal transition-colors" href="#security">Security</a></li>
            </ul>
          </div>
          <div>
            <h5 className="text-brand-charcoal font-bold text-sm mb-6 uppercase tracking-wider">Account</h5>
            <ul className="space-y-4 text-sm">
              <li><button className="text-brand-grayBody hover:text-brand-charcoal transition-colors" onClick={() => navigate('/onboard')}>Create Workspace</button></li>
              <li><button className="text-brand-grayBody hover:text-brand-charcoal transition-colors" onClick={() => setIsLoginOpen(true)}>Sign In</button></li>
              <li><button className="text-brand-grayBody hover:text-brand-charcoal transition-colors" onClick={() => navigate('/register')}>Register</button></li>
            </ul>
          </div>
          <div>
            <h5 className="text-brand-charcoal font-bold text-sm mb-6 uppercase tracking-wider">Compliance</h5>
            <div className="flex gap-4 opacity-50">
              <div className="w-10 h-10 bg-gray-200 rounded-md"></div>
              <div className="w-10 h-10 bg-gray-200 rounded-md"></div>
              <div className="w-10 h-10 bg-gray-200 rounded-md"></div>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 pt-10 border-t border-brand-border flex flex-col md:flex-row justify-between items-center text-xs text-gray-400 gap-4">
          <p>© 2025 QueryMind. All rights reserved.</p>
          <div className="flex space-x-8">
            <a className="hover:text-brand-charcoal transition-colors" href="#hero">Privacy Policy</a>
            <a className="hover:text-brand-charcoal transition-colors" href="#hero">Terms of Service</a>
            <a className="hover:text-brand-charcoal transition-colors" href="#hero">Contact</a>
          </div>
        </div>
      </footer>
    </>
  );
};

export default LandingPage;
