import apiClient from './client';

export const planningApi = {
  // Projects
  listProjects: async ({ page = 1, page_size = 20, search = '', status = '', priority = '' } = {}) => {
    const params = { page, page_size };
    if (search) params.search = search;
    if (status) params.status_filter = status;
    if (priority) params.priority = priority;
    const response = await apiClient.get('/projects', { params });
    return response.data;
  },

  getProject: async (id) => {
    const response = await apiClient.get(`/projects/${id}`);
    return response.data;
  },

  createProject: async (payload) => {
    const response = await apiClient.post('/projects', payload);
    return response.data;
  },

  updateProject: async (id, payload) => {
    const response = await apiClient.put(`/projects/${id}`, payload);
    return response.data;
  },

  deleteProject: async (id) => {
    const response = await apiClient.delete(`/projects/${id}`);
    return response.data;
  },

  // Demand Plans
  listDemand: async ({ page = 1, page_size = 30, project_id = '', status = '', priority = '' } = {}) => {
    const params = { page, page_size };
    if (project_id) params.project_id = project_id;
    if (status) params.status = status;
    if (priority) params.priority = priority;
    const response = await apiClient.get('/demand', { params });
    return response.data;
  },

  createDemand: async (payload) => {
    const response = await apiClient.post('/demand', payload);
    return response.data;
  },

  updateDemand: async (id, payload) => {
    const response = await apiClient.put(`/demand/${id}`, payload);
    return response.data;
  },

  // Allocations
  listAllocations: async ({ page = 1, page_size = 30, project_id = '', employee_id = '', status = '' } = {}) => {
    const params = { page, page_size };
    if (project_id) params.project_id = project_id;
    if (employee_id) params.employee_id = employee_id;
    if (status) params.status = status;
    const response = await apiClient.get('/allocations', { params });
    return response.data;
  },

  createAllocation: async (payload) => {
    const response = await apiClient.post('/allocations', payload);
    return response.data;
  },

  updateAllocation: async (id, payload) => {
    const response = await apiClient.put(`/allocations/${id}`, payload);
    return response.data;
  },

  deleteAllocation: async (id) => {
    const response = await apiClient.delete(`/allocations/${id}`);
    return response.data;
  },
};

export default planningApi;
