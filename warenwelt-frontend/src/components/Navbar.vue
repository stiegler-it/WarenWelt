<template>
  <Menubar :model="items">
    <template #end>
      <div class="p-menubar-end-content">
        <span v-if="currentUserEmail" class="user-email p-mr-2">{{ currentUserEmail }}</span>
        <Button label="Logout" icon="pi pi-fw pi-power-off" class="p-button-sm" @click="handleLogout" />
      </div>
    </template>
  </Menubar>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'vue-router';
import Menubar from 'primevue/menubar';
import Button from 'primevue/button';

const authStore = useAuthStore();
const router = useRouter();

const currentUserEmail = computed(() => authStore.user?.email || '');

const handleLogout = () => {
  authStore.logout();
  // Router push to /login is handled by the store's logout action
};

const items = ref([
  {
    label: 'Dashboard',
    icon: 'pi pi-fw pi-home',
    to: '/dashboard'
  },
  {
    label: 'Kasse',
    icon: 'pi pi-fw pi-th-large',
    to: '/pos'
  },
  {
    label: 'Artikel',
    icon: 'pi pi-fw pi-tags',
    to: '/products'
  },
  {
    label: 'Kategorien',
    icon: 'pi pi-fw pi-briefcase',
    to: '/product-categories'
  },
  {
    label: 'Lieferanten',
    icon: 'pi pi-fw pi-users',
    to: '/suppliers'
  },
  {
    label: 'Preisschilder',
    icon: 'pi pi-fw pi-print',
    to: '/products/print-price-tags'
  },
  {
    label: 'Auszahlungen',
    icon: 'pi pi-fw pi-money-bill',
    to: '/payouts'
  },
  {
    label: 'Tagesabschluss',
    icon: 'pi pi-fw pi-chart-bar',
    to: '/reports/daily-summary'
  }
  // Logout is handled separately in the template #end slot
]);

// PrimeVue Menubar uses its own router-link mechanism via the `to` property.
// If direct router.push is needed for some items, command property can be used:
// {
//   label: 'Some Route',
//   icon: 'pi pi-fw pi-cog',
//   command: () => router.push('/some-route')
// }
</script>

<style scoped>
/* Scoped styles for Navbar, if any specific overrides are needed for Menubar */
.p-menubar {
  background-color: #333; /* Example: Set background color */
  border-radius: 0; /* Example: Remove border-radius if you want a full-width bar */
}

/* Styling for the menu items - PrimeVue classes can be targeted for overrides */
:deep(.p-menubar-root-list > .p-menuitem > .p-menuitem-link .p-menuitem-text) {
  color: white !important; /* Example: Change text color of root items */
}
:deep(.p-menubar-root-list > .p-menuitem > .p-menuitem-link .p-menuitem-icon) {
  color: white !important; /* Example: Change icon color of root items */
}

:deep(.p-menuitem-link:hover .p-menuitem-text) {
  color: #ccc !important; /* Example: Change text color on hover */
}
:deep(.p-menuitem-link:hover .p-menuitem-icon) {
  color: #ccc !important; /* Example: Change icon color on hover */
}

.p-menubar-end-content {
  display: flex;
  align-items: center;
  padding-right: 0.5rem; /* Adjust as needed */
}

.user-email {
  color: white;
  margin-right: 1rem; /* Space between email and logout button */
}

/* Ensure the logout button text is visible */
:deep(.p-button .p-button-label) {
    color: white; /* Default state text color */
}

/* You might need to adjust styles for PrimeVue's Button component if it doesn't inherit well */
/* For example, to make the logout button text white if it's not by default in this context */
/* .p-button.p-button-sm { */
  /* color: white; */ /* This might not be specific enough, use :deep if needed */
/* } */

</style>
