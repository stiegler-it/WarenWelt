<template>
  <div class="category-edit-view p-p-4">
    <Card>
      <template #title>
        {{ isNewPage ? 'Neue Produktkategorie anlegen' : 'Produktkategorie bearbeiten' }}
      </template>
      <template #content>
        <div v-if="pageLoading" class="text-center p-p-4">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <p>Lade Kategorie Daten...</p>
        </div>
        <form @submit.prevent="saveCategory" v-else>
          <div class="p-fluid grid">
            <div class="field col-12 md:col-6">
              <label for="name">Kategoriename*</label>
              <InputText id="name" v-model="category.name" required />
            </div>
            <div class="field col-12 md:col-6">
              <label for="differential_tax_surcharge_percent">Aufschlag für Differenzbesteuerung (%)</label>
              <InputNumber
                id="differential_tax_surcharge_percent"
                v-model="category.differential_tax_surcharge_percent"
                mode="decimal"
                :minFractionDigits="2"
                :maxFractionDigits="2"
                :min="0"
                :max="100"
                suffix=" %"
                placeholder="0,00 %"
              />
              <small class="p-d-block mt-1">Geben Sie den Prozentsatz ein, z.B. 10 für 10%.</small>
            </div>
          </div>

          <Message v-if="errorMessage" severity="error" :closable="true" @close="errorMessage=''" class="mt-3">{{ errorMessage }}</Message>

          <div class="form-actions mt-4">
            <Button type="submit" :label="isNewPage ? 'Anlegen' : 'Speichern'" :loading="formLoading" icon="pi pi-check" />
            <router-link to="/product-categories">
              <Button label="Abbrechen" class="p-button-text" icon="pi pi-times"/>
            </router-link>
          </div>
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import productCategoryService from '@/services/productCategoryService';
import { useToast } from 'primevue/usetoast';

// Globally registered: Card, InputText, InputNumber, Button, Message

const props = defineProps({
  id: [String, Number],
});

const router = useRouter();
const route = useRoute();
const toast = useToast();
const isNewPage = computed(() => !props.id);

const category = ref({
  name: '',
  differential_tax_surcharge_percent: null, // Use null for InputNumber to show placeholder correctly
});

const pageLoading = ref(false);
const formLoading = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  if (!isNewPage.value) {
    pageLoading.value = true;
    try {
      const response = await productCategoryService.getProductCategory(props.id);
      category.value = response.data;
      // Ensure the percentage is a number for InputNumber
      if (category.value.differential_tax_surcharge_percent !== null && category.value.differential_tax_surcharge_percent !== undefined) {
          category.value.differential_tax_surcharge_percent = parseFloat(category.value.differential_tax_surcharge_percent);
      } else {
          category.value.differential_tax_surcharge_percent = null; // Keep as null if not set
      }
    } catch (err) {
      errorMessage.value = 'Fehler beim Laden der Kategorie: ' + (err.response?.data?.detail || err.message);
      toast.add({severity:'error', summary: 'Ladefehler', detail: errorMessage.value, life: 5000});
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
    differential_tax_surcharge_percent: category.value.differential_tax_surcharge_percent === null
                                            ? 0.00 // Default to 0.00 if null (placeholder was shown)
                                            : parseFloat(category.value.differential_tax_surcharge_percent)
  };

  try {
    if (isNewPage.value) {
      await productCategoryService.createProductCategory(payload);
      toast.add({severity:'success', summary: 'Erstellt', detail: 'Produktkategorie erfolgreich angelegt.', life: 3000});
    } else {
      await productCategoryService.updateProductCategory(props.id, payload);
      toast.add({severity:'success', summary: 'Aktualisiert', detail: 'Produktkategorie erfolgreich aktualisiert.', life: 3000});
    }
    router.push('/product-categories');
  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern der Kategorie: ' + (err.response?.data?.detail || err.message);
    toast.add({severity:'error', summary: 'Speicherfehler', detail: errorMessage.value, life: 5000});
  } finally {
    formLoading.value = false;
  }
};
</script>

<style scoped>
/* Using PrimeFlex for padding (p-p-4), fluid layout (p-fluid), grid, and spacing (mt-3, mt-4) */
.form-actions {
  display: flex;
  gap: 0.5rem;
}
.mt-1 { margin-top: 0.25rem; }
.field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}
</style>
