import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const LandingPage = lazy(() => import('./pages/LandingPage'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Onboarding = lazy(() => import('./pages/Onboarding'));
const Chat = lazy(() => import('./pages/Chat'));
const Layout = lazy(() => import('./components/Layout'));
const Overview = lazy(() => import('./pages/Overview'));
const Users = lazy(() => import('./pages/Users'));
const Documents = lazy(() => import('./pages/Documents'));
const EmailSettings = lazy(() => import('./pages/EmailSettings'));
const Metrics = lazy(() => import('./pages/Metrics'));

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white text-brand-grayBody">
      Loading...
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/onboard" element={<Onboarding />} />
          <Route path="/chat" element={<Chat />} />

          {/* Dashboard Routes wrapped in Layout */}
          <Route path="/dashboard" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard/overview" replace />} />
            <Route path="overview" element={<Overview />} />
            <Route path="users" element={<Users />} />
            <Route path="documents" element={<Documents />} />
            <Route path="email-settings" element={<EmailSettings />} />
            <Route path="metrics" element={<Metrics />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
