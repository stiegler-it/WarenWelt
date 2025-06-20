<template>
  <div class="category-edit-view">
    <h1>{{ isNew ? 'Neue Produktkategorie anlegen' : 'Produktkategorie bearbeiten' }}</h1>
    <form @submit.prevent="saveCategory" v-if="!pageLoading">
      <div class="form-group">
        <label for="name">Kategoriename:</label>
        <input type="text" id="name" v-model="category.name" required />
      </div>
      <div class="form-group">
        <label for="differential_tax_surcharge_percent">Aufschlag für Differenzbesteuerung (%):</label>
        <input
            type="number"
            step="0.01"
            min="0"
            max="100"
            id="differential_tax_surcharge_percent"
            v-model.number="category.differential_tax_surcharge_percent"
            placeholder="0.00"
        />
        <small>Geben Sie den Prozentsatz ein, z.B. 10 für 10%.</small>
      </div>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <div class="form-actions">
        <button type="submit" :disabled="formLoading">{{ formLoading ? 'Speichern...' : 'Speichern' }}</button>
        <router-link to="/product-categories" class="button secondary">Abbrechen</router-link>
      </div>
    </form>
    <div v-if="pageLoading" class="loading">Lade Kategorie Daten...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import productCategoryService from '@/services/productCategoryService';

const props = defineProps({
  id: [String, Number], // From route params for editing
});

const router = useRouter();
const route = useRoute();
const isNew = ref(!props.id);

const category = ref({
  name: '',
  differential_tax_surcharge_percent: 0.00,
});

const pageLoading = ref(false);
const formLoading = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  if (!isNew.value) {
    pageLoading.value = true;
    try {
      const response = await productCategoryService.getProductCategory(props.id);
      category.value = response.data;
      // Ensure the percentage is a number for the input field
      if (category.value.differential_tax_surcharge_percent === null || category.value.differential_tax_surcharge_percent === undefined) {
          category.value.differential_tax_surcharge_percent = 0.00;
      } else {
          category.value.differential_tax_surcharge_percent = parseFloat(category.value.differential_tax_surcharge_percent);
      }
    } catch (err) {
      errorMessage.value = 'Fehler beim Laden der Kategorie: ' + (err.response?.data?.detail || err.message);
    } finally {
      pageLoading.value = false;
    }
  }
});

const saveCategory = async () => {
  formLoading.value = true;
  errorMessage.value = '';

  const payload = {
    name: category.value.name,
    // Ensure the value is a string representation of a number if API expects that, or number if it expects number.
    // Pydantic with Decimal should handle string or number.
    differential_tax_surcharge_percent: category.value.differential_tax_surcharge_percent === null || category.value.differential_tax_surcharge_percent === ''
                                            ? 0.00
                                            : parseFloat(category.value.differential_tax_surcharge_percent)
  };

  try {
    if (isNew.value) {
      await productCategoryService.createProductCategory(payload);
    } else {
      await productCategoryService.updateProductCategory(props.id, payload);
    }
    router.push('/product-categories');
  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern der Kategorie: ' + (err.response?.data?.detail || err.message);
  } finally {
    formLoading.value = false;
  }
};
</script>

<style scoped>
/* Form styles */
.form-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 1rem;
}
</style>
