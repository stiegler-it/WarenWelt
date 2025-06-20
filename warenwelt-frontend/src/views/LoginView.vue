<template>
  <div class="login-container">
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" v-model="email" required />
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/store/auth';

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const authStore = useAuthStore();

const handleLogin = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    await authStore.login(email.value, password.value);
    // Redirect is handled by the auth store's login action
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Login failed. Please check your credentials.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h2 {
  text-align: center;
  margin-bottom: 20px;
}

/* .form-group styles are global in App.vue or main.css */
/* button styles are global */

.error-message {
  color: red;
  margin-bottom: 1rem;
  text-align: center;
}
</style>
