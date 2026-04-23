import axios from "axios";
import { useAuthStore } from "@/stores/authStore";

// Production: set VITE_API_BASE_URL to your deployed API origin (e.g. https://api-xx.up.railway.app)
// with no trailing slash. Vite inlines this at build time from .env.production.
const baseRoot = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const baseURL = `${baseRoot}/api/v1`;

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Attach bearer token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Refresh once on 401, then auto-logout if refresh fails.
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err.response?.status;
    const original = (err.config || {}) as {
      _retry?: boolean;
      url?: string;
      headers?: Record<string, string>;
    };
    const isAuthPath = String(original?.url || "").includes("/auth/");
    const alreadyRetried = Boolean(original?._retry);

    if (status === 401 && !isAuthPath && !alreadyRetried) {
      original._retry = true;
      const { refreshToken, user, setAuth, logout } = useAuthStore.getState();
      if (!refreshToken || !user) {
        logout();
        window.location.href = "/login";
        return Promise.reject(err);
      }
      try {
        const refresh = await api.post("/auth/refresh", { refresh_token: refreshToken });
        const tokens = refresh.data;
        setAuth(user, tokens.access_token, tokens.refresh_token);
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${tokens.access_token}`;
        return api.request(original);
      } catch (_refreshError) {
        logout();
        window.location.href = "/login";
        return Promise.reject(err);
      }
    }

    if (status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    api.post("/auth/login", { username, password }).then((r) => r.data),
  refresh: (refreshToken: string) =>
    api.post("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data),
  logout: () => api.post("/auth/logout"),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data),
  mfaEnroll: () => api.post("/auth/mfa/enroll").then((r) => r.data),
  mfaVerify: (code: string) => api.post("/auth/mfa/verify", { code }).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
};

export const usersApi = {
  listUsers: () => api.get("/users").then((r) => r.data),
  createUser: (data: unknown) => api.post("/users", data).then((r) => r.data),
  updateUser: (userId: string, data: unknown) => api.patch(`/users/${userId}`, data).then((r) => r.data),
  deactivateUser: (userId: string) => api.post(`/users/${userId}/deactivate`).then((r) => r.data),
  assignRole: (userId: string, roleId: string) =>
    api.post(`/users/${userId}/roles/${roleId}`).then((r) => r.data),
  revokeRole: (userId: string, roleId: string) =>
    api.delete(`/users/${userId}/roles/${roleId}`).then((r) => r.data),
};

export const rolesApi = {
  listRoles: () => api.get("/users/roles").then((r) => r.data),
  createRole: (data: unknown) => api.post("/users/roles", data).then((r) => r.data),
  updateRole: (roleId: string, data: unknown) =>
    api.patch(`/users/roles/${roleId}`, data).then((r) => r.data),
  deleteRole: (roleId: string) => api.delete(`/users/roles/${roleId}`).then((r) => r.data),
  listPermissions: () => api.get("/users/permissions").then((r) => r.data),
};

// ── QMS ──────────────────────────────────────────────────────────────────────
export const qmsApi = {
  // CAPAs
  listCapas: (params?: Record<string, string | number>) =>
    api.get("/qms/capas", { params }).then((r) => r.data),
  getCapa: (id: string) => api.get(`/qms/capas/${id}`).then((r) => r.data),
  createCapa: (data: unknown) => api.post("/qms/capas", data).then((r) => r.data),
  updateCapa: (id: string, data: unknown) =>
    api.patch(`/qms/capas/${id}`, data).then((r) => r.data),
  signCapa: (id: string, data: unknown) =>
    api.post(`/qms/capas/${id}/sign`, data).then((r) => r.data),
  addCapaAction: (id: string, data: unknown) =>
    api.post(`/qms/capas/${id}/actions`, data).then((r) => r.data),
  updateCapaAction: (capaId: string, actionId: string, data: unknown) =>
    api.patch(`/qms/capas/${capaId}/actions/${actionId}`, data).then((r) => r.data),
  listCapaAuditTrail: (id: string) =>
    api.get(`/qms/capas/${id}/audit-trail`).then((r) => r.data),

  // Deviations
  listDeviations: (params?: Record<string, string | number>) =>
    api.get("/qms/deviations", { params }).then((r) => r.data),
  getDeviation: (id: string) => api.get(`/qms/deviations/${id}`).then((r) => r.data),
  createDeviation: (data: unknown) =>
    api.post("/qms/deviations", data).then((r) => r.data),
  updateDeviation: (id: string, data: unknown) =>
    api.patch(`/qms/deviations/${id}`, data).then((r) => r.data),
  signDeviation: (id: string, data: unknown) =>
    api.post(`/qms/deviations/${id}/sign`, data).then((r) => r.data),
  listDeviationAuditTrail: (id: string) =>
    api.get(`/qms/deviations/${id}/audit-trail`).then((r) => r.data),
  transitionDeviation: (id: string, action: "submit" | "approve" | "close") =>
    api.post(`/qms/deviations/${id}/${action}`).then((r) => r.data),

  // Change Controls
  listChangeControls: (params?: Record<string, string | number>) =>
    api.get("/qms/change-controls", { params }).then((r) => r.data),
  getChangeControl: (id: string) =>
    api.get(`/qms/change-controls/${id}`).then((r) => r.data),
  createChangeControl: (data: unknown) =>
    api.post("/qms/change-controls", data).then((r) => r.data),
  updateChangeControl: (id: string, data: unknown) =>
    api.patch(`/qms/change-controls/${id}`, data).then((r) => r.data),
  signChangeControl: (id: string, data: unknown) =>
    api.post(`/qms/change-controls/${id}/sign`, data).then((r) => r.data),
  listChangeControlAuditTrail: (id: string) =>
    api.get(`/qms/change-controls/${id}/audit-trail`).then((r) => r.data),
  transitionChangeControl: (
    id: string,
    action: "submit" | "approve" | "implement" | "review_effectiveness" | "close"
  ) => api.post(`/qms/change-controls/${id}/${action}`).then((r) => r.data),
};

// ── MES ──────────────────────────────────────────────────────────────────────
export const mesApi = {
  // Products
  listProducts: (params?: Record<string, string | number>) =>
    api.get("/mes/products", { params }).then((r) => r.data),
  createProduct: (data: unknown) =>
    api.post("/mes/products", data).then((r) => r.data),

  // Master Batch Records
  listMBRs: (params?: Record<string, string | number>) =>
    api.get("/mes/mbrs", { params }).then((r) => r.data),
  getMBR: (id: string) => api.get(`/mes/mbrs/${id}`).then((r) => r.data),
  createMBR: (data: unknown) => api.post("/mes/mbrs", data).then((r) => r.data),
  signMBR: (id: string, data: unknown) =>
    api.post(`/mes/mbrs/${id}/sign`, data).then((r) => r.data),

  // Batch Records
  listBatchRecords: (params?: Record<string, string | number>) =>
    api.get("/mes/batch-records", { params }).then((r) => r.data),
  getBatchRecord: (id: string) =>
    api.get(`/mes/batch-records/${id}`).then((r) => r.data),
  createBatchRecord: (data: unknown) =>
    api.post("/mes/batch-records", data).then((r) => r.data),
  executeStep: (batchId: string, stepId: string, data: unknown) =>
    api
      .patch(`/mes/batch-records/${batchId}/steps/${stepId}`, data)
      .then((r) => r.data),
  releaseBatchRecord: (id: string, data: unknown) =>
    api.post(`/mes/batch-records/${id}/release`, data).then((r) => r.data),
};

// ── Equipment ────────────────────────────────────────────────────────────────
export const equipmentApi = {
  listEquipment: (params?: Record<string, string | number>) =>
    api.get("/equipment", { params }).then((r) => r.data),
  getEquipment: (id: string) => api.get(`/equipment/${id}`).then((r) => r.data),
  createEquipment: (data: unknown) =>
    api.post("/equipment", data).then((r) => r.data),
  updateStatus: (id: string, data: unknown) =>
    api.patch(`/equipment/${id}/status`, data).then((r) => r.data),

  // Calibration
  listCalibrations: (equipmentId: string) =>
    api.get(`/equipment/${equipmentId}/calibrations`).then((r) => r.data),
  addCalibration: (equipmentId: string, data: unknown) =>
    api.post(`/equipment/${equipmentId}/calibrations`, data).then((r) => r.data),

  // Qualifications
  listQualifications: (equipmentId: string) =>
    api.get(`/equipment/${equipmentId}/qualifications`).then((r) => r.data),
  addQualification: (equipmentId: string, data: unknown) =>
    api
      .post(`/equipment/${equipmentId}/qualifications`, data)
      .then((r) => r.data),

  // Maintenance
  listMaintenance: (equipmentId: string) =>
    api.get(`/equipment/${equipmentId}/maintenance`).then((r) => r.data),
  addMaintenance: (equipmentId: string, data: unknown) =>
    api.post(`/equipment/${equipmentId}/maintenance`, data).then((r) => r.data),
};

// ── Training ─────────────────────────────────────────────────────────────────
export const trainingApi = {
  // Curricula
  listCurricula: (params?: Record<string, string | number>) =>
    api.get("/training/curricula", { params }).then((r) => r.data),
  getCurriculum: (id: string) =>
    api.get(`/training/curricula/${id}`).then((r) => r.data),
  createCurriculum: (data: unknown) =>
    api.post("/training/curricula", data).then((r) => r.data),

  // Assignments
  myAssignments: () =>
    api.get("/training/assignments/my").then((r) => r.data),
  listAssignments: (params?: Record<string, string | number>) =>
    api.get("/training/assignments", { params }).then((r) => r.data),
  getAssignment: (id: string) =>
    api.get(`/training/assignments/${id}`).then((r) => r.data),
  createAssignment: (data: unknown) =>
    api.post("/training/assignments", data).then((r) => r.data),

  // Completion
  complete: (assignmentId: string, data: unknown) =>
    api
      .post(`/training/assignments/${assignmentId}/complete`, data)
      .then((r) => r.data),
  readAndUnderstood: (assignmentId: string, data: unknown) =>
    api
      .post(`/training/assignments/${assignmentId}/read-and-understood`, data)
      .then((r) => r.data),
};

// ── Documents ────────────────────────────────────────────────────────────────
export const documentsApi = {
  listTypes: () => api.get("/documents/types").then((r) => r.data),
  listDocuments: (params?: Record<string, string | number>) =>
    api.get("/documents", { params }).then((r) => r.data),
  getDocument: (id: string) => api.get(`/documents/${id}`).then((r) => r.data),
  createDocument: (data: unknown) =>
    api.post("/documents", data).then((r) => r.data),

  // Versions
  listVersions: (docId: string) =>
    api.get(`/documents/${docId}/versions`).then((r) => r.data),
  createVersion: (docId: string, data: unknown) =>
    api.post(`/documents/${docId}/versions`, data).then((r) => r.data),
  signVersion: (docId: string, versionId: string, data: unknown) =>
    api
      .post(`/documents/${docId}/versions/${versionId}/sign`, data)
      .then((r) => r.data),
};

// ── Environmental Monitoring ──────────────────────────────────────────────────
export const envMonitoringApi = {
  listLocations: (params?: Record<string, string | number>) =>
    api.get("/env-monitoring/locations", { params }).then((r) => r.data),
  createLocation: (data: unknown) =>
    api.post("/env-monitoring/locations", data).then((r) => r.data),
  setAlertLimits: (locationId: string, data: unknown) =>
    api
      .post(`/env-monitoring/locations/${locationId}/limits`, data)
      .then((r) => r.data),

  listResults: (params?: Record<string, string | number>) =>
    api.get("/env-monitoring/results", { params }).then((r) => r.data),
  recordResult: (locationId: string, data: unknown) =>
    api.post(`/env-monitoring/locations/${locationId}/results`, data).then((r) => r.data),
};

// ── LIMS ─────────────────────────────────────────────────────────────────────
export const limsApi = {
  listSpecifications: (params?: Record<string, string | number>) =>
    api.get("/lims/specifications", { params }).then((r) => r.data),
  createSpecification: (data: unknown) =>
    api.post("/lims/specifications", data).then((r) => r.data),

  listSamples: (params?: Record<string, string | number>) =>
    api.get("/lims/samples", { params }).then((r) => r.data),
  getSample: (id: string) => api.get(`/lims/samples/${id}`).then((r) => r.data),
  listResults: (sampleId: string) =>
    api.get(`/lims/samples/${sampleId}/results`).then((r) => r.data),
  createSample: (data: unknown) =>
    api.post("/lims/samples", data).then((r) => r.data),

  addResult: (sampleId: string, data: unknown) =>
    api.post(`/lims/samples/${sampleId}/results`, data).then((r) => r.data),
  reviewResult: (_sampleId: string, resultId: string, data: unknown) =>
    api
      .post(`/lims/results/${resultId}/review`, data)
      .then((r) => r.data),
};

export const dashboardApi = {
  summary: () => api.get("/dashboard/summary").then((r) => r.data),
};
