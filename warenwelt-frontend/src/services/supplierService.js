import apiClient from './apiClient';

const resource = '/suppliers';

export default {
  getSuppliers(params) {
    return apiClient.get(resource, { params });
  },
  getSupplier(id) {
    return apiClient.get(`${resource}/${id}`);
  },
  createSupplier(payload) {
    return apiClient.post(resource, payload);
  },
  updateSupplier(id, payload) {
    return apiClient.put(`${resource}/${id}`, payload);
  },
  deleteSupplier(id) {
    return apiClient.delete(`${resource}/${id}`);
  },
};
