import apiClient from './apiClient';

const API_PATH = '/import'; // Base path for import API, matches backend router prefix

export default {
  /**
   * Imports suppliers from a CSV file.
   * @param {File} file - The CSV file object to upload.
   * @returns {Promise} Resolves with the import result (imported_count, skipped_count, errors).
   */
  importSuppliersCSV(file) {
    if (!(file instanceof File)) {
        return Promise.reject(new Error("Invalid file object provided for supplier import."));
    }
    const formData = new FormData();
    formData.append('csv_file', file, file.name); // filename is important for backend or just good practice

    return apiClient.post(`${API_PATH}/suppliers/csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data' // Axios usually sets this automatically for FormData, but explicit is fine
      }
    });
  },

  /**
   * Imports products from a CSV file.
   * @param {File} file - The CSV file object to upload.
   * @returns {Promise} Resolves with the import result (imported_count, skipped_count, errors).
   */
  importProductsCSV(file) {
    if (!(file instanceof File)) {
        return Promise.reject(new Error("Invalid file object provided for product import."));
    }
    const formData = new FormData();
    formData.append('csv_file', file, file.name);

    return apiClient.post(`${API_PATH}/products/csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};
