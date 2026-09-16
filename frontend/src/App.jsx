import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
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
import ComplaintsPage from "./pages/ComplaintsPage";
import SkillGraphPage from "./pages/SkillGraphPage";
import TaskDecompositionPage from "./pages/TaskDecompositionPage";

export default function App() { return <Routes><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route element={<ProtectedRoute />}><Route element={<AppLayout />}><Route index element={<DashboardPage />} /><Route path="tasks" element={<TasksPage />} /><Route path="tasks/:id" element={<TaskDetailPage />} /><Route path="tasks/:id/decomposition" element={<TaskDecompositionPage />} /><Route path="profile" element={<ProfilePage />} /><Route path="assignments" element={<AssignmentsPage />} /><Route path="recommendations" element={<RecommendationsPage />} /><Route path="skill-graph" element={<SkillGraphPage />} /><Route path="reviews" element={<ReviewsPage />} /><Route path="payments" element={<PaymentsPage />} /><Route path="complaints" element={<ComplaintsPage />} /><Route path="notifications" element={<NotificationsPage />} /><Route element={<ProtectedRoute roles={["ADMIN"]} />}><Route path="admin" element={<AdminPage />} /></Route></Route></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes>; }
