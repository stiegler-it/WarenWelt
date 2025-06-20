import apiClient from './apiClient';

const resource = '/products';
const taxRateResource = '/tax-rates'; // For fetching tax rates
const categoryResource = '/product-categories'; // For fetching categories


export default {
  getProducts(params) {
    return apiClient.get(resource, { params });
  },
  getProduct(id) {
    return apiClient.get(`${resource}/${id}`);
  },
  getProductBySku(sku) {
    return apiClient.get(`${resource}/sku/${sku}`);
  },
  createProduct(payload) {
    return apiClient.post(resource, payload);
  },
  updateProduct(id, payload) {
    return apiClient.put(`${resource}/${id}`, payload);
  },
  deleteProduct(id) {
    return apiClient.delete(`${resource}/${id}`);
  },
  // Helper to get related data for product forms
  getTaxRates(params) {
    return apiClient.get(taxRateResource, { params });
  },
  getProductCategories(params) {
    return apiClient.get(categoryResource, { params });
  },
  uploadProductImage(productId, file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`${resource}/${productId}/upload-image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getPriceTagData(productId) {
    return apiClient.get(`${resource}/${productId}/price-tag`);
  }
};
