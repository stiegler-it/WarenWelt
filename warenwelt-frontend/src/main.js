import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';

// Simple global CSS (can be expanded)
import './assets/main.css';

// PrimeVue CSS
import 'primevue/resources/themes/lara-light-indigo/theme.css'; // Choose your theme
// import 'primevue/resources/themes/saga-blue/theme.css'; // Alternative Theme
import 'primevue/resources/primevue.min.css'; // Core CSS
import 'primeicons/primeicons.css'; // Icons
import 'primeflex/primeflex.css'; // PrimeFlex utility classes

import PrimeVue from 'primevue/config';
// Import PrimeVue components globally or locally as needed.
// For MVP Phase 2, let's import some common ones globally for ease of use.
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Card from 'primevue/card';
import ToastService from 'primevue/toastservice';
import Toast from 'primevue/toast';
import Dropdown from 'primevue/dropdown';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import Checkbox from 'primevue/checkbox';
import Dialog from 'primevue/dialog';
import ConfirmDialog from 'primevue/confirmdialog';
import ConfirmationService from 'primevue/confirmationservice';


const app = createApp(App);

app.use(createPinia()); // Use Pinia for state management
app.use(router);
app.use(PrimeVue, { ripple: true }); // ripple: true for ripple effect on components
app.use(ToastService);
app.use(ConfirmationService);

// Register components globally
app.component('Button', Button);
app.component('InputText', InputText);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('Card', Card);
app.component('Toast', Toast);
app.component('Dropdown', Dropdown);
app.component('InputNumber', InputNumber);
app.component('Textarea', Textarea);
app.component('Checkbox', Checkbox);
app.component('Dialog', Dialog);
app.component('ConfirmDialog', ConfirmDialog);

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
