<template>
  <div class="login-container">
    <h2>Login</h2>
    <Card class="login-card">
      <template #title>
        <h2 class="text-center">Login</h2>
      </template>
      <template #content>
        <form @submit.prevent="handleLogin">
          <div class="field p-fluid">
            <label for="email">Email</label>
            <InputText id="email" type="email" v-model="email" required />
          </div>
          <div class="field p-fluid">
            <label for="password">Passwort</label>
            <InputText id="password" type="password" v-model="password" required />
          </div>
          <small v-if="errorMessage" class="p-error block mb-2">{{ errorMessage }}</small>
          <Button type="submit" label="Login" :loading="isLoading" class="w-full" />
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useToast } from 'primevue/usetoast'; // Import useToast

// PrimeVue components are globally registered, no need to import Button, InputText, Card here.

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const authStore = useAuthStore();
const toast = useToast(); // Initialize toast

const handleLogin = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    await authStore.login(email.value, password.value);
    // Redirect is handled by the auth store's login action
    // toast.add({ severity: 'success', summary: 'Login erfolgreich', detail: 'Willkommen!', life: 3000 });
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Login fehlgeschlagen. Bitte Zugangsdaten prüfen.';
    toast.add({ severity: 'error', summary: 'Login Fehlgeschlagen', detail: errorMessage.value, life: 5000 });
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-view-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh; /* Adjust as needed */
  padding: 20px;
}
.login-card {
  width: 100%;
  max-width: 450px; /* Max width for the card */
}
.text-center {
  text-align: center;
}
.field {
  margin-bottom: 1.5rem;
}
.p-error.block { /* Ensure error message takes block space */
    display: block;
}
.mb-2 {
    margin-bottom: 0.5rem; /* PrimeFlex class */
}
.w-full { /* PrimeFlex class */
    width: 100%;
}
</style>
