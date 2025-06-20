<template>
  <form @submit.prevent="submitForm" class="p-fluid">
    <div class="formgrid grid">
      <div class="field col-12 md:col-6">
        <label for="contract_number">Vertragsnummer</label>
        <InputText id="contract_number" v-model.trim="editableContract.contract_number" :class="{'p-invalid': v$.editableContract.contract_number?.$invalid && submitted}" />
        <small class="p-text-sm p-text-secondary">Optional, wird automatisch generiert, falls leer.</small>
        <small v-if="v$.editableContract.contract_number?.$invalid && submitted" class="p-error">{{ v$.editableContract.contract_number?.$errors[0]?.$message }}</small>
      </div>

      <div class="field col-12 md:col-6">
        <label for="status">Status</label>
        <Dropdown id="status" v-model="editableContract.status" :options="contractStatusOptions" optionLabel="label" optionValue="value" placeholder="Status auswählen" required :class="{'p-invalid': v$.editableContract.status.$invalid && submitted}" />
        <small v-if="v$.editableContract.status.$invalid && submitted" class="p-error">{{ v$.editableContract.status.$errors[0]?.$message }}</small>
      </div>

      <div class="field col-12">
        <label for="shelf_id">Regal</label>
        <Dropdown id="shelf_id" v-model="editableContract.shelf_id" :options="availableShelves" optionLabel="displayName" optionValue="id" placeholder="Regal auswählen" filter required :class="{'p-invalid': v$.editableContract.shelf_id.$invalid && submitted}" @change="onShelfSelected">
          <template #value="slotProps">
            <div v-if="slotProps.value">
              {{ availableShelves.find(s => s.id === slotProps.value)?.displayName }}
            </div>
            <span v-else>
              {{ slotProps.placeholder }}
            </span>
          </template>
          <template #option="slotProps">
            <div>{{slotProps.option.name}} ({{formatCurrency(slotProps.option.monthly_rent_price)}}) <Tag :value="slotProps.option.status" :severity="getSeverityForShelfStatus(slotProps.option.status)"></Tag></div>
          </template>
        </Dropdown>
        <small v-if="v$.editableContract.shelf_id.$invalid && submitted" class="p-error">{{ v$.editableContract.shelf_id.$errors[0]?.$message }}</small>
      </div>

      <div class="field col-12">
        <label for="tenant_supplier_id">Mieter (Lieferant)</label>
        <Dropdown id="tenant_supplier_id" v-model="editableContract.tenant_supplier_id" :options="availableTenants" optionLabel="displayName" optionValue="id" placeholder="Mieter auswählen" filter required :class="{'p-invalid': v$.editableContract.tenant_supplier_id.$invalid && submitted}">
            <template #value="slotProps">
                <div v-if="slotProps.value">
                    {{ availableTenants.find(t => t.id === slotProps.value)?.displayName }}
                </div>
                <span v-else>
                    {{ slotProps.placeholder }}
                </span>
            </template>
            <template #option="slotProps">
                <div>{{slotProps.option.displayName}} (Nr: {{slotProps.option.supplier_number}})</div>
            </template>
        </Dropdown>
        <small v-if="v$.editableContract.tenant_supplier_id.$invalid && submitted" class="p-error">{{ v$.editableContract.tenant_supplier_id.$errors[0]?.$message }}</small>
      </div>

      <div class="field col-12 md:col-6">
        <label for="start_date">Startdatum</label>
        <Calendar id="start_date" v-model="editableContract.start_date" dateFormat="yy-mm-dd" showIcon required :class="{'p-invalid': v$.editableContract.start_date.$invalid && submitted}" />
        <small v-if="v$.editableContract.start_date.$invalid && submitted" class="p-error">{{ v$.editableContract.start_date.$errors[0]?.$message }}</small>
      </div>

      <div class="field col-12 md:col-6">
        <label for="end_date">Enddatum</label>
        <Calendar id="end_date" v-model="editableContract.end_date" dateFormat="yy-mm-dd" showIcon required :class="{'p-invalid': v$.editableContract.end_date.$invalid && submitted}" :minDate="minEndDate" />
        <small v-if="v$.editableContract.end_date.$invalid && submitted" class="p-error">{{ v$.editableContract.end_date.$errors[0]?.$message }}</small>
      </div>

      <div class="field col-12 md:col-6">
        <label for="rent_price_at_signing">Mietpreis bei Abschluss (€)</label>
        <InputNumber id="rent_price_at_signing" v-model="editableContract.rent_price_at_signing" mode="currency" currency="EUR" locale="de-DE" required :class="{'p-invalid': v$.editableContract.rent_price_at_signing.$invalid && submitted}" :min="0" :minFractionDigits="2" :maxFractionDigits="2"/>
        <small v-if="v$.editableContract.rent_price_at_signing.$invalid && submitted" class="p-error">{{ v$.editableContract.rent_price_at_signing.$errors[0]?.$message }}</small>
      </div>

       <div class="field col-12 md:col-6">
        <label for="payment_terms">Zahlungsbedingungen</label>
        <InputText id="payment_terms" v-model.trim="editableContract.payment_terms" />
      </div>

    </div>

    <div class="form-dialog-footer">
      <Button label="Abbrechen" icon="pi pi-times" class="p-button-text" @click="closeDialog" />
      <Button type="submit" label="Speichern" icon="pi pi-check" :loading="isSaving" />
    </div>
  </form>
</template>

<script setup>
import { ref, watch, onMounted, reactive, computed } from 'vue';
import { useVuelidate } from '@vuelidate/core';
import { required, minValue, helpers } from '@vuelidate/validators';

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import Calendar from 'primevue/calendar';
import Tag from 'primevue/tag';

import shelfService from '@/services/shelfService';
import supplierService from '@/services/supplierService';

const props = defineProps({
  contractDataProp: { type: Object, default: () => ({}) },
  isSaving: { type: Boolean, default: false }
});

const emit = defineEmits(['contract-save-event', 'close-dialog-event']);

const editableContract = reactive({
  id: null, contract_number: '', shelf_id: null, tenant_supplier_id: null,
  start_date: null, end_date: null, rent_price_at_signing: null,
  payment_terms: '', status: 'PENDING'
});

const submitted = ref(false);
const availableShelves = ref([]);
const availableTenants = ref([]);

const contractStatusOptions = ref([
    {label: 'Aktiv', value: 'ACTIVE'}, {label: 'Ausgelaufen', value: 'EXPIRED'},
    {label: 'Gekündigt', value: 'TERMINATED'}, {label: 'Anstehend', value: 'PENDING'}
]);

const rules = {
  editableContract: {
    shelf_id: { required: helpers.withMessage('Regal ist ein Pflichtfeld.', required) },
    tenant_supplier_id: { required: helpers.withMessage('Mieter ist ein Pflichtfeld.', required) },
    start_date: { required: helpers.withMessage('Startdatum ist ein Pflichtfeld.', required) },
    end_date: {
        required: helpers.withMessage('Enddatum ist ein Pflichtfeld.', required),
        validEndDate: helpers.withMessage('Enddatum muss nach dem Startdatum liegen.', (value) => {
            if (!value || !editableContract.start_date) return true;
            return new Date(value) > new Date(editableContract.start_date);
        })
    },
    rent_price_at_signing: {
        required: helpers.withMessage('Mietpreis ist ein Pflichtfeld.', required),
        validPrice: helpers.withMessage('Mietpreis muss eine Zahl >= 0 sein.', value => value === null || (typeof value === 'number' && value >= 0))
    },
    status: { required: helpers.withMessage('Status ist ein Pflichtfeld.', required) },
    contract_number: {}
  }
};
const v$ = useVuelidate(rules, { editableContract });

const minEndDate = computed(() => {
  if (editableContract.start_date) {
    const startDate = new Date(editableContract.start_date);
    return startDate; // End date can be same day, but validEndDate rule will check if it's > start_date
  }
  return null;
});

const fetchDropdownData = async () => {
  try {
    const shelvesPromise = shelfService.getAllShelves({ is_active: true, limit: 2000 });
    const tenantsPromise = supplierService.getAllSuppliers({ limit: 2000 });

    const [shelvesResponse, tenantsResponse] = await Promise.all([shelvesPromise, tenantsPromise]);

    availableShelves.value = shelvesResponse.data.map(s => ({
        ...s,
        displayName: `${s.name} (${formatCurrency(s.monthly_rent_price)}) - ${s.status}`
    }));

    availableTenants.value = tenantsResponse.data.map(t => ({
        ...t,
        displayName: t.company_name || `${t.first_name || ''} ${t.last_name || ''}`.trim() || t.supplier_number
    }));
  } catch (error) {
    console.error("Error fetching dropdown data for contracts form:", error);
    // TODO: Show toast message to user
  }
};

const initializeForm = (data) => {
    if (data && data.id) { // Editing existing contract
        Object.assign(editableContract, data);
        if (data.start_date && typeof data.start_date === 'string') {
            editableContract.start_date = new Date(data.start_date);
        }
        if (data.end_date && typeof data.end_date === 'string') {
            editableContract.end_date = new Date(data.end_date);
        }
    } else { // New contract defaults
        editableContract.id = null;
        editableContract.contract_number = data?.contract_number || ''; // Allow pre-fill if any
        editableContract.shelf_id = data?.shelf_id || null;
        editableContract.tenant_supplier_id = data?.tenant_supplier_id || null;
        editableContract.start_date = data?.start_date ? new Date(data.start_date) : new Date();
        editableContract.end_date = data?.end_date ? new Date(data.end_date) : null;
        editableContract.rent_price_at_signing = data?.rent_price_at_signing === undefined ? null : data.rent_price_at_signing;
        editableContract.payment_terms = data?.payment_terms || '';
        editableContract.status = data?.status || 'PENDING';
    }
    submitted.value = false;
    v$.value.$reset();
};


onMounted(() => {
  fetchDropdownData();
  initializeForm(props.contractDataProp); // Initialize with current prop data
});

watch(() => props.contractDataProp, (newVal) => {
  initializeForm(newVal);
}, { deep: true });


const onShelfSelected = (event) => {
    const selectedShelf = availableShelves.value.find(s => s.id === event.value);
    if (selectedShelf && editableContract.rent_price_at_signing === null && !editableContract.id) { // Only for new contracts and if price not already set
        editableContract.rent_price_at_signing = parseFloat(selectedShelf.monthly_rent_price);
    }
};

const submitForm = async () => {
  submitted.value = true;
  const isValid = await v$.value.$validate();
  if (!isValid) return;

  const payload = { ...editableContract };
  if (payload.start_date instanceof Date) {
    payload.start_date = payload.start_date.toISOString().split('T')[0];
  }
  if (payload.end_date instanceof Date) {
    payload.end_date = payload.end_date.toISOString().split('T')[0];
  }
  emit('contract-save-event', payload);
};

const closeDialog = () => {
  emit('close-dialog-event');
};

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(value));
};
const getSeverityForShelfStatus = (status) => {
  switch (status) {
    case 'AVAILABLE': return 'success';
    case 'RENTED': return 'info';
    case 'MAINTENANCE': return 'warning';
    default: return 'secondary';
  }
};

</script>

<style scoped>
.form-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 1.5rem;
  margin-top: 1rem;
  border-top: 1px solid var(--surface-border);
}
.field {
    margin-bottom: 1.25rem; /* Increased spacing a bit */
}
</style>
