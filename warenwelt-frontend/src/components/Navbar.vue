<template>
  <header class="navbar">
    <nav>
      <ul>
        <li><router-link to="/dashboard">Dashboard</router-link></li>
        <li><router-link to="/pos">Kasse</router-link></li>
        <li><router-link to="/products">Artikel</router-link></li>
        <li><router-link to="/product-categories">Kategorien</router-link></li>
        <li><router-link to="/suppliers">Lieferanten</router-link></li>
        <li><router-link to="/products/print-price-tags">Preisschilder</router-link></li>
        <li><router-link to="/payouts">Auszahlungen</router-link></li>
        <li><router-link to="/reports/daily-summary">Tagesabschluss</router-link></li>
        <li><button @click="handleLogout" class="nav-button">Logout ({{ currentUserEmail }})</button></li>
      </ul>
    </nav>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const currentUserEmail = computed(() => authStore.user?.email || '');

const handleLogout = () => {
  authStore.logout();
  // Router push to /login is handled by the store's logout action
};
</script>

<style scoped>
.navbar {
  background-color: #333; /* Match App.vue header style or define uniquely */
  color: white;
  padding: 1rem;
  /* text-align: center; */ /* Removed to allow ul to center itself better */
}

nav ul {
  list-style-type: none;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center; /* Vertically align items */
  margin: 0; /* Reset margin for ul */
}

nav ul li {
  margin: 0 15px;
}

nav ul li a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 0; /* Add some padding for better clickability */
}

nav ul li a:hover, .nav-button:hover {
  text-decoration: underline;
}

.nav-button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: inherit; /* Ensure same size as links */
  font-family: inherit;
  padding: 0.5rem 0; /* Match link padding */
}
</style>
