import apiClient from './apiClient';

const API_PATH = '/shelves'; // Base path for shelves API, matches backend router prefix

export default {
  /**
   * Get all shelves, optionally filtered.
   * @param {object} params - Query parameters (e.g., skip, limit, shelf_status, is_active)
   * @returns {Promise}
   */
  getAllShelves(params = {}) {
    return apiClient.get(API_PATH, { params });
  },

  /**
   * Get a single shelf by its ID.
   * @param {number|string} shelfId - The ID of the shelf.
   * @returns {Promise}
   */
  getShelfById(shelfId) {
    if (!shelfId) return Promise.reject(new Error("Shelf ID is required."));
    return apiClient.get(`${API_PATH}/${shelfId}`);
  },

  /**
   * Create a new shelf.
   * @param {object} shelfData - Data for the new shelf.
   *   Example: { name: "Regal X", monthly_rent_price: 50.00, status: "AVAILABLE", ... }
   * @returns {Promise}
   */
  createShelf(shelfData) {
    return apiClient.post(API_PATH, shelfData);
  },

  /**
   * Update an existing shelf.
   * @param {number|string} shelfId - The ID of the shelf to update.
   * @param {object} shelfData - Data to update for the shelf.
   * @returns {Promise}
   */
  updateShelf(shelfId, shelfData) {
    if (!shelfId) return Promise.reject(new Error("Shelf ID is required for update."));
    return apiClient.put(`${API_PATH}/${shelfId}`, shelfData);
  },

  /**
   * Delete a shelf.
   * @param {number|string} shelfId - The ID of the shelf to delete.
   * @returns {Promise} Resolves with backend confirmation message.
   */
  deleteShelf(shelfId) {
    if (!shelfId) return Promise.reject(new Error("Shelf ID is required for deletion."));
    return apiClient.delete(`${API_PATH}/${shelfId}`);
  }
};
