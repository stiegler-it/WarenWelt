import apiClient from './apiClient';

const API_PATH = '/reports'; // Base path for reports API, matches backend router prefix

export default {
  /**
   * Get the daily sales summary report.
   * @param {string} reportDate - The date for the report in 'YYYY-MM-DD' format.
   * @returns {Promise}
   */
  getDailySalesReport(reportDate) {
    if (!reportDate) return Promise.reject(new Error("Report date is required."));
    return apiClient.get(`${API_PATH}/sales/summary/daily`, { params: { report_date: reportDate } });
  },

  /**
   * Get the weekly sales summary report.
   * @param {string} targetDateForWeek - A date within the desired week in 'YYYY-MM-DD' format.
   * @returns {Promise}
   */
  getWeeklySalesReport(targetDateForWeek) {
    if (!targetDateForWeek) return Promise.reject(new Error("Target date for week is required."));
    return apiClient.get(`${API_PATH}/sales/summary/weekly`, { params: { target_date_for_week: targetDateForWeek } });
  },

  /**
   * Get the monthly sales summary report.
   * @param {number} year - The year for the report (e.g., 2024).
   * @param {number} month - The month for the report (1-12).
   * @returns {Promise}
   */
  getMonthlySalesReport(year, month) {
    if (!year || !month) return Promise.reject(new Error("Year and month are required."));
    return apiClient.get(`${API_PATH}/sales/summary/monthly`, { params: { year, month } });
  },

  /**
   * Get the detailed revenue list report for a period.
   * @param {string} startDate - The start date for the period in 'YYYY-MM-DD' format.
   * @param {string} endDate - The end date for the period in 'YYYY-MM-DD' format.
   * @returns {Promise}
   */
  getRevenueListReport(startDate, endDate) {
    if (!startDate || !endDate) return Promise.reject(new Error("Start date and end date are required."));
    return apiClient.get(`${API_PATH}/revenue/list`, { params: { start_date: startDate, end_date: endDate } });
  },

  // --- CSV Export Functions ---

  /**
   * Download the daily sales summary as a CSV file.
   * @param {string} reportDate - 'YYYY-MM-DD'
   * @returns {Promise<Blob>}
   */
  downloadDailySalesSummaryCSV(reportDate) {
    if (!reportDate) return Promise.reject(new Error("Report date is required for CSV export."));
    return apiClient.get(`${API_PATH}/export/daily-sales-summary/csv`, {
      params: { report_date: reportDate },
      responseType: 'blob' // Axios will handle the response as a Blob
    });
  },

  /**
   * Download the monthly sales summary as a CSV file.
   * @param {number} year
   * @param {number} month
   * @returns {Promise<Blob>}
   */
  downloadMonthlySalesSummaryCSV(year, month) {
    if (!year || !month) return Promise.reject(new Error("Year and month are required for CSV export."));
    return apiClient.get(`${API_PATH}/export/monthly-sales-summary/csv`, {
      params: { year, month },
      responseType: 'blob'
    });
  },

  /**
   * Download the revenue list in a DATEV-like CSV format.
   * @param {string} startDate - 'YYYY-MM-DD'
   * @param {string} endDate - 'YYYY-MM-DD'
   * @returns {Promise<Blob>}
   */
  downloadRevenueListDatevLikeCSV(startDate, endDate) {
    if (!startDate || !endDate) return Promise.reject(new Error("Start date and end date are required for CSV export."));
    return apiClient.get(`${API_PATH}/export/revenue-list/datev-like/csv`, {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob'
    });
  }
};
