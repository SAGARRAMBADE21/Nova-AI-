import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { register as registerUser } from '@/lib/api';

const Register = () => {
  const [formData, setFormData] = useState({ join_code: '', email: '', password: '', confirm_password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [registeredRole, setRegisteredRole] = useState('Employee');
  const [errorMsg, setErrorMsg] = useState('');
  const [countdown, setCountdown] = useState(3);
  const navigate = useNavigate();

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const val = formData.password;
  const hasLength = val.length >= 8;
  const hasUpper = /[A-Z]/.test(val);
  const hasNum = /[0-9]/.test(val);
  let score = 0;
  if (hasLength) score++;
  if (hasUpper) score++;
  if (hasNum) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;

  const getStrengthLabel = () => {
    switch(score) {
      case 1: return 'Weak';
      case 2: return 'Fair';
      case 3: return 'Strong';
      case 4: return 'Very Strong';
      default: return 'None';
    }
  };

  const getStrengthColor = (reqScore: number) => {
    if (score >= reqScore) {
      if (score === 1) return 'bg-red-400';
      if (score === 2) return 'bg-yellow-400';
      if (score === 3) return 'bg-blue-400';
      if (score >= 4) return 'bg-green-500';
    }
    return 'bg-gray-100';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirm_password) return;
    setIsSubmitting(true);
    setErrorMsg('');
    
    try {
      const result = await registerUser({
        join_code: formData.join_code.trim().toUpperCase(),
        email:     formData.email.trim().toLowerCase(),
        password:  formData.password,
      });
      setRegisteredRole(result.role);
      setSuccess(true);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Registration failed. Is the backend running?');
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (!success) return;
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          navigate('/login');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [success, navigate]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-x-hidden bg-white text-brand-grayBody font-sans">
      <div className="absolute -top-20 -right-20 w-96 h-96 opacity-10 pointer-events-none">
        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <path d="M44.7,-76.4C58.1,-69.2,69.2,-58.1,76.4,-44.7C83.7,-31.3,87.1,-15.7,85.2,-0.8C83.4,14.1,76.2,28.2,67.6,41.2C59,54.2,49,66.1,36.1,73.5C23.2,80.9,7.4,83.8,-8.5,82.4C-24.4,81,-40.4,75.3,-54.1,65.7C-67.8,56.1,-79.1,42.6,-84.9,27.1C-90.7,11.6,-91,-5.9,-85.9,-21.4C-80.8,-36.9,-70.4,-50.4,-57.6,-58.1C-44.8,-65.8,-29.7,-67.7,-15.6,-72.3C-1.5,-76.9,11.5,-84.1,44.7,-76.4Z" fill="#FF5925" transform="translate(100 100)"></path>
        </svg>
      </div>

      <header className="mb-10 text-center relative z-10 w-full">
        <div className="flex items-center justify-center mb-4 cursor-pointer" onClick={() => navigate('/')}>
          <span className="text-2xl font-bold text-brand-charcoal tracking-tight">QueryMind</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold text-brand-charcoal mb-3">Set Up Your Account</h1>
        <p className="text-lg text-brand-grayBody">Complete your registration using your invite details</p>
      </header>

      <main className="w-full max-w-xl bg-white border border-brand-border rounded-card shadow-sm p-8 md:p-12 z-10">
        {!success ? (
          <>
            <div className="bg-[#FFF4F0] border border-[#FFD0C0] rounded-xl p-4 mb-8 flex items-start gap-3">
              <svg className="w-5 h-5 text-brand-orange mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
              <p className="text-sm text-[#854D0E]">Check your invite email for your <strong>Join Code</strong> and the email address your admin used to invite you.</p>
            </div>

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-brand-charcoal" htmlFor="join_code">Company Join Code</label>
                <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:border-brand-charcoal focus:ring-0 placeholder:text-gray-400 uppercase text-brand-charcoal" id="join_code" name="join_code" onChange={handleInput} placeholder="Your company join code (e.g. ACMEXK7P12)" required type="text" value={formData.join_code}/>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-brand-charcoal" htmlFor="email">Email Address</label>
                <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:border-brand-charcoal focus:ring-0 placeholder:text-gray-400 text-brand-charcoal" id="email" name="email" onChange={handleInput} placeholder="The email address your admin invited" required type="email" value={formData.email}/>
                <p className="text-[13px] text-gray-400">Must match exactly the email your admin used</p>
              </div>

              <div className="space-y-2 relative">
                <label className="block text-sm font-semibold text-brand-charcoal" htmlFor="password">New Password</label>
                <div className="relative">
                  <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:border-brand-charcoal focus:ring-0 placeholder:text-gray-400 pr-12 text-brand-charcoal" id="password" name="password" onChange={handleInput} placeholder="Create your password" required type={showPassword ? 'text' : 'password'} value={formData.password}/>
                  <button className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-brand-charcoal" onClick={() => setShowPassword(!showPassword)} type="button">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                  </button>
                </div>

                <div className="mt-3 space-y-2">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4].map(s => <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${getStrengthColor(s)}`}></div>)}
                  </div>
                  <p className={`text-[11px] font-bold uppercase tracking-wider ${score === 0 ? 'text-gray-400' : 'text-brand-charcoal'}`}>Strength: {getStrengthLabel()}</p>
                </div>

                <ul className="text-[13px] space-y-1.5 pt-2">
                  <li className={`flex items-center gap-2 ${hasLength ? 'text-green-600' : 'text-gray-400'}`}><span>{hasLength ? '✓' : '○'}</span> At least 8 characters</li>
                  <li className={`flex items-center gap-2 ${hasUpper ? 'text-green-600' : 'text-gray-400'}`}><span>{hasUpper ? '✓' : '○'}</span> At least one uppercase letter</li>
                  <li className={`flex items-center gap-2 ${hasNum ? 'text-green-600' : 'text-gray-400'}`}><span>{hasNum ? '✓' : '○'}</span> At least one number</li>
                </ul>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-brand-charcoal" htmlFor="confirm_password">Confirm Password</label>
                <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:border-brand-charcoal focus:ring-0 placeholder:text-gray-400 text-brand-charcoal" id="confirm_password" name="confirm_password" onChange={handleInput} placeholder="Repeat your password" required type="password" value={formData.confirm_password}/>
              </div>

              <div className="pt-4">
                <button className="w-full py-4 bg-brand-charcoal text-white font-semibold rounded-pill hover:bg-black transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2" disabled={isSubmitting || formData.password !== formData.confirm_password || formData.password === ''} type="submit">
                  <span>{isSubmitting ? 'Creating...' : 'Create Account'}</span>
                  {isSubmitting && (
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"></path></svg>
                  )}
                </button>
              </div>

              {errorMsg && (
                <p className="text-sm font-semibold text-red-500 pt-2">{errorMsg}</p>
              )}
            </form>
          </>
        ) : (
          <div className="flex flex-col items-center text-center py-4">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"></path></svg>
            </div>
            <h2 className="text-2xl font-bold text-brand-charcoal mb-2">Account Created Successfully</h2>
            <p className="text-brand-grayBody mb-6">You are joining as: <span className="font-semibold text-brand-charcoal bg-gray-100 px-3 py-1 rounded-full text-sm capitalize">{registeredRole}</span></p>
            <div className="w-full bg-gray-50 border border-brand-border rounded-xl p-6 mb-8">
              <p className="text-sm text-brand-grayBody mb-1">Auto-redirect countdown:</p>
              <p className="text-2xl font-bold text-brand-orange">Taking you to login in {countdown}...</p>
            </div>
            <button className="text-brand-charcoal font-semibold hover:text-brand-orange transition-colors flex items-center gap-2" onClick={() => navigate('/login')}>
              Go to Login Now
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M14 5l7 7m0 0l-7 7m7-7H3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
            </button>
          </div>
        )}
      </main>

      <footer className="mt-8 text-center relative z-10 w-full">
        <button className="text-sm font-semibold text-brand-grayBody hover:text-brand-charcoal transition-colors" onClick={() => navigate('/login')}>
          Already registered? <span className="text-brand-orange underline">Sign In →</span>
        </button>
      </footer>
    </div>
  );
};

export default Register;
