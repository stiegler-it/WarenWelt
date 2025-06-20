<template>
  <div class="supplier-edit-view">
    <h1>{{ isNew ? 'Neuen Lieferant anlegen' : 'Lieferant bearbeiten' }}</h1>
    <form @submit.prevent="saveSupplier">
      <div class="form-group">
        <label for="supplier_number">Lieferantennummer:</label>
        <input type="text" id="supplier_number" v-model="supplier.supplier_number" required />
      </div>
      <div class="form-group">
        <label for="company_name">Firmenname:</label>
        <input type="text" id="company_name" v-model="supplier.company_name" />
      </div>
      <div class="form-group">
        <label for="first_name">Vorname:</label>
        <input type="text" id="first_name" v-model="supplier.first_name" />
      </div>
      <div class="form-group">
        <label for="last_name">Nachname:</label>
        <input type="text" id="last_name" v-model="supplier.last_name" />
      </div>
      <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" v-model="supplier.email" />
      </div>
      <div class="form-group">
        <label for="phone">Telefon:</label>
        <input type="tel" id="phone" v-model="supplier.phone" />
      </div>
      <div class="form-group">
        <label>
          <input type="checkbox" v-model="supplier.is_internal" />
          Interner Lieferant (für Eigenbestand)
        </label>
      </div>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <button type="submit" :disabled="isLoading">{{ isLoading ? 'Speichern...' : 'Speichern' }}</button>
      <router-link to="/suppliers" class="button secondary">Abbrechen</router-link>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import supplierService from '@/services/supplierService';

const props = defineProps({
  id: [String, Number], // From route params for editing
  isNew: {             // Injected from router for /new route
    type: Boolean,
    default: false
  }
});

const router = useRouter();
// const route = useRoute(); // Not strictly needed if props are correctly set up by router

const supplier = ref({
  supplier_number: '',
  company_name: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  is_internal: false,
});
const isLoading = ref(false);
const errorMessage = ref('');
// const isNew = ref(!props.id); // Determine if creating new or editing

onMounted(async () => {
  if (!props.isNew && props.id) {
    isLoading.value = true;
    try {
      const response = await supplierService.getSupplier(props.id);
      supplier.value = response.data;
    } catch (err) {
      errorMessage.value = 'Fehler beim Laden des Lieferanten: ' + (err.response?.data?.detail || err.message);
    } finally {
      isLoading.value = false;
    }
  }
});

// Watch for prop changes if the same component instance is reused for navigation (e.g. edit -> new)
// This might not be necessary with current router setup (keying or full re-mount)
// watch(() => props.id, async (newId) => {
//   isNew.value = !newId;
//   if (newId) { /* load data */ } else { /* reset form */ }
// });
// watch(() => props.isNew, (newIsNewVal) => {
//  if(newIsNewVal) { /* reset form */ }
// });


const saveSupplier = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    if (props.isNew) {
      await supplierService.createSupplier(supplier.value);
    } else {
      await supplierService.updateSupplier(props.id, supplier.value);
    }
    router.push('/suppliers');
  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Form styles are global or defined here */
.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}
</style>
