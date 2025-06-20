<template>
  <div class="supplier-edit-view p-p-4">
    <Card>
      <template #title>
        {{ isNewPage ? 'Neuen Lieferant anlegen' : 'Lieferant bearbeiten' }}
      </template>
      <template #content>
        <div v-if="pageLoading" class="text-center p-p-4">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <p>Lade Lieferantendaten...</p>
        </div>
        <form @submit.prevent="saveSupplier" v-else>
          <div class="p-fluid grid">
            <div class="field col-12 md:col-6">
              <label for="supplier_number">Lieferantennummer*</label>
              <InputText id="supplier_number" v-model="supplier.supplier_number" required />
            </div>
            <div class="field col-12 md:col-6">
              <label for="company_name">Firmenname</label>
              <InputText id="company_name" v-model="supplier.company_name" />
            </div>
            <div class="field col-12 md:col-6">
              <label for="first_name">Vorname</label>
              <InputText id="first_name" v-model="supplier.first_name" />
            </div>
            <div class="field col-12 md:col-6">
              <label for="last_name">Nachname</label>
              <InputText id="last_name" v-model="supplier.last_name" />
            </div>
            <div class="field col-12 md:col-6">
              <label for="email">Email</label>
              <InputText id="email" type="email" v-model="supplier.email" />
            </div>
            <div class="field col-12 md:col-6">
              <label for="phone">Telefon</label>
              <InputText id="phone" v-model="supplier.phone" />
            </div>
            <div class="field-checkbox col-12">
              <Checkbox id="is_internal" v-model="supplier.is_internal" :binary="true" />
              <label for="is_internal" class="ml-2">Interner Lieferant (für Eigenbestand)</label>
            </div>
          </div>

          <small v-if="errorMessage" class="p-error block mt-2">{{ errorMessage }}</small>

          <div class="form-actions mt-4">
            <Button type="submit" :label="isNewPage ? 'Anlegen' : 'Speichern'" :loading="formLoading" icon="pi pi-check" />
            <router-link to="/suppliers">
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
import supplierService from '@/services/supplierService';
import { useToast } from 'primevue/usetoast';

// PrimeVue components (Card, InputText, Checkbox, Button) are globally registered

const props = defineProps({
  id: [String, Number], // From route params for editing
});

const router = useRouter();
const route = useRoute();
const toast = useToast();

// Determine if it's a new supplier page based on the route name or presence of id
const isNewPage = computed(() => route.name === 'SupplierNew');

const supplier = ref({
  supplier_number: '',
  company_name: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  is_internal: false,
});

const pageLoading = ref(false); // For loading existing supplier data
const formLoading = ref(false); // For submit action
const errorMessage = ref('');

onMounted(async () => {
  if (!isNewPage.value && props.id) {
    pageLoading.value = true;
    try {
      const response = await supplierService.getSupplier(props.id);
      supplier.value = response.data;
    } catch (err) {
      errorMessage.value = 'Fehler beim Laden des Lieferanten: ' + (err.response?.data?.detail || err.message);
      toast.add({severity:'error', summary: 'Ladefehler', detail: errorMessage.value, life: 5000});
    } finally {
      pageLoading.value = false;
    }
  } else {
    // Optionally generate a new supplier_number suggestion for new suppliers
    // supplier.value.supplier_number = `S-${Date.now().toString().slice(-6)}`;
  }
});

const saveSupplier = async () => {
  formLoading.value = true;
  errorMessage.value = '';
  try {
    let response;
    if (isNewPage.value) {
      response = await supplierService.createSupplier(supplier.value);
      toast.add({severity:'success', summary: 'Erfolgreich', detail: 'Lieferant angelegt.', life: 3000});
    } else {
      response = await supplierService.updateSupplier(props.id, supplier.value);
      toast.add({severity:'success', summary: 'Erfolgreich', detail: 'Lieferant aktualisiert.', life: 3000});
    }
    router.push('/suppliers');
  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern: ' + (err.response?.data?.detail || err.message);
    toast.add({severity:'error', summary: 'Speicherfehler', detail: errorMessage.value, life: 5000});
  } finally {
    formLoading.value = false;
  }
};
</script>

<style scoped>
/* Using PrimeFlex for padding (p-p-4), fluid layout (p-fluid), grid, and spacing (mt-2, mt-4, ml-2) */
.form-actions {
  display: flex;
  gap: 0.5rem; /* PrimeFlex 'gap' class can also be used if available in version */
}
.field-checkbox label {
    vertical-align: middle;
}
</style>
