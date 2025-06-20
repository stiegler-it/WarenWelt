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
  getDailySummary(date) { // date should be in YYYY-MM-DD format
    return apiClient.get(`${resource}/summary/daily`, { params: { report_date: date } });
  }
};
