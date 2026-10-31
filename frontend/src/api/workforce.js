import apiClient from './client';

export const workforceApi = {
  // Employees
  listEmployees: async ({ page = 1, page_size = 20, search = '', department = '', status = '', sort_by = 'last_name', sort_order = 'asc' } = {}) => {
    const params = { page, page_size, sort_by, sort_order };
    if (search) params.search = search;
    if (department) params.department = department;
    if (status) params.status = status;
    const response = await apiClient.get('/employees', { params });
    return response.data;
  },

  getEmployee: async (id) => {
    const response = await apiClient.get(`/employees/${id}`);
    return response.data;
  },

  createEmployee: async (payload) => {
    const response = await apiClient.post('/employees', payload);
    return response.data;
  },

  updateEmployee: async (id, payload) => {
    const response = await apiClient.put(`/employees/${id}`, payload);
    return response.data;
  },

  deleteEmployee: async (id) => {
    const response = await apiClient.delete(`/employees/${id}`);
    return response.data;
  },

  // Roles
  listRoles: async ({ page = 1, page_size = 50, search = '', department = '' } = {}) => {
    const params = { page, page_size };
    if (search) params.search = search;
    if (department) params.department = department;
    const response = await apiClient.get('/roles', { params });
    return response.data;
  },

  createRole: async (payload) => {
    const response = await apiClient.post('/roles', payload);
    return response.data;
  },

  updateRole: async (id, payload) => {
    const response = await apiClient.put(`/roles/${id}`, payload);
    return response.data;
  },

  // Skills
  listSkills: async ({ page = 1, page_size = 100, search = '', category = '' } = {}) => {
    const params = { page, page_size };
    if (search) params.search = search;
    if (category) params.category = category;
    const response = await apiClient.get('/skills', { params });
    return response.data;
  },

  createSkill: async (payload) => {
    const response = await apiClient.post('/skills', payload);
    return response.data;
  },

  getEmployeeSkills: async (employeeId) => {
    const response = await apiClient.get(`/skills/employee/${employeeId}`);
    return response.data;
  },

  addEmployeeSkill: async (payload) => {
    const response = await apiClient.post('/skills/employee', payload);
    return response.data;
  },

  // Availability & Leave
  listAvailability: async ({ page = 1, page_size = 30, employee_id = '', availability_type = '', is_approved = '' } = {}) => {
    const params = { page, page_size };
    if (employee_id) params.employee_id = employee_id;
    if (availability_type) params.availability_type = availability_type;
    if (is_approved !== '') params.is_approved = is_approved;
    const response = await apiClient.get('/availability', { params });
    return response.data;
  },

  createAvailability: async (payload) => {
    const response = await apiClient.post('/availability', payload);
    return response.data;
  },

  // Training
  listTraining: async ({ page = 1, page_size = 30, employee_id = '', status = '' } = {}) => {
    const params = { page, page_size };
    if (employee_id) params.employee_id = employee_id;
    if (status) params.status = status;
    const response = await apiClient.get('/training', { params });
    return response.data;
  },

  createTraining: async (payload) => {
    const response = await apiClient.post('/training', payload);
    return response.data;
  },
};

export default workforceApi;
