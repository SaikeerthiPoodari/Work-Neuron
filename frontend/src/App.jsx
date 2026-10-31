import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthLanding, LoginPage, RegisterPage } from "./pages/AuthPages";
import DashboardPage from "./pages/DashboardPage";
import TasksPage from "./pages/TasksPage";
import TaskDetailPage from "./pages/TaskDetailPage";
import ProfilePage from "./pages/ProfilePage";
import AssignmentsPage from "./pages/AssignmentsPage";
import NotificationsPage from "./pages/NotificationsPage";
import AdminPage from "./pages/AdminPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import ReviewsPage from "./pages/ReviewsPage";
import PaymentsPage from "./pages/PaymentsPage";
import WalletPage from "./pages/WalletPage";
import ComplaintsPage from "./pages/ComplaintsPage";
import SkillGraphPage from "./pages/SkillGraphPage";
import NearbyJobsPage from "./pages/NearbyJobsPage";
import EmployerVerificationPage from "./pages/EmployerVerificationPage";
import ApplicationComparison from "./components/ApplicationComparison";
import ClientWorkersPage from "./pages/ClientWorkersPage";
import ClientAnalyticsPage from "./pages/ClientAnalyticsPage";
import SettingsPage from "./pages/SettingsPage";
import ClientCommunicationPage from "./pages/ClientCommunicationPage";
import PaymentDetailPage from "./pages/PaymentDetailPage";
import { PasswordResetConfirmPage, PasswordResetRequestPage } from "./pages/PasswordResetPage";
import NetworkFeedPage from "./pages/NetworkFeedPage";
import NetworkDiscoverPage from "./pages/NetworkDiscoverPage";
import NetworkMessagesPage from "./pages/NetworkMessagesPage";
import PublicProfilePage from "./pages/PublicProfilePage";

const portalPages = <Route element={<AppLayout />}>
  <Route index element={<Navigate to="dashboard" replace />} />
  <Route path="dashboard" element={<DashboardPage />} />
  <Route path="feed" element={<NetworkFeedPage />} />
  <Route path="discover" element={<NetworkDiscoverPage />} />
  <Route path="network-messages" element={<NetworkMessagesPage />} />
  <Route path="people/:id" element={<PublicProfilePage />} />
  <Route path="tasks" element={<TasksPage />} />
  <Route path="nearby" element={<NearbyJobsPage />} />
  <Route path="tasks/:id" element={<TaskDetailPage />} />
  <Route path="profile" element={<ProfilePage />} />
  <Route path="settings" element={<SettingsPage />} />
  <Route path="verification" element={<EmployerVerificationPage />} />
  <Route path="applications" element={<ApplicationComparison />} />
  <Route path="workers" element={<ClientWorkersPage />} />
  <Route path="analytics" element={<ClientAnalyticsPage />} />
  <Route path="messages" element={<ClientCommunicationPage />} />
  <Route path="assignments" element={<AssignmentsPage />} />
  <Route path="recommendations" element={<RecommendationsPage />} />
  <Route path="skill-graph" element={<SkillGraphPage />} />
  <Route path="reviews" element={<ReviewsPage />} />
  <Route path="payments" element={<PaymentsPage />} />
  <Route path="wallet" element={<WalletPage />} />
  <Route path="payments/:id" element={<PaymentDetailPage />} />
  <Route path="complaints" element={<ComplaintsPage />} />
  <Route path="notifications" element={<NotificationsPage />} />
  <Route path="admin" element={<AdminPage />} />
</Route>;

function Portal({ role }) { return <ProtectedRoute roles={[role]}><Outlet /></ProtectedRoute>; }
function RoleRoutes({ role, prefix }) { return <Route path={prefix} element={<Portal role={role} />}>{portalPages}</Route>; }
function LegacyPortal() { return <ProtectedRoute><Outlet /></ProtectedRoute>; }

export default function App() {
  return <Routes>
    <Route path="/auth" element={<AuthLanding />} />
    <Route path="/" element={<AuthLanding />} />
    <Route path="/login" element={<Navigate to="/auth" replace />} />
    <Route path="/register" element={<Navigate to="/auth" replace />} />
    <Route path="/password-reset" element={<PasswordResetRequestPage />} />
    <Route path="/password-reset/confirm/:uid/:token" element={<PasswordResetConfirmPage />} />
    <Route path="/worker/login" element={<LoginPage role="WORKER" />} />
    <Route path="/worker/register" element={<RegisterPage role="WORKER" />} />
    <Route path="/client/login" element={<LoginPage role="CLIENT" />} />
    <Route path="/client/register" element={<RegisterPage role="CLIENT" />} />
    <Route path="/admin/login" element={<LoginPage role="ADMIN" />} />
    {RoleRoutes({ role: "WORKER", prefix: "/worker" })}
    {RoleRoutes({ role: "CLIENT", prefix: "/client" })}
    {RoleRoutes({ role: "ADMIN", prefix: "/admin" })}
    <Route element={<LegacyPortal />}><Route element={<AppLayout />}><Route path="/tasks" element={<TasksPage />} /><Route path="/nearby" element={<NearbyJobsPage />} /><Route path="/feed" element={<NetworkFeedPage />} /><Route path="/discover" element={<NetworkDiscoverPage />} /><Route path="/people/:id" element={<PublicProfilePage />} /><Route path="/messages" element={<ClientCommunicationPage />} /><Route path="/tasks/:id" element={<TaskDetailPage />} /><Route path="/profile" element={<ProfilePage />} /><Route path="/assignments" element={<AssignmentsPage />} /><Route path="/recommendations" element={<RecommendationsPage />} /><Route path="/skill-graph" element={<SkillGraphPage />} /><Route path="/reviews" element={<ReviewsPage />} /><Route path="/payments" element={<PaymentsPage />} /><Route path="/complaints" element={<ComplaintsPage />} /><Route path="/notifications" element={<NotificationsPage />} /></Route></Route>
    <Route path="*" element={<Navigate to="/auth" replace />} />
  </Routes>;
}
