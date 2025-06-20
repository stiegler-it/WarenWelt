import apiClient from './apiClient';

const resource = '/product-categories';

export default {
  getProductCategories(params) {
    return apiClient.get(resource, { params });
  },
  getProductCategory(id) {
    return apiClient.get(`${resource}/${id}`);
  },
  createProductCategory(payload) {
    return apiClient.post(resource, payload);
  },
  updateProductCategory(id, payload) {
    return apiClient.put(`${resource}/${id}`, payload);
  },
  deleteProductCategory(id) {
    // Be cautious with deleting categories if products are associated
    return apiClient.delete(`${resource}/${id}`);
  },
};
