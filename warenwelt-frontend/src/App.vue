<template>
  <div id="app-container">
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
/* Global styles - can be moved to assets/main.css */
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background-color: #f4f4f4;
  color: #333;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex-grow: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

header { /* Style for Navbar if needed directly here */
  background-color: #333;
  color: white;
  padding: 1rem;
  text-align: center;
}

nav ul {
  list-style-type: none;
  padding: 0;
  display: flex;
  justify-content: center;
}

nav ul li {
  margin: 0 15px;
}

nav ul li a {
  color: white;
  text-decoration: none;
}

nav ul li a:hover, .nav-button:hover {
  text-decoration: underline;
}

.nav-button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
}


footer {
  text-align: center;
  padding: 10px;
  background-color: #333;
  color: white;
  margin-top: auto; /* Pushes footer to the bottom */
}

/* Basic form styling */
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
}
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group textarea {
  min-height: 80px;
}

button, .button {
  padding: 0.75rem 1.5rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  font-size: 1rem;
}
button:hover, .button:hover {
  background-color: #0056b3;
}
button.secondary, .button.secondary {
  background-color: #6c757d;
}
button.secondary:hover, .button.secondary:hover {
  background-color: #545b62;
}
button.danger, .button.danger {
  background-color: #dc3545;
}
button.danger:hover, .button.danger:hover {
  background-color: #b02a37;
}

.error-message {
  color: red;
  margin-bottom: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f0f0f0;
}
</style>
