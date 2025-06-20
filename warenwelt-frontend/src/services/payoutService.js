import apiClient from './apiClient';

const resource = '/payouts';

export default {
  getPayoutSummary(supplierId) {
    return apiClient.get(`${resource}/summary/${supplierId}`);
  },
  createPayout(payload) {
    // Payload should contain supplier_id
    return apiClient.post(resource, payload);
  },
  getPayouts(params) {
    return apiClient.get(resource, { params });
  },
  getPayout(id) {
    return apiClient.get(`${resource}/${id}`);
  },
};
