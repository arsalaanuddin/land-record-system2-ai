import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { Splash } from './pages/Splash';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { UploadComponent } from './pages/Upload';
import { Processing } from './pages/Processing';
import { VerificationStudio } from './pages/Verification';
import { AllRecords } from './pages/AllRecords';
import { ReviewQueue } from './pages/ReviewQueue';
import { GISMap } from './pages/GISMap';
import { Reports } from './pages/Reports';
import { ApiPortal } from './pages/ApiPortal';

function AppShell() {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <Navbar />
        <Outlet />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Splash />} />
        <Route path="/login" element={<Login />} />

        <Route path="/dashboard" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<UploadComponent />} />
          <Route path="processing/:documentId" element={<Processing />} />
          <Route path="verification/:recordId" element={<VerificationStudio />} />
          <Route path="records" element={<AllRecords />} />
          <Route path="review" element={<ReviewQueue />} />
          <Route path="map" element={<GISMap />} />
          <Route path="reports" element={<Reports />} />
          <Route path="apis" element={<ApiPortal />} />
        </Route>

        {/* Legacy paths kept so old links do not dead-end. */}
        <Route path="/upload" element={<Navigate to="/dashboard/upload" replace />} />
        <Route path="/records" element={<Navigate to="/dashboard/records" replace />} />
        <Route path="/verify/:recordId" element={<LegacyVerificationRedirect />} />
        <Route path="/gis" element={<Navigate to="/dashboard/map" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

function LegacyVerificationRedirect() {
  const match = window.location.pathname.match(/\/verify\/(.+)$/);
  const recordId = match?.[1] ?? '';
  return <Navigate to={`/dashboard/verification/${recordId}`} replace />;
}
