import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import { useAuth } from "./context/AuthContext";
import AdminScores from "./pages/AdminScores";
import AdminSettings from "./pages/AdminSettings";
import AdminSubgroups from "./pages/AdminSubgroups";
import Dashboard from "./pages/Dashboard";
import Groups from "./pages/Groups";
import ForgotPassword from "./pages/ForgotPassword";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import MatchDetail from "./pages/MatchDetail";
import Matches from "./pages/Matches";
import Rankings from "./pages/Rankings";
import Register from "./pages/Register";
import SubgroupDetail from "./pages/SubgroupDetail";
import Subgroups from "./pages/Subgroups";
import Venues from "./pages/Venues";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function HomeRoute() {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  return user ? <Dashboard /> : <LandingPage />;
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 w-full min-w-0 overflow-x-hidden">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={<HomeRoute />}
          />
          <Route
            path="/matches"
            element={
              <ProtectedRoute>
                <Matches />
              </ProtectedRoute>
            }
          />
          <Route
            path="/matches/:id"
            element={
              <ProtectedRoute>
                <MatchDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/groups"
            element={
              <ProtectedRoute>
                <Groups />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rankings"
            element={
              <ProtectedRoute>
                <Rankings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/venues"
            element={
              <ProtectedRoute>
                <Venues />
              </ProtectedRoute>
            }
          />
          <Route
            path="/subgroups"
            element={
              <ProtectedRoute>
                <Subgroups />
              </ProtectedRoute>
            }
          />
          <Route
            path="/subgroups/:id"
            element={
              <ProtectedRoute>
                <SubgroupDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/scores"
            element={
              <AdminRoute>
                <AdminScores />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <AdminRoute>
                <AdminSettings />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/subgroups"
            element={
              <AdminRoute>
                <AdminSubgroups />
              </AdminRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}
