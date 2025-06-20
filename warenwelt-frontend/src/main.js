import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';

// Simple global CSS (can be expanded)
import './assets/main.css';

const app = createApp(App);

app.use(createPinia()); // Use Pinia for state management
app.use(router);

// Attempt to initialize auth state as soon as the app loads
// This helps if the user reloads the page on a protected route
// Note: The router guard also calls initAuth, this is an early attempt.
// import { useAuthStore } from './store/auth';
// const authStore = useAuthStore(); // This needs to be after app.use(createPinia())
// if (authStore.accessToken && !authStore.user) {
//   authStore.fetchCurrentUser();
// }
// Better to handle this in router.beforeEach or App.vue onMounted

app.mount('#app');
