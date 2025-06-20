<template>
  <form @submit.prevent="submitForm" class="p-fluid">
    <div class="field">
      <label for="name">Regalname</label>
      <InputText id="name" v-model.trim="editableShelf.name" required autofocus :class="{'p-invalid': v$.editableShelf.name.$invalid && submitted}" />
      <small v-if="v$.editableShelf.name.$invalid && submitted" class="p-error">{{ v$.editableShelf.name.$errors[0]?.$message }}</small>
    </div>

    <div class="field">
      <label for="location_description">Standortbeschreibung</label>
      <InputText id="location_description" v-model.trim="editableShelf.location_description" />
    </div>

    <div class="field">
      <label for="size_description">Größenbeschreibung</label>
      <InputText id="size_description" v-model.trim="editableShelf.size_description" />
    </div>

    <div class="formgrid grid">
        <div class="field col-12 md:col-6">
            <label for="monthly_rent_price">Mietpreis/Monat (€)</label>
            <InputNumber id="monthly_rent_price" v-model="editableShelf.monthly_rent_price" mode="currency" currency="EUR" locale="de-DE" required :class="{'p-invalid': v$.editableShelf.monthly_rent_price.$invalid && submitted}" :min="0" :minFractionDigits="2" :maxFractionDigits="2" />
            <small v-if="v$.editableShelf.monthly_rent_price.$invalid && submitted" class="p-error">{{ v$.editableShelf.monthly_rent_price.$errors[0]?.$message }}</small>
        </div>

        <div class="field col-12 md:col-6">
            <label for="status">Status</label>
            <Dropdown id="status" v-model="editableShelf.status" :options="shelfStatusOptions" optionLabel="label" optionValue="value" placeholder="Status auswählen" required :class="{'p-invalid': v$.editableShelf.status.$invalid && submitted}" />
            <small v-if="v$.editableShelf.status.$invalid && submitted" class="p-error">{{ v$.editableShelf.status.$errors[0]?.$message }}</small>
        </div>
    </div>

    <div class="field">
      <div class="flex align-items-center">
        <Checkbox id="is_active" v-model="editableShelf.is_active" :binary="true" class="mr-2"/>
        <label for="is_active">Aktiv</label>
      </div>
    </div>

    <div class="form-dialog-footer">
      <Button label="Abbrechen" icon="pi pi-times" class="p-button-text" @click="closeDialog" />
      <Button type="submit" label="Speichern" icon="pi pi-check" :loading="isSaving" />
    </div>
  </form>
</template>

<script setup>
import { ref, watch, onMounted, reactive } from 'vue';
import { useVuelidate } from '@vuelidate/core';
import { required, minValue, decimal, helpers } from '@vuelidate/validators'; // Ensure decimal is correctly used or replaced if not from vuelidate/validators

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import Checkbox from 'primevue/checkbox';

// Props definition
const props = defineProps({
  shelfDataProp: { // Renamed to avoid conflict with 'shelfData' ref
    type: Object,
    default: () => ({}) // Default to an empty object
  },
  isSaving: { // To show loading state on save button
      type: Boolean,
      default: false
  }
});

// Emits definition
const emit = defineEmits(['shelf-save-event', 'close-dialog-event']); // Renamed events

// Reactive state for the form
const editableShelf = reactive({
  id: null,
  name: '',
  location_description: '',
  size_description: '',
  monthly_rent_price: null,
  status: 'AVAILABLE', // Default status
  is_active: true,     // Default active state
});

const submitted = ref(false);

const shelfStatusOptions = ref([
    {label: 'Verfügbar', value: 'AVAILABLE'},
    {label: 'Vermietet', value: 'RENTED'},
    {label: 'Wartung', value: 'MAINTENANCE'}
]);

// Vuelidate Rules
const rules = {
  editableShelf: {
    name: {
        required: helpers.withMessage('Regalname ist ein Pflichtfeld.', required)
    },
    monthly_rent_price: {
        required: helpers.withMessage('Mietpreis ist ein Pflichtfeld.', required),
        // Using a custom validator for number because InputNumber v-model can be null
        validPrice: helpers.withMessage('Mietpreis muss eine gültige, positive Zahl sein.', (value) => value === null || (typeof value === 'number' && value >= 0.01))
    },
    status: {
        required: helpers.withMessage('Status ist ein Pflichtfeld.', required)
    }
  }
};

const v$ = useVuelidate(rules, { editableShelf });

// Watch for prop changes to update the local reactive editableShelf
watch(() => props.shelfDataProp, (newVal) => {
  // Update only if newVal is not empty, to prevent overwriting defaults when prop is initially empty
  if (newVal && Object.keys(newVal).length > 0) {
    editableShelf.id = newVal.id || null;
    editableShelf.name = newVal.name || '';
    editableShelf.location_description = newVal.location_description || '';
    editableShelf.size_description = newVal.size_description || '';
    editableShelf.monthly_rent_price = newVal.monthly_rent_price === undefined ? null : newVal.monthly_rent_price;
    editableShelf.status = newVal.status || 'AVAILABLE';
    editableShelf.is_active = newVal.is_active === undefined ? true : newVal.is_active;
  } else {
    // Reset to defaults if prop is empty (e.g. for new shelf)
    editableShelf.id = null;
    editableShelf.name = '';
    editableShelf.location_description = '';
    editableShelf.size_description = '';
    editableShelf.monthly_rent_price = null;
    editableShelf.status = 'AVAILABLE';
    editableShelf.is_active = true;
  }
  submitted.value = false;
  v$.value.$reset();
}, { deep: true, immediate: true });


const submitForm = async () => {
  submitted.value = true;
  const isValid = await v$.value.$validate();
  if (!isValid) {
    return;
  }
  emit('shelf-save-event', { ...editableShelf }); // Emit a copy
};

const closeDialog = () => {
  emit('close-dialog-event');
};

</script>

<style scoped>
/* PrimeVue uses utility classes like p-fluid, formgrid, field, col-12 etc.
   These are generally available if PrimeVue is set up globally.
   Additional custom styling can be added here. */
.form-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 1.5rem; /* Increased padding a bit */
  margin-top: 1rem; /* Added margin for separation */
  border-top: 1px solid var(--surface-border); /* PrimeVue variable for border */
}
.field {
    margin-bottom: 1rem; /* Consistent spacing for fields */
}
</style>
