import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import Layout from "@/components/core/Layout";
import Login from "@/pages/Login";
import ChangePassword from "@/pages/ChangePassword";
import Security from "@/pages/Security";
import Dashboard from "@/pages/Dashboard";
import UsersAdmin from "@/pages/admin/UsersAdmin";
import RolesAdmin from "@/pages/admin/RolesAdmin";

// QMS
import CAPAList from "@/pages/qms/CAPAList";
import CAPADetail from "@/pages/qms/CAPADetail";
import DeviationList from "@/pages/qms/DeviationList";
import DeviationDetail from "@/pages/qms/DeviationDetail";
import ChangeControlList from "@/pages/qms/ChangeControlList";
import ChangeControlDetail from "@/pages/qms/ChangeControlDetail";

// MES
import BatchRecordList from "@/pages/mes/BatchRecordList";

// Equipment
import EquipmentList from "@/pages/equipment/EquipmentList";
import EquipmentDetail from "@/pages/equipment/EquipmentDetail";

// Training
import TrainingList from "@/pages/training/TrainingList";
import TrainingDetail from "@/pages/training/TrainingDetail";

// Documents
import DocumentList from "@/pages/documents/DocumentList";
import DocumentDetail from "@/pages/documents/DocumentDetail";

// Environmental Monitoring
import EnvMonitoringList from "@/pages/env_monitoring/EnvMonitoringList";

// LIMS
import SampleList from "@/pages/lims/SampleList";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PasswordGate({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  if (user.must_change_password) return <Navigate to="/change-password" replace />;
  return <>{children}</>;
}

function PermissionRoute({ code, children }: { code: string; children: React.ReactNode }) {
  const hasPermission = useAuthStore((s) => s.hasPermission(code));
  return hasPermission ? <>{children}</> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePassword />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <PasswordGate>
              <Layout />
            </PasswordGate>
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />

        {/* QMS */}
        <Route path="qms/capas" element={<CAPAList />} />
        <Route path="qms/capas/:id" element={<CAPADetail />} />
        <Route path="qms/deviations" element={<DeviationList />} />
        <Route path="qms/deviations/:id" element={<DeviationDetail />} />
        <Route path="qms/change-controls" element={<ChangeControlList />} />
        <Route path="qms/change-controls/:id" element={<ChangeControlDetail />} />

        {/* MES */}
        <Route path="mes/batch-records" element={<BatchRecordList />} />

        {/* Equipment */}
        <Route path="equipment" element={<EquipmentList />} />
        <Route path="equipment/:id" element={<EquipmentDetail />} />

        {/* Training */}
        <Route path="training" element={<TrainingList />} />
        <Route path="training/:id" element={<TrainingDetail />} />

        {/* Documents */}
        <Route path="documents" element={<DocumentList />} />
        <Route path="documents/:id" element={<DocumentDetail />} />

        {/* Environmental Monitoring */}
        <Route path="env-monitoring" element={<EnvMonitoringList />} />

        {/* LIMS */}
        <Route path="lims/samples" element={<SampleList />} />
        <Route path="security" element={<Security />} />

        {/* Admin */}
        <Route
          path="admin/users"
          element={
            <PermissionRoute code="admin.users.manage">
              <UsersAdmin />
            </PermissionRoute>
          }
        />
        <Route
          path="admin/roles"
          element={
            <PermissionRoute code="admin.roles.manage">
              <RolesAdmin />
            </PermissionRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
