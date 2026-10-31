import apiClient from './client';

export const intelligenceApi = {
  // Analytics
  calculateCapacity: async (employeeId, startDate, endDate) => {
    const response = await apiClient.post('/analytics/capacity', {
      employee_id: employeeId,
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  },

  calculateUtilization: async (employeeId, startDate, endDate) => {
    const response = await apiClient.post('/analytics/utilization', {
      employee_id: employeeId,
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  },

  getDepartmentUtilization: async (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const response = await apiClient.get('/analytics/department-utilization', { params });
    return response.data;
  },

  listGaps: async ({ page = 1, page_size = 50, project_id = '', severity = '', status = '' } = {}) => {
    const params = { page, page_size };
    if (project_id) params.project_id = project_id;
    if (severity) params.severity = severity;
    if (status) params.status = status;
    const response = await apiClient.get('/analytics/gaps', { params });
    return response.data;
  },

  syncGaps: async () => {
    const response = await apiClient.post('/analytics/sync-gaps');
    return response.data;
  },

  // Forecasting
  getHistoricalForecast: async ({ model_type = 'EXPONENTIAL_SMOOTHING', forecast_horizon_weeks = 12 } = {}) => {
    const response = await apiClient.post('/forecasting/historical', {
      model_type,
      forecast_horizon_weeks,
    });
    return response.data;
  },

  getProjectDemandForecast: async ({ group_by = 'role', start_date = '', end_date = '' } = {}) => {
    const params = { group_by };
    if (start_date) params.start_date = start_date;
    if (end_date) params.end_date = end_date;
    const response = await apiClient.get('/forecasting/project-demand', { params });
    return response.data;
  },

  // Recommendations
  generateRecommendations: async (options = {}) => {
    const response = await apiClient.post('/recommendations/generate', options);
    return response.data;
  },

  listRecommendations: async ({ page = 1, page_size = 20, status = '', type = '' } = {}) => {
    const params = { page, page_size };
    if (status) params.status_filter = status;
    if (type) params.type_filter = type;
    const response = await apiClient.get('/recommendations', { params });
    return response.data;
  },

  approveRecommendation: async (id, reason = 'Approved by manager') => {
    const response = await apiClient.post(`/recommendations/${id}/approve`, { reason });
    return response.data;
  },

  rejectRecommendation: async (id, reason = 'Rejected by manager') => {
    const response = await apiClient.post(`/recommendations/${id}/reject`, { reason });
    return response.data;
  },

  // Scenarios
  listScenarios: async ({ page = 1, page_size = 20 } = {}) => {
    const response = await apiClient.get('/scenarios', { params: { page, page_size } });
    return response.data;
  },

  getScenario: async (id) => {
    const response = await apiClient.get(`/scenarios/${id}`);
    return response.data;
  },

  runScenario: async (payload) => {
    const response = await apiClient.post('/scenarios', payload);
    return response.data;
  },

  // Risks & Exceptions
  listIssues: async ({ page = 1, page_size = 30, severity = '', status = '', issue_type = '' } = {}) => {
    const params = { page, page_size };
    if (severity) params.severity = severity;
    if (status) params.status = status;
    if (issue_type) params.issue_type = issue_type;
    const response = await apiClient.get('/risks/issues', { params });
    return response.data;
  },

  updateIssue: async (id, payload) => {
    const response = await apiClient.put(`/risks/issues/${id}`, payload);
    return response.data;
  },

  runRiskScan: async () => {
    const response = await apiClient.post('/risks/scan');
    return response.data;
  },

  // Audit History
  listAuditEvents: async ({ page = 1, page_size = 20, action = '', entity_type = '' } = {}) => {
    const params = { page, page_size };
    if (action) params.action = action;
    if (entity_type) params.entity_type = entity_type;
    const response = await apiClient.get('/audit', { params });
    return response.data;
  },

  // Quality & Evaluation
  getValidationReport: async () => {
    const response = await apiClient.get('/quality/validation');
    return response.data;
  },

  runReproducibility: async () => {
    const response = await apiClient.get('/quality/reproducibility');
    return response.data;
  },

  getAnomalyEvaluation: async () => {
    const response = await apiClient.get('/evaluation/anomaly-detection');
    return response.data;
  },
};

export default intelligenceApi;
