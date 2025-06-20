<template>
  <div class="category-list-view">
    <h1>Produktkategorien</h1>
    <router-link to="/product-categories/new" class="button">Neue Kategorie anlegen</router-link>

    <div v-if="isLoading" class="loading">Lade Kategorien...</div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <table v-if="categories.length > 0">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Diff.-Bst. Aufschlag (%)</th>
          <th>Aktionen</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="category in categories" :key="category.id">
          <td>{{ category.id }}</td>
          <td>{{ category.name }}</td>
          <td>{{ formatPercentage(category.differential_tax_surcharge_percent) }}</td>
          <td>
            <router-link :to="{ name: 'ProductCategoryEdit', params: { id: category.id } }" class="button secondary small">Bearbeiten</router-link>
            <button @click="confirmDeleteCategory(category)" class="button danger small" :disabled="deleting[category.id]">
              {{ deleting[category.id] ? 'Löschen...' : 'Löschen' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!isLoading && categories.length === 0">Keine Kategorien gefunden.</p>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import productCategoryService from '@/services/productCategoryService';
import { useRouter } from 'vue-router';

const categories = ref([]);
const isLoading = ref(true);
const error = ref('');
const router = useRouter();
const deleting = reactive({}); // To track delete status per category

const formatPercentage = (value) => {
  if (value === null || value === undefined) return '-';
  return `${parseFloat(value).toFixed(2)}%`;
};

const fetchCategories = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    const response = await productCategoryService.getProductCategories();
    categories.value = response.data;
  } catch (err) {
    error.value = 'Fehler beim Laden der Kategorien: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchCategories);

const confirmDeleteCategory = async (category) => {
  if (window.confirm(`Sind Sie sicher, dass Sie die Kategorie "${category.name}" löschen möchten? Dies kann nicht rückgängig gemacht werden und könnte Produkte betreffen.`)) {
    deleting[category.id] = true;
    error.value = '';
    try {
      await productCategoryService.deleteProductCategory(category.id);
      // Refresh list
      fetchCategories();
    } catch (err) {
      error.value = `Fehler beim Löschen der Kategorie "${category.name}": ` + (err.response?.data?.detail || err.message);
    } finally {
      deleting[category.id] = false;
    }
  }
};
</script>

<style scoped>
.button.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  margin-left: 5px;
}
/* Additional styles if needed */
</style>
