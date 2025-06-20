import axios from 'axios';
import { useAuthStore } from '@/store/auth'; // Pinia store

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1', // Configurable via .env
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const authStore = useAuthStore();
    if (error.response && error.response.status === 401) {
      // Token might be expired or invalid
      authStore.logout(); // Clear token and redirect to login
      // Optionally redirect to login page from here or let the router guard handle it
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
