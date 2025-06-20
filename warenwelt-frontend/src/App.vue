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
/* Global styles using PrimeFlex and some baseline settings */
body {
  margin: 0;
  font-family: var(--font-family); /* PrimeVue should set this */
  background-color: var(--surface-ground, #f4f4f4); /* Using PrimeVue surface colors */
  color: var(--text-color, #333); /* Using PrimeVue text colors */
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
  padding: 1rem; /* Adjusted padding, PrimeFlex spacers can also be used */
  /* max-width: 1200px; */ /* Consider if this is still needed or handled by layout components */
  /* margin: 0 auto; */
  /* width: 100%; */
}

/* Footer styling remains, but could also be a PrimeVue component like Toolbar */
footer {
  text-align: center;
  padding: 1rem;
  background-color: var(--surface-section, #333); /* Example: using a PrimeVue surface color */
  color: var(--text-color-inverse, white); /* Example: for text on dark backgrounds */
  margin-top: auto; /* Pushes footer to the bottom */
}

/*
  The following styles are largely replaced by PrimeVue components and PrimeFlex utilities:
  - header specific styles (Menubar has its own styling)
  - nav ul, nav ul li, nav ul li a (Menubar handles this)
  - .nav-button (Menubar handles this)
  - Basic form styling (.form-group, input, select, textarea) -> Use p-fluid, p-field, PrimeVue form components
  - button, .button styling -> Use p-button
  - .error-message -> Can be handled with PrimeVue's Message or Toast
  - table, th, td styling -> Use PrimeVue DataTable
*/

/* Global error message styling if not using Toast/Message for all errors */
.error-message {
  color: var(--red-500, red); /* Using PrimeVue color variables */
  margin-bottom: 1rem;
}

/* Add some base styling for links if needed, though PrimeVue components manage their own */
a {
  color: var(--primary-color, #007bff);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
