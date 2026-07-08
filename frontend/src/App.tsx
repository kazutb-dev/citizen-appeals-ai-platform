import { Navigate, Route, Routes } from 'react-router-dom'
import { PrivateRoute } from './auth/PrivateRoute'
import { RoleRoute } from './auth/RoleRoute'
import { Layout } from './components/layout/Layout'
import { useAuth } from './hooks/useAuth'
import { AdminPage } from './pages/AdminPage'
import { AgentLab } from './pages/AgentLab'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { AppealDetail } from './pages/AppealDetail'
import { AppealsList } from './pages/AppealsList'
import { AuditLog } from './pages/AuditLog'
import { ClusterDetail } from './pages/ClusterDetail'
import { ClustersPage } from './pages/ClustersPage'
import { Dashboard } from './pages/Dashboard'
import { DraftsPage } from './pages/DraftsPage'
import { LoginPage } from './pages/LoginPage'
import { MyAppealDetail } from './pages/MyAppealDetail'
import { MyAppeals } from './pages/MyAppeals'
import { RegionalMap } from './pages/RegionalMap'
import { RegisterPage } from './pages/RegisterPage'
import { RequesterCard } from './pages/RequesterCard'
import { RequestersPage } from './pages/RequestersPage'
import { AIMonitoring } from './pages/AIMonitoring'
import { ChiefDoctorDashboard } from './pages/ChiefDoctorDashboard'
import { ExecutiveDashboard } from './pages/ExecutiveDashboard'
import { IntegrationCenter } from './pages/IntegrationCenter'
import { IntelligenceCenter } from './pages/IntelligenceCenter'
import { RegionalDashboard } from './pages/RegionalDashboard'
import { SituationCenter } from './pages/SituationCenter'
import { SocialMonitor } from './pages/SocialMonitor'
import { SubmitAppeal } from './pages/SubmitAppeal'

function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user?.role === 'requester' ? '/my-appeals' : '/situation-center'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<PrivateRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<HomeRedirect />} />

          {/* Портал заявителя: доступен всем авторизованным */}
          <Route path="/submit" element={<SubmitAppeal />} />
          <Route path="/my-appeals" element={<MyAppeals />} />
          <Route path="/appeal/:id" element={<MyAppealDetail />} />

          {/* Служебные разделы: сотрудники организации (роль viewer и выше) */}
          <Route element={<RoleRoute minimum="viewer" />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/situation-center" element={<SituationCenter />} />
            <Route path="/chief-doctor" element={<ChiefDoctorDashboard />} />
            <Route path="/regional-dashboard" element={<RegionalDashboard />} />
            <Route path="/appeals" element={<AppealsList />} />
            <Route path="/critical" element={<AppealsList criticalOnly />} />
            <Route path="/appeals/:id" element={<AppealDetail />} />
            <Route path="/clusters" element={<ClustersPage />} />
            <Route path="/clusters/:id" element={<ClusterDetail />} />
            <Route path="/lab" element={<AgentLab />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/regional" element={<RegionalMap />} />
            <Route path="/requesters" element={<RequestersPage />} />
            <Route path="/requesters/:id" element={<RequesterCard />} />
            <Route path="/drafts" element={<DraftsPage />} />
            <Route path="/social" element={<SocialMonitor />} />
            <Route path="/audit" element={<AuditLog />} />
          </Route>

          {/* Операторы и выше: центр интеграций */}
          <Route element={<RoleRoute minimum="operator" />}>
            <Route path="/integrations" element={<IntegrationCenter />} />
          </Route>

          {/* Аналитики и выше: исполнительная панель и AI-мониторинг */}
          <Route element={<RoleRoute minimum="analyst" />}>
            <Route path="/executive" element={<ExecutiveDashboard />} />
            <Route path="/intelligence" element={<IntelligenceCenter />} />
            <Route path="/ai-monitoring" element={<AIMonitoring />} />
          </Route>

          {/* Администрирование */}
          <Route element={<RoleRoute minimum="admin" />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
