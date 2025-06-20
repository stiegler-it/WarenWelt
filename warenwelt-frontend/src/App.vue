<template>
  <div id="app-container">
    <Toast position="top-right" />
    <ConfirmDialog />
    <Navbar v.if="authStore.isAuthenticated" />
    <main class="main-content">
      <router-view />
    </main>
    <footer>
      <p>&copy; {{ new Date().getFullYear() }} WarenWelt</p>
    </footer>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import Navbar from '@/components/Navbar.vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

// Initialize auth state when App component is mounted
// This helps ensure user data is loaded if a token exists from localStorage
onMounted(async () => {
  if (authStore.accessToken && !authStore.user) {
    await authStore.fetchCurrentUser();
  }
});
</script>

<style>
/* Global styles - to be minimized when using PrimeVue extensively */
body {
  margin: 0;
  font-family: var(--font-family); /* Use PrimeVue's font family */
  background-color: var(--surface-ground); /* Use PrimeVue's background color */
  color: var(--text-color); /* Use PrimeVue's text color */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex-grow: 1;
  /* Padding can be managed by PrimeFlex classes on a per-view basis e.g. p-p-4 */
  /* max-width: 1200px; */ /* This can be handled by layout containers if needed */
  /* margin: 0 auto; */
  /* width: 100%; */
}

footer {
  text-align: center;
  padding: 1rem; /* Use consistent spacing */
  background-color: var(--surface-section); /* Example using a PrimeVue variable */
  color: var(--text-color);
  border-top: 1px solid var(--surface-border);
  margin-top: auto; /* Pushes footer to the bottom */
}

/* Basic helper classes that might still be useful if not covered by PrimeFlex */
.loading {
  text-align: center;
  padding: 20px;
  color: var(--text-color-secondary);
}
.error-message {
  color: var(--red-500); /* PrimeVue color variable */
  margin-bottom: 1rem;
  /* Consider using p-message for inline errors or Toast for global errors */
}
.success-message {
  color: var(--green-500); /* PrimeVue color variable */
  margin-bottom: 1rem;
}

/*
  Most form, button, table styles are now handled by PrimeVue components.
  Customizations should be done via PrimeVue's theming/styling capabilities
  or by targeting PrimeVue's specific classes carefully.
  Avoid overly broad selectors that might conflict.

  Example:
  .p-button { // Targets all PrimeVue buttons
    // custom styles...
  }
  .p-datatable .p-datatable-thead > tr > th { // Targets DataTable headers
    // custom styles...
  }
*/
</style>
