<template>
  <div class="supplier-list-view p-p-4">
    <Card>
      <template #title>
        <div class="flex justify-content-between align-items-center">
          <span>Lieferantenübersicht</span>
          <router-link to="/suppliers/new">
            <Button label="Neuen Lieferant anlegen" icon="pi pi-plus" />
          </router-link>
        </div>
      </template>
      <template #content>
        <DataTable
          :value="suppliers"
          :loading="isLoading"
          paginator
          :rows="10"
          :rowsPerPageOptions="[5, 10, 20, 50]"
          responsiveLayout="scroll"
          v-model:filters="filters"
          filterDisplay="menu"
          :globalFilterFields="['supplier_number', 'name', 'email']"
        >
          <template #header>
            <div class="flex justify-content-end">
              <span class="p-input-icon-left">
                <i class="pi pi-search" />
                <InputText v-model="filters['global'].value" placeholder="Suche..." />
              </span>
            </div>
          </template>
          <template #empty>
            Keine Lieferanten gefunden.
          </template>
          <template #loading>
            Lade Lieferantendaten...
          </template>

          <Column field="supplier_number" header="Nr." sortable filterField="supplier_number" :showFilterMatchModes="false">
            <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Nr."/>
            </template>
          </Column>
          <Column field="name" header="Name" sortable filterField="name" :showFilterMatchModes="false">
             <template #body="{data}">
              {{ data.company_name || (data.first_name + ' ' + data.last_name) }}
            </template>
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Name"/>
            </template>
          </Column>
          <Column field="email" header="Email" sortable filterField="email" :showFilterMatchModes="false">
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Email"/>
            </template>
          </Column>
          <Column field="phone" header="Telefon" sortable></Column>
          <Column field="is_internal" header="Intern" sortable dataType="boolean">
            <template #body="{data}">
              <i class="pi" :class="{'true-icon pi-check-circle': data.is_internal, 'false-icon pi-times-circle': !data.is_internal}"></i>
            </template>
          </Column>
          <Column header="Aktionen" style="min-width:10rem">
            <template #body="{data}">
              <router-link :to="{ name: 'SupplierEdit', params: { id: data.id } }">
                <Button icon="pi pi-pencil" class="p-button-rounded p-button-success p-mr-2" v-tooltip.top="'Bearbeiten'" />
              </router-link>
              <!-- Delete button would require confirmation logic -->
              <!-- <Button icon="pi pi-trash" class="p-button-rounded p-button-warning" @click="confirmDeleteSupplier(data)" /> -->
            </template>
          </Column>
        </DataTable>
        <small v-if="error" class="p-error">{{ error }}</small>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import supplierService from '@/services/supplierService';
import { FilterMatchMode, FilterOperator } from 'primevue/api'; // For DataTable filtering
import Tooltip from 'primevue/tooltip'; // Import Tooltip directive

// PrimeVue components (Button, Card, DataTable, Column, InputText) are globally registered

const suppliers = ref([]);
const isLoading = ref(true);
const error = ref('');

const filters = ref({
    'global': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'supplier_number': { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    'name': { value: null, matchMode: FilterMatchMode.CONTAINS }, // Custom logic for combined name needed if backend doesn't support it
    'email': { value: null, matchMode: FilterMatchMode.CONTAINS },
});


onMounted(async () => {
  try {
    // Add a name field to each supplier for easier filtering/sorting if not present
    const response = await supplierService.getSuppliers();
    suppliers.value = response.data.map(s => ({
        ...s,
        name: s.company_name || `${s.first_name || ''} ${s.last_name || ''}`.trim()
    }));
  } catch (err) {
    error.value = 'Fehler beim Laden der Lieferanten: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoading.value = false;
  }
});

// Add v-tooltip directive
const vTooltip = Tooltip;

// Delete confirmation logic would go here
// const confirmDeleteSupplier = (supplier) => { ... }
</script>

<style scoped>
/* Using PrimeFlex for padding (p-p-4) and layout (flex, justify-content-between, etc.) */
.true-icon {
  color: var(--green-500);
}
.false-icon {
  color: var(--red-500);
}
.p-mr-2 { /* PrimeFlex class for margin */
    margin-right: 0.5rem;
}
</style>
