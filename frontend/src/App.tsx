import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import Onboarding from './pages/Onboarding';
import Chat from './pages/Chat';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import Users from './pages/Users';
import Documents from './pages/Documents';
import EmailSettings from './pages/EmailSettings';
import Metrics from './pages/Metrics';

function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}

export default App;
