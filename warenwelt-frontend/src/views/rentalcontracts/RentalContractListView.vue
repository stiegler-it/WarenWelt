<template>
  <div class="rental-contract-list-view card">
    <Toast />
    <ConfirmDialog></ConfirmDialog>

    <Toolbar class="mb-4">
      <template #start>
        <Button label="Neuer Mietvertrag" icon="pi pi-plus" class="p-button-success mr-2" @click="openNewContractDialog" />
      </template>
    </Toolbar>

    <DataTable :value="contracts" :loading="isLoading" responsiveLayout="scroll" dataKey="id"
      paginator :rows="10" :rowsPerPageOptions="[5,10,25,50]"
      v-model:filters="filters" filterDisplay="menu"
      :globalFilterFields="['contract_number', 'shelf.name', 'tenant.display_name', 'status', 'tenant.supplier_number']">
      <template #header>
        <div class="flex justify-content-between align-items-center">
          <h5 class="m-0">Mietvertragsübersicht</h5>
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="filters['global'].value" placeholder="Global suchen..." />
          </span>
        </div>
      </template>
      <template #empty>Keine Mietverträge gefunden.</template>
      <template #loading>Lade Mietvertragsdaten...</template>

      <Column field="contract_number" header="Vertragsnr." sortable style="min-width: 10rem">
        <template #body="{data}">{{ data.contract_number }}</template>
      </Column>
      <Column field="shelf.name" header="Regal" sortable filterField="shelf.name" :showFilterMatchModes="false" style="min-width: 12rem">
         <template #filter="{filterModel, filterCallback}">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Regal suchen"/>
        </template>
        <template #body="{data}">{{ data.shelf?.name }}</template>
      </Column>
      <Column field="tenant.display_name" header="Mieter" sortable filterField="tenant.display_name" :showFilterMatchModes="false" style="min-width: 14rem">
        <template #filter="{filterModel, filterCallback}">
            <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Mieter suchen"/>
        </template>
         <template #body="{data}">
            {{ data.tenant?.display_name || `${data.tenant?.first_name || ''} ${data.tenant?.last_name || ''}`.trim() || data.tenant?.supplier_number }}
        </template>
      </Column>
      <Column field="start_date" header="Startdatum" sortable dataType="date" style="min-width: 10rem">
        <template #body="{data}">{{ formatDate(data.start_date) }}</template>
      </Column>
      <Column field="end_date" header="Enddatum" sortable dataType="date" style="min-width: 10rem">
        <template #body="{data}">{{ formatDate(data.end_date) }}</template>
      </Column>
      <Column field="rent_price_at_signing" header="Mietpreis" sortable dataType="numeric" style="min-width: 9rem">
        <template #body="{data}">{{ formatCurrency(data.rent_price_at_signing) }}</template>
      </Column>
      <Column field="status" header="Status" sortable filterField="status" :showFilterMatchModes="false" style="min-width:10rem">
        <template #filter="{filterModel, filterCallback}">
             <Dropdown v-model="filterModel.value" :options="contractStatusOptions" optionLabel="label" optionValue="value" placeholder="Alle Status" class="p-column-filter" @change="filterCallback()" showClear/>
        </template>
        <template #body="{data}">
          <Tag :value="getContractStatusLabel(data.status)" :severity="getSeverityForContractStatus(data.status)" />
        </template>
      </Column>
      <Column headerStyle="min-width:10rem; text-align:center;" bodyStyle="text-align:center; overflow:visible;">
        <template #header>Aktionen</template>
        <template #body="slotProps">
          <Button icon="pi pi-pencil" class="p-button-rounded p-button-success mr-2" @click="editContract(slotProps.data)" v-tooltip.top="'Bearbeiten'" />
          <Button icon="pi pi-trash" class="p-button-rounded p-button-warning" @click="confirmDeleteContract(slotProps.data)" v-tooltip.top="'Löschen'" />
          <!-- TODO: Button für Vertragsdetails/Druckansicht -->
           <!-- <Button icon="pi pi-print" class="p-button-rounded p-button-info ml-2" @click="printContract(slotProps.data)" v-tooltip.top="'Drucken'" disabled /> -->
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="contractDialogVisible" :style="{width: '600px'}" header="Mietvertragsdetails" :modal="true" class="p-fluid" @hide="hideContractDialog">
        <RentalContractEditForm
            v-if="contractDialogVisible"
            :contract-data-prop="currentContract"
            :is-saving="isSubmittingContract"
            @contract-save-event="onContractSubmit"
            @close-dialog-event="hideContractDialog" />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Toolbar from 'primevue/toolbar';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Dropdown from 'primevue/dropdown';
import { FilterMatchMode } from 'primevue/api';
import Tooltip from 'primevue/tooltip'; // For v-tooltip

import rentalContractService from '@/services/rentalContractService';
// Annahme: Pfad zur Edit-Form Komponente
import RentalContractEditForm from '@/components/rentalcontracts/RentalContractEditForm.vue';

const toast = useToast();
const confirm = useConfirm();

const contracts = ref([]);
const isLoading = ref(true);
const contractDialogVisible = ref(false);
const currentContract = ref({});
const isSubmittingContract = ref(false);

const filters = ref({
    'global': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'status': { value: null, matchMode: FilterMatchMode.EQUALS },
    'shelf.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'tenant.display_name': { value: null, matchMode: FilterMatchMode.CONTAINS },
});

const contractStatusOptions = ref([
    {label: 'Aktiv', value: 'ACTIVE'},
    {label: 'Ausgelaufen', value: 'EXPIRED'},
    {label: 'Gekündigt', value: 'TERMINATED'},
    {label: 'Anstehend', value: 'PENDING'}
]);

const fetchContracts = async () => {
  isLoading.value = true;
  try {
    // Load all contracts, frontend paginator handles display. For very large datasets, server-side paging is better.
    const response = await rentalContractService.getAllRentalContracts({ limit: 2000 });
    contracts.value = response.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Fehler', detail: 'Mietverträge konnten nicht geladen werden.', life: 3000 });
    console.error("Error fetching rental contracts:", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchContracts);

const openNewContractDialog = () => {
  currentContract.value = {
    status: 'PENDING',
    start_date: new Date().toISOString().split('T')[0], // Default to today
    // end_date: // can be set in form, e.g., +1 year
    rent_price_at_signing: null,
    shelf_id: null,
    tenant_supplier_id: null,
  };
  contractDialogVisible.value = true;
};

const editContract = (contract) => {
  // Ensure dates are in YYYY-MM-DD string format if they come as full datetime strings
  const contractCopy = { ...contract };
  if (contractCopy.start_date) contractCopy.start_date = contractCopy.start_date.split('T')[0];
  if (contractCopy.end_date) contractCopy.end_date = contractCopy.end_date.split('T')[0];
  currentContract.value = contractCopy;
  contractDialogVisible.value = true;
};

const hideContractDialog = () => {
  contractDialogVisible.value = false;
};

const onContractSubmit = async (contractToSave) => {
  isSubmittingContract.value = true;
  try {
    let savedContractData;
    if (contractToSave.id) {
      const response = await rentalContractService.updateRentalContract(contractToSave.id, contractToSave);
      savedContractData = response.data;
    } else {
      const response = await rentalContractService.createRentalContract(contractToSave);
      savedContractData = response.data;
    }
    toast.add({ severity: 'success', summary: 'Erfolgreich', detail: `Mietvertrag "${savedContractData.contract_number || 'Neu'}" gespeichert.`, life: 3000 });
    hideContractDialog();
    await fetchContracts();
  } catch (error) {
    const errorMsg = error.response?.data?.detail || 'Mietvertrag konnte nicht gespeichert werden.';
    toast.add({ severity: 'error', summary: 'Fehler beim Speichern', detail: errorMsg, life: 5000 });
    console.error("Error saving rental contract:", error);
  } finally {
    isSubmittingContract.value = false;
  }
};

const confirmDeleteContract = (contract) => {
  confirm.require({
    message: `Möchten Sie den Mietvertrag "${contract.contract_number}" wirklich löschen?`,
    header: 'Löschen bestätigen',
    icon: 'pi pi-info-circle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Löschen',
    rejectLabel: 'Abbrechen',
    accept: async () => {
      try {
        await rentalContractService.deleteRentalContract(contract.id);
        toast.add({ severity: 'success', summary: 'Gelöscht', detail: `Mietvertrag "${contract.contract_number}" gelöscht.`, life: 3000 });
        await fetchContracts();
      } catch (error) {
        const errorMsg = error.response?.data?.detail || 'Mietvertrag konnte nicht gelöscht werden.';
        toast.add({ severity: 'error', summary: 'Fehler beim Löschen', detail: errorMsg, life: 5000 });
        console.error("Error deleting rental contract:", error);
      }
    },
  });
};

const formatDate = (value) => {
  if (!value) return '';
  // Assuming value is already a date string YYYY-MM-DD or a Date object
  return new Date(value).toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit' });
};

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(value));
};

const getContractStatusLabel = (statusValue) => {
    const option = contractStatusOptions.value.find(opt => opt.value === statusValue);
    return option ? option.label : statusValue;
};

const getSeverityForContractStatus = (status) => {
  switch (status) {
    case 'ACTIVE': return 'success';
    case 'PENDING': return 'info';
    case 'EXPIRED': return 'warning';
    case 'TERMINATED': return 'danger';
    default: return 'secondary';
  }
};

// const printContract = (contract) => {
//   toast.add({ severity: 'info', summary: 'Info', detail: 'Vertragsdruck noch nicht implementiert.', life: 3000 });
//   // Logic for printing contract details, perhaps opening a new window/tab with a printable view
// };

</script>

<style scoped>
.rental-contract-list-view {
  padding: 1rem;
}
/* Add custom styles if needed, PrimeVue provides most styling */
</style>
