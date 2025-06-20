<template>
  <Menubar :model="items" class="warenwelt-menubar">
    <template #start>
      <router-link to="/dashboard" class="p-menubar-item-link">
        <img alt="logo" src="/favicon.ico" height="40" class="mr-2" />
        <span class="font-bold">WarenWelt</span>
      </router-link>
    </template>
    <template #end>
      <div class="flex align-items-center">
        <span class="mr-3" v-if="authStore.user">
          Angemeldet als: {{ authStore.user.full_name || authStore.user.email }}
        </span>
        <Button icon="pi pi-sign-out" label="Logout" @click="handleLogout" class="p-button-sm p-button-text" />
      </div>
    </template>
  </Menubar>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'vue-router';
import Menubar from 'primevue/menubar'; // Import Menubar

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
};

// Define menu items reactively based on auth state or roles if needed
const items = ref([
  {
    label: 'Dashboard',
    icon: 'pi pi-fw pi-home',
    to: '/dashboard'
  },
  {
    label: 'Kasse',
    icon: 'pi pi-fw pi-shopping-cart',
    to: '/pos'
  },
  {
    label: 'Stammdaten',
    icon: 'pi pi-fw pi-database',
    items: [
        { label: 'Artikel', icon: 'pi pi-fw pi-tags', to: '/products' },
        { label: 'Kategorien', icon: 'pi pi-fw pi-bookmark', to: '/product-categories' },
        { label: 'Lieferanten', icon: 'pi pi-fw pi-users', to: '/suppliers' },
    ]
  },
  {
    label: 'Regalvermietung',
    icon: 'pi pi-fw pi-th-large', // Icon for shelves/layout
    items: [
        { label: 'Regalübersicht', icon: 'pi pi-fw pi-table', to: '/shelves'},
        { label: 'Mietverträge', icon: 'pi pi-fw pi-file-edit', to: '/rental-contracts'}
        // TODO: Add Rental Invoices link later: { label: 'Mietrechnungen', icon: 'pi pi-fw pi-dollar', to: '/rental-invoices'}
    ]
  },
   {
    label: 'Funktionen',
    icon: 'pi pi-fw pi-cog',
    items: [
        { label: 'Preisschilder', icon: 'pi pi-fw pi-print', to: '/products/print-price-tags' },
        { label: 'Auszahlungen', icon: 'pi pi-fw pi-money-bill', to: '/payouts' },
        { label: 'Datenimport (CSV)', icon: 'pi pi-fw pi-upload', to: '/import-data' },
    ]
  },
  {
    label: 'Berichte',
    icon: 'pi pi-fw pi-chart-bar',
    items: [
      { label: 'Verkaufsübersicht (Tag/Woche/Monat)', icon: 'pi pi-fw pi-calendar', to: '/reports/sales-summary' },
      { label: 'Umsatzliste (Detail)', icon: 'pi pi-fw pi-list-ol', to: '/reports/revenue-list' },
      // Future reports can be added here
    ]
  }
  // Add more items or role-based visibility later
]);

// PrimeVue Menubar 'to' property handles router navigation internally.
// No need for custom click handlers for navigation items.
</script>

<style scoped>
.warenwelt-menubar {
  border-radius: 0; /* Optional: remove border-radius for a full-width look */
  /* background-color: var(--surface-card); */ /* Or your specific header color */
}

/* Custom styling for the router-link if Menubar doesn't style it as desired */
.p-menubar-item-link {
  text-decoration: none;
  color: var(--text-color); /* Or specific color */
  display: flex;
  align-items: center;
}
.p-menubar-item-link:hover {
  /* background-color: var(--surface-hover); */
}

/* Ensure logout button aligns well and has text color if using p-button-text */
/* PrimeVue's p-button-text usually handles this, but can be overridden. */
</style>
