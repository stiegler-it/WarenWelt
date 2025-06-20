<template>
  <div class="product-list-view">
    <h1>Artikelübersicht</h1>
    <router-link to="/products/new" class="button">Neuen Artikel anlegen</router-link>
    <!-- Filter options can be added here -->
    <div v-if="isLoading" class="loading">Lade Artikel...</div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <table v-if="products.length > 0">
      <thead>
        <tr>
          <th>SKU</th>
          <th>Name</th>
          <th>Lieferant</th>
          <th>Kategorie</th>
          <th>VK-Preis</th>
          <th>Status</th>
          <th>Aktionen</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="product in products" :key="product.id">
          <td>{{ product.sku }}</td>
          <td>{{ product.name }}</td>
          <td>{{ product.supplier?.supplier_number }} - {{ product.supplier?.company_name || product.supplier?.first_name }}</td>
          <td>{{ product.category?.name }}</td>
          <td>{{ formatCurrency(product.selling_price) }}</td>
          <td>{{ product.status }}</td>
          <td>
            <router-link :to="{ name: 'ProductEdit', params: { id: product.id } }" class="button secondary small">Bearbeiten</router-link>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!isLoading && products.length === 0">Keine Artikel gefunden.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import productService from '@/services/productService';

const products = ref([]);
const isLoading = ref(true);
const error = ref('');

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

onMounted(async () => {
  try {
    const response = await productService.getProducts(); // Add params for filtering/pagination later
    products.value = response.data;
  } catch (err) {
    error.value = 'Fehler beim Laden der Artikel: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* Styles */
</style>
