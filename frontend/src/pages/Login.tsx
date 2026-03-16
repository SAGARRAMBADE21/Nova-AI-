import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { joinWorkspace } from '@/lib/api';

const Login = () => {
  const [formData, setFormData] = useState({ join_code: '', email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const result = await joinWorkspace({
        join_code: formData.join_code.trim().toUpperCase(),
        email:     formData.email.trim().toLowerCase(),
        password:  formData.password,
      });
      localStorage.setItem('nova_token',   result.token);
      localStorage.setItem('nova_role',    result.role);
      localStorage.setItem('nova_company', result.company_name);
      navigate('/dashboard');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Login failed. Is the backend running?');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans overflow-x-hidden bg-white text-brand-grayBody relative">
      <style>{`
        .ribbon-top-right {
          position: absolute;
          top: -100px;
          right: -100px;
          width: 400px;
          height: 400px;
          background: linear-gradient(135deg, #FF5925 0%, #FFB347 100%);
          filter: blur(80px);
          opacity: 0.15;
          border-radius: 50%;
          z-index: 0;
        }
        .ribbon-bottom-left {
          position: absolute;
          bottom: -150px;
          left: -150px;
          width: 500px;
          height: 500px;
          background: linear-gradient(135deg, #FFB347 0%, #FF5925 100%);
          filter: blur(100px);
          opacity: 0.1;
          border-radius: 50%;
          z-index: 0;
        }
      `}</style>
      
      {/* Navigation */}
      <nav className="sticky top-0 z-50 h-16 bg-white/92 backdrop-blur-md border-b border-brand-border flex items-center px-6 lg:px-12 justify-between">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
          <span className="text-brand-charcoal font-bold text-xl tracking-tight">QueryMind</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="/#features">Features</a>
          <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="/#how-it-works">How It Works</a>
          <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="/#security">Security</a>
          <a className="text-sm font-medium text-brand-grayBody hover:text-brand-charcoal transition-colors" href="/#pricing">Pricing</a>
        </div>
        <div>
          <button className="bg-brand-charcoal text-white px-5 py-2 rounded-pill text-sm font-semibold hover:opacity-90 transition-all" onClick={() => navigate('/onboard')}>
            Create Workspace
          </button>
        </div>
      </nav>

      <main className="flex-grow flex items-center justify-center px-4 py-12 relative z-10 w-full">
        <div className="ribbon-top-right"></div>
        <div className="ribbon-bottom-left"></div>

        <div className="w-full max-w-[480px] bg-brand-lightBg border border-brand-border rounded-card p-8 md:p-10 shadow-[0_2px_16px_rgba(0,0,0,0.06)] relative z-10">
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-bold text-brand-charcoal mb-3">Sign In to QueryMind</h1>
            <p className="text-brand-grayBody">Enter your company credentials to continue</p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="block text-[13px] font-semibold text-brand-charcoal mb-1.5" htmlFor="join_code">Company Join Code</label>
              <input className="w-full px-4 py-3 bg-white border border-brand-border rounded-[12px] text-brand-charcoal placeholder-brand-placeholder focus:border-brand-charcoal focus:ring-1 focus:ring-brand-charcoal transition-all uppercase" id="join_code" name="join_code" onChange={handleInput} placeholder="e.g. ACMEXK7P12" required type="text" value={formData.join_code.toUpperCase()}/>
              <p className="mt-1.5 text-xs text-gray-400">Find this in your invite email or from your admin</p>
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-brand-charcoal mb-1.5" htmlFor="email">Email Address</label>
              <input className="w-full px-4 py-3 bg-white border border-brand-border rounded-[12px] text-brand-charcoal placeholder-brand-placeholder focus:border-brand-charcoal focus:ring-1 focus:ring-brand-charcoal transition-all" id="email" name="email" onChange={handleInput} placeholder="your@company.com" required type="email" value={formData.email}/>
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-brand-charcoal mb-1.5" htmlFor="password">Password</label>
              <div className="relative">
                <input className="w-full px-4 py-3 bg-white border border-brand-border rounded-[12px] text-brand-charcoal placeholder-brand-placeholder focus:border-brand-charcoal focus:ring-1 focus:ring-brand-charcoal transition-all pr-12" id="password" name="password" onChange={handleInput} placeholder="Your password" required type={showPassword ? 'text' : 'password'} value={formData.password}/>
                <button aria-label="Toggle password visibility" className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-placeholder hover:text-brand-charcoal transition-colors" onClick={() => setShowPassword(!showPassword)} type="button">
                  <svg className="lucide lucide-eye" fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input className="h-4 w-4 text-brand-orange border-brand-border rounded focus:ring-brand-orange" id="remember" type="checkbox"/>
                <label className="ml-2 block text-sm text-brand-grayBody" htmlFor="remember">Remember me</label>
              </div>
            </div>

            <button className="w-full bg-brand-charcoal text-white py-3.5 rounded-pill font-semibold text-base hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed" disabled={isSubmitting} type="submit">
              <span>{isSubmitting ? 'Verifying...' : 'Sign In'}</span>
              {isSubmitting && (
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
              )}
            </button>

            {errorMsg && (
              <div className="text-center text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">
                {errorMsg}
              </div>
            )}
          </form>

          <div className="mt-8 pt-6 border-t border-brand-border flex flex-col gap-3 text-center">
            <p className="text-sm">First time? <button className="text-brand-orange font-semibold hover:text-brand-orangeHover transition-colors ml-1" onClick={() => navigate('/register')}>Register your account →</button></p>
            <p className="text-sm">New company? <button className="text-brand-orange font-semibold hover:text-brand-orangeHover transition-colors ml-1" onClick={() => navigate('/onboard')}>Create a workspace →</button></p>
          </div>
        </div>
      </main>

      <footer className="py-8 px-6 border-t border-brand-border bg-white text-center z-10">
        <p className="text-sm text-brand-placeholder">© 2025 QueryMind. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Login;
