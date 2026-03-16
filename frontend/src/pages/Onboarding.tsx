import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Onboarding = () => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({ companyName: '', adminEmail: '', password: '', confirmPassword: '' });
  const [joinCode, setJoinCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
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
  if (val.length > 12) score++;

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
      if (score === 1) return 'bg-red-500';
      if (score === 2) return 'bg-yellow-500';
      if (score === 3) return 'bg-blue-500';
      if (score >= 4) return 'bg-green-500';
    }
    return 'bg-brand-grayBorder';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) return;
    setIsSubmitting(true);
    
    // Simulate API Call
    setTimeout(() => {
      setJoinCode(formData.companyName.substring(0, 4).toUpperCase() + 'XK7P12');
      setIsSubmitting(false);
      setStep(2);
    }, 1200);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-brand-lightBg font-sans text-brand-grayBody">
      <main className="w-full max-w-[540px]">
        {/* Header Section */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-2 mb-6 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-8 h-8 bg-brand-charcoal rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">Q</span>
            </div>
            <span className="text-brand-charcoal font-bold text-2xl tracking-tight">QueryMind</span>
          </div>
          <h1 className="text-brand-charcoal text-4xl font-bold mb-3">Create Your Company Workspace</h1>
          <p className="text-brand-grayBody text-lg">Set up your private AI assistant for your entire team</p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-8 px-4">
          <div className="flex flex-col items-center gap-2 flex-1">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold border-2 ${step >= 1 ? 'border-brand-orange bg-brand-orange text-white' : 'border-brand-grayBorder bg-white text-brand-grayCaption'}`}>1</div>
            <span className={`text-xs font-bold uppercase tracking-widest ${step >= 1 ? 'text-brand-orange' : 'text-brand-grayCaption'}`}>Company Setup</span>
          </div>
          <div className={`h-[2px] flex-1 mb-6 ${step >= 2 ? 'bg-brand-orange' : 'bg-brand-grayBorder'}`}></div>
          <div className="flex flex-col items-center gap-2 flex-1">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold border-2 ${step >= 2 ? 'border-brand-orange bg-brand-orange text-white' : 'border-brand-grayBorder bg-white text-brand-grayCaption'}`}>2</div>
            <span className={`text-xs font-bold uppercase tracking-widest ${step >= 2 ? 'text-brand-orange' : 'text-brand-grayCaption'}`}>Your Join Code</span>
          </div>
        </div>

        {/* Step 1 Form */}
        {step === 1 && (
          <section className="bg-white p-9 rounded-card shadow-sm border border-brand-border">
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-1.5">
                <label className="block text-[13px] font-semibold text-brand-charcoal" htmlFor="companyName">Company Name</label>
                <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:ring-brand-charcoal focus:border-brand-charcoal transition-all placeholder:text-brand-grayCaption text-brand-charcoal" id="companyName" name="companyName" onChange={handleInput} placeholder="Acme Corporation" required type="text" value={formData.companyName}/>
              </div>
              
              <div className="space-y-1.5">
                <label className="block text-[13px] font-semibold text-brand-charcoal" htmlFor="adminEmail">Admin Email</label>
                <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:ring-brand-charcoal focus:border-brand-charcoal transition-all placeholder:text-brand-grayCaption text-brand-charcoal" id="adminEmail" name="adminEmail" onChange={handleInput} placeholder="admin@yourcompany.com" required type="email" value={formData.adminEmail}/>
                <p className="text-[13px] text-brand-grayCaption">This becomes your login email address</p>
              </div>

              <div className="space-y-1.5 relative">
                <label className="block text-[13px] font-semibold text-brand-charcoal" htmlFor="password">Password</label>
                <div className="relative">
                  <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:ring-brand-charcoal focus:border-brand-charcoal transition-all placeholder:text-brand-grayCaption pr-12 text-brand-charcoal" id="password" minLength={8} name="password" onChange={handleInput} placeholder="Create a strong password" required type={showPassword ? 'text' : 'password'} value={formData.password}/>
                  <button className="absolute right-4 top-1/2 -translate-y-1/2 text-brand-grayCaption hover:text-brand-charcoal" onClick={() => setShowPassword(!showPassword)} type="button">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                  </button>
                </div>
                <div className="flex gap-1 mt-3">
                  {[1, 2, 3, 4].map((s) => (
                    <div key={s} className={`h-1 flex-1 rounded-sm transition-colors ${getStrengthColor(s)}`}></div>
                  ))}
                </div>
                <p className="text-xs font-semibold text-brand-grayCaption mt-1">Strength: {getStrengthLabel()}</p>
                <ul className="mt-3 space-y-1 text-xs">
                  <li className={`flex items-center gap-2 ${hasLength ? 'text-brand-success' : 'text-brand-danger'}`}><span>{hasLength ? '✓' : '✕'}</span> At least 8 characters</li>
                  <li className={`flex items-center gap-2 ${hasUpper ? 'text-brand-success' : 'text-brand-danger'}`}><span>{hasUpper ? '✓' : '✕'}</span> At least one uppercase letter</li>
                  <li className={`flex items-center gap-2 ${hasNum ? 'text-brand-success' : 'text-brand-danger'}`}><span>{hasNum ? '✓' : '✕'}</span> At least one number</li>
                </ul>
              </div>

              <div className="space-y-1.5">
                <label className="block text-[13px] font-semibold text-brand-charcoal" htmlFor="confirmPassword">Confirm Password</label>
                <input className="w-full px-4 py-3 rounded-xl border-brand-border focus:ring-brand-charcoal focus:border-brand-charcoal transition-all placeholder:text-brand-grayCaption text-brand-charcoal" id="confirmPassword" name="confirmPassword" onChange={handleInput} placeholder="Repeat password" required type="password" value={formData.confirmPassword}/>
              </div>

              <div className="flex items-start gap-3 pt-2">
                <input className="mt-1 rounded border-brand-border text-brand-charcoal focus:ring-brand-charcoal" id="authCheck" required type="checkbox"/>
                <label className="text-[13px] text-brand-grayBody leading-relaxed" htmlFor="authCheck">
                  I confirm I am authorised to create this workspace for my company
                </label>
              </div>

              <button className="w-full bg-brand-charcoal text-white font-bold py-4 rounded-pill hover:bg-black transition-all flex items-center justify-center gap-2 disabled:opacity-70 group" disabled={isSubmitting} type="submit">
                <span>{isSubmitting ? 'Creating...' : 'Create Workspace'}</span>
                {!isSubmitting && (
                  <svg className="h-5 w-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M14 5l7 7m0 0l-7 7m7-7H3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></path></svg>
                )}
              </button>
            </form>
            <div className="mt-8 pt-8 border-t border-brand-border text-center">
              <button className="text-sm font-semibold text-brand-charcoal hover:underline" onClick={() => navigate('/login')}>Already have a workspace? Sign In →</button>
            </div>
          </section>
        )}

        {/* Step 2 Success */}
        {step === 2 && (
          <section className="bg-white p-9 rounded-card shadow-sm border border-brand-border">
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-green-100 text-brand-success rounded-full flex items-center justify-center mb-6">
                <svg className="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"></path></svg>
              </div>
              <h2 className="text-2xl font-bold text-brand-charcoal mb-2">Your Workspace is Ready!</h2>
              <p className="text-brand-grayBody mb-8">Company: <span className="font-semibold">{formData.companyName}</span></p>

              <div className="w-full bg-brand-lightBg border border-brand-border rounded-2xl p-6 mb-8">
                <p className="text-xs font-bold uppercase tracking-widest text-brand-grayCaption mb-3">Your Company Join Code</p>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-4xl font-mono font-bold tracking-tighter text-brand-charcoal">{joinCode}</span>
                  <button className="bg-white border border-brand-border text-brand-charcoal px-4 py-2 rounded-pill text-xs font-bold shadow-sm hover:bg-brand-lightBg transition-all" onClick={() => copyToClipboard(joinCode)}>
                    Copy Code
                  </button>
                </div>
              </div>

              <div className="w-full bg-orange-50 border border-orange-100 rounded-xl p-4 text-left mb-8">
                <p className="text-[13px] text-orange-800 leading-relaxed">
                  <strong>Important:</strong> Share this code with your team members. They need it to register and log in to QueryMind. Anyone with this code can join your workspace.
                </p>
              </div>

              <div className="w-full text-left mb-8">
                <label className="block text-[13px] font-semibold text-brand-charcoal mb-2">Invite Message</label>
                <div className="bg-white border border-brand-border rounded-xl p-4 font-mono text-[13px] text-brand-grayBody whitespace-pre-wrap relative group">
                  {`You've been invited to ${formData.companyName} on QueryMind.\n\nJoin Code: ${joinCode}\n1. Register at: querymind.ai/register\n2. Log in at: querymind.ai/login`}
                </div>
                <button className="mt-3 w-full bg-brand-lightBg text-brand-charcoal font-bold py-3 rounded-pill text-sm hover:bg-brand-border transition-all" onClick={() => copyToClipboard(`You've been invited to ${formData.companyName} on QueryMind.\n\nJoin Code: ${joinCode}\n1. Register at: querymind.ai/register\n2. Log in at: querymind.ai/login`)}>
                  Copy Invite Message
                </button>
              </div>

              <div className="w-full space-y-4 pt-4 border-t border-brand-border">
                <button className="block w-full bg-brand-charcoal text-white font-bold py-4 rounded-pill hover:bg-black transition-all text-center" onClick={() => navigate('/login')}>
                  Go to Login →
                </button>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default Onboarding;
