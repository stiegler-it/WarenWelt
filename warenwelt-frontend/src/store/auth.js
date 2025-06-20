import { defineStore } from 'pinia';
import authService from '@/services/authService';
import router from '@/router'; // To redirect after login/logout

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('accessToken') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    returnUrl: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    currentUser: (state) => state.user,
  },
  actions: {
    async login(email, password) {
      try {
        const response = await authService.login(email, password);
        this.accessToken = response.data.access_token;
        localStorage.setItem('accessToken', this.accessToken);

        // Fetch user details after successful login
        await this.fetchCurrentUser();

        // Redirect to previous url or default to dashboard
        router.push(this.returnUrl || '/dashboard');
      } catch (error) {
        this.accessToken = null;
        this.user = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        // console.error('Login failed:', error.response?.data?.detail || error.message);
        throw error; // Re-throw to be caught by the component
      }
    },
    async fetchCurrentUser() {
      if (this.accessToken) {
        try {
          const userResponse = await authService.getCurrentUser();
          this.user = userResponse.data;
          localStorage.setItem('user', JSON.stringify(this.user));
        } catch (error) {
          // console.error('Failed to fetch current user:', error);
          // Potentially logout if user fetch fails (e.g. token invalid)
          this.logout();
        }
      }
    },
    logout() {
      this.accessToken = null;
      this.user = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('user');
      router.push('/login');
    },
    // Action to be called by router guard if token exists but user is not fetched
    async initAuth() {
      if (this.accessToken && !this.user) {
        await this.fetchCurrentUser();
      }
    }
  },
});
