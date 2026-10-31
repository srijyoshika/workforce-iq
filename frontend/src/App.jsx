import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import EmployeesPage from './pages/EmployeesPage';
import EmployeeProfilePage from './pages/EmployeeProfilePage';
import RolesSkillsPage from './pages/RolesSkillsPage';
import ProjectsPage from './pages/ProjectsPage';
import DemandForecastPage from './pages/DemandForecastPage';
import ScenarioPlanningPage from './pages/ScenarioPlanningPage';
import AllocationsPage from './pages/AllocationsPage';
import AvailabilityPage from './pages/AvailabilityPage';
import SkillGapPage from './pages/SkillGapPage';
import UtilizationPage from './pages/UtilizationPage';
import TrainingPage from './pages/TrainingPage';
import RecommendationsPage from './pages/RecommendationsPage';
import OptimizationPage from './pages/OptimizationPage';
import ExceptionMonitoringPage from './pages/ExceptionMonitoringPage';
import DataQualityPage from './pages/DataQualityPage';
import AuditHistoryPage from './pages/AuditHistoryPage';
import AdministrationPage from './pages/AdministrationPage';
import SystemHealthPage from './pages/SystemHealthPage';
import NotFoundPage from './pages/NotFoundPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Enterprise Platform Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            {/* Core */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="health" element={<SystemHealthPage />} />

            {/* Workforce Management */}
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="employees/:id" element={<EmployeeProfilePage />} />
            <Route path="roles-skills" element={<RolesSkillsPage />} />
            <Route path="availability" element={<AvailabilityPage />} />
            <Route path="training" element={<TrainingPage />} />

            {/* Planning & Capacity */}
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="forecast" element={<DemandForecastPage />} />
            <Route path="allocations" element={<AllocationsPage />} />
            <Route path="skill-gaps" element={<SkillGapPage />} />
            <Route path="utilization" element={<UtilizationPage />} />

            {/* AI Intelligence */}
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="optimization" element={<OptimizationPage />} />
            <Route path="scenarios" element={<ScenarioPlanningPage />} />

            {/* Governance & Quality */}
            <Route path="exceptions" element={<ExceptionMonitoringPage />} />
            <Route path="quality" element={<DataQualityPage />} />
            <Route path="audit" element={<AuditHistoryPage />} />
            <Route path="admin" element={<AdministrationPage />} />

            {/* Fallback */}
            <Route path="404" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
