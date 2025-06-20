<template>
  <div class="supplier-list-view">
    <h1>Lieferantenübersicht</h1>
    <router-link to="/suppliers/new" class="button">Neuen Lieferant anlegen</router-link>
    <div v-if="isLoading" class="loading">Lade Lieferanten...</div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <table v-if="suppliers.length > 0">
      <thead>
        <tr>
          <th>Nr.</th>
          <th>Name</th>
          <th>Email</th>
          <th>Telefon</th>
          <th>Intern</th>
          <th>Aktionen</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="supplier in suppliers" :key="supplier.id">
          <td>{{ supplier.supplier_number }}</td>
          <td>{{ supplier.company_name || supplier.first_name + ' ' + supplier.last_name }}</td>
          <td>{{ supplier.email }}</td>
          <td>{{ supplier.phone }}</td>
          <td>{{ supplier.is_internal ? 'Ja' : 'Nein' }}</td>
          <td>
            <router-link :to="{ name: 'SupplierEdit', params: { id: supplier.id } }" class="button secondary small">Bearbeiten</router-link>
            <!-- Delete button would require confirmation logic -->
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!isLoading && suppliers.length === 0">Keine Lieferanten gefunden.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import supplierService from '@/services/supplierService';

const suppliers = ref([]);
const isLoading = ref(true);
const error = ref('');

onMounted(async () => {
  try {
    const response = await supplierService.getSuppliers();
    suppliers.value = response.data;
  } catch (err) {
    error.value = 'Fehler beim Laden der Lieferanten: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* Styles for loading, error, table, buttons are assumed to be somewhat global or defined here */
.button.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}
</style>
