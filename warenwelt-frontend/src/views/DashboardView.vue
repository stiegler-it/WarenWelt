<template>
  <div class="dashboard">
    <h1>Willkommen bei WarenWelt!</h1>
    <p v-if="authStore.user">
      Angemeldet als: <strong>{{ authStore.user.full_name || authStore.user.email }}</strong>
      <span v-if="authStore.user.role"> (Rolle: {{ authStore.user.role.name }})</span>
    </p>
    <p>Dies ist dein Dashboard. Wähle eine Aktion aus der Navigation.</p>

    <div class="quick-actions">
      <router-link to="/pos" class="button">Zur Kasse</router-link>
      <router-link to="/products/new" class="button secondary">Neuen Artikel erfassen</router-link>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/store/auth';
const authStore = useAuthStore();

// Fetch user details if not already present (e.g., after page reload)
// This is also handled in App.vue and router, but can be an additional check.
// import { onMounted } from 'vue';
// onMounted(async () => {
//   if (!authStore.user && authStore.isAuthenticated) {
//     await authStore.fetchCurrentUser();
//   }
// });
</script>

<style scoped>
.dashboard {
  text-align: center;
}
.quick-actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 20px; /* Adds space between buttons */
}
/* .button styles are global */
</style>
