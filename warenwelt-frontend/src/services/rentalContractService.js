import apiClient from './apiClient';

const API_PATH = '/rental-contracts'; // Base path for rental contracts API

export default {
  /**
   * Get all rental contracts, optionally filtered.
   * @param {object} params - Query parameters (e.g., skip, limit, shelf_id, tenant_supplier_id, contract_status, date filters)
   * @returns {Promise}
   */
  getAllRentalContracts(params = {}) {
    return apiClient.get(API_PATH, { params });
  },

  /**
   * Get a single rental contract by its ID.
   * @param {number|string} contractId - The ID of the rental contract.
   * @returns {Promise}
   */
  getRentalContractById(contractId) {
    if (!contractId) return Promise.reject(new Error("Rental Contract ID is required."));
    return apiClient.get(`${API_PATH}/${contractId}`);
  },

  /**
   * Create a new rental contract.
   * @param {object} contractData - Data for the new rental contract.
   *   Example: { shelf_id: 1, tenant_supplier_id: 1, start_date: "YYYY-MM-DD", end_date: "YYYY-MM-DD", rent_price_at_signing: 45.00, ... }
   * @returns {Promise}
   */
  createRentalContract(contractData) {
    return apiClient.post(API_PATH, contractData);
  },

  /**
   * Update an existing rental contract.
   * @param {number|string} contractId - The ID of the rental contract to update.
   * @param {object} contractData - Data to update for the rental contract.
   * @returns {Promise}
   */
  updateRentalContract(contractId, contractData) {
    if (!contractId) return Promise.reject(new Error("Rental Contract ID is required for update."));
    return apiClient.put(`${API_PATH}/${contractId}`, contractData);
  },

  /**
   * Delete a rental contract.
   * @param {number|string} contractId - The ID of the rental contract to delete.
   * @returns {Promise} Resolves with backend confirmation message.
   */
  deleteRentalContract(contractId) {
    if (!contractId) return Promise.reject(new Error("Rental Contract ID is required for deletion."));
    return apiClient.delete(`${API_PATH}/${contractId}`);
  }
};
