<template>
  <div class="dashboard-view p-p-4">
    <Card>
      <template #title>
        <div class="text-center text-2xl">Willkommen bei WarenWelt!</div>
      </template>
      <template #content>
        <p v-if="authStore.user" class="text-center">
          Angemeldet als: <strong>{{ authStore.user.full_name || authStore.user.email }}</strong>
          <span v-if="authStore.user.role"> (Rolle: {{ authStore.user.role.name }})</span>
        </p>
        <p class="text-center">Dies ist dein Dashboard. Wähle eine Aktion aus der Navigation oder den Schnellzugriffen.</p>
      </template>
    </Card>

    <div class="quick-actions grid mt-4">
      <div class="col-12 md:col-6 lg:col-3">
        <router-link to="/pos" class="no-underline">
          <Card class="quick-action-card hover:surface-hover transition-colors transition-duration-150">
            <template #title><i class="pi pi-shopping-cart mr-2"></i>Kasse</template>
            <template #content>Schnell zum Verkaufsprozess.</template>
          </Card>
        </router-link>
      </div>
      <div class="col-12 md:col-6 lg:col-3">
        <router-link to="/products/new" class="no-underline">
          <Card class="quick-action-card hover:surface-hover transition-colors transition-duration-150">
            <template #title><i class="pi pi-plus-circle mr-2"></i>Neuer Artikel</template>
            <template #content>Einen neuen Artikel erfassen.</template>
          </Card>
        </router-link>
      </div>
       <div class="col-12 md:col-6 lg:col-3">
        <router-link to="/reports/daily-summary" class="no-underline">
          <Card class="quick-action-card hover:surface-hover transition-colors transition-duration-150">
            <template #title><i class="pi pi-chart-line mr-2"></i>Tagesabschluss</template>
            <template #content>Aktuellen Tagesabschluss einsehen.</template>
          </Card>
        </router-link>
      </div>
      <!-- Add more quick action cards as needed -->
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/store/auth';
// Globally registered: Card
// No need to import Button for router-link styling if Card itself is clickable or styled appropriately.

const authStore = useAuthStore();
</script>

<style scoped>
.dashboard-view {
  /* padding: 1rem; Using PrimeFlex p-p-4 */
}
.text-center {
  text-align: center;
}
.text-2xl { /* PrimeFlex class for font size */
    font-size: 1.5rem; /* Example, adjust based on theme */
}
.mt-4 { /* PrimeFlex class */
    margin-top: 1.5rem;
}
.mr-2 { /* PrimeFlex class */
    margin-right: 0.5rem;
}
.quick-action-card {
  cursor: pointer;
  /* min-height: 120px; */ /* Ensure cards have some height */
}
.quick-action-card .p-card-title {
  font-size: 1.2rem; /* Adjust title size in cards */
  display: flex;
  align-items: center;
}
.quick-action-card .p-card-content {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}
.no-underline {
  text-decoration: none;
}

/* PrimeFlex grid classes like 'grid', 'col-12', 'md:col-6', 'lg:col-3' handle responsiveness */
/* PrimeFlex transition classes 'hover:surface-hover', 'transition-colors', 'transition-duration-150' for hover effects */
</style>
