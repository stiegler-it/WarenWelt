import apiClient from './apiClient';

const resource = '/sales';

export default {
  createSale(payload) {
    return apiClient.post(resource, payload);
  },
  getSales(params) {
    return apiClient.get(resource, { params });
  },
  getSale(id) {
    return apiClient.get(`${resource}/${id}`);
  },
};
