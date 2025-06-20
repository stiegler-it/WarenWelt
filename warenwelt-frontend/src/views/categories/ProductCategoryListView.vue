<template>
  <div class="category-list-view p-p-4">
    <Card>
      <template #title>
        <div class="flex justify-content-between align-items-center">
          <span>Produktkategorien</span>
          <router-link to="/product-categories/new">
            <Button label="Neue Kategorie" icon="pi pi-plus" />
          </router-link>
        </div>
      </template>
      <template #content>
        <DataTable
          :value="categories"
          :loading="isLoading"
          paginator :rows="10" :rowsPerPageOptions="[5,10,20,50]"
          responsiveLayout="scroll"
          v-model:filters="filters"
          filterDisplay="menu"
          :globalFilterFields="['name']"
          dataKey="id"
        >
          <template #header>
            <div class="flex justify-content-end">
              <span class="p-input-icon-left">
                <i class="pi pi-search" />
                <InputText v-model="filters['global'].value" placeholder="Kategorien durchsuchen..." />
              </span>
            </div>
          </template>
          <template #empty>Keine Kategorien gefunden.</template>
          <template #loading>Lade Kategorien...</template>

          <Column field="id" header="ID" sortable style="width:10%"></Column>
          <Column field="name" header="Name" sortable filterField="name" :showFilterMatchModes="false">
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Name"/>
            </template>
          </Column>
          <Column field="differential_tax_surcharge_percent" header="Diff.-Bst. Aufschlag" sortable dataType="numeric" style="width:25%; text-align:right;">
            <template #body="{data}">
              {{ formatPercentage(data.differential_tax_surcharge_percent) }}
            </template>
          </Column>
          <Column header="Aktionen" style="min-width:10rem; text-align:center;">
            <template #body="{data}">
              <router-link :to="{ name: 'ProductCategoryEdit', params: { id: data.id } }">
                <Button icon="pi pi-pencil" class="p-button-rounded p-button-success p-mr-2" v-tooltip.top="'Bearbeiten'" />
              </router-link>
              <Button
                icon="pi pi-trash"
                class="p-button-rounded p-button-danger"
                @click="confirmDeleteCategory(data)"
                :loading="deleting[data.id]"
                v-tooltip.top="'Löschen'"
              />
            </template>
          </Column>
        </DataTable>
        <Message v-if="error" severity="error" :closable="true" @close="error=''" class="mt-3">{{ error }}</Message>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import productCategoryService from '@/services/productCategoryService';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import { FilterMatchMode } from 'primevue/api';
import Tooltip from 'primevue/tooltip';
// Globally registered: Card, Button, DataTable, Column, InputText, Message

const categories = ref([]);
const isLoading = ref(true);
const error = ref('');
const router = useRouter();
const toast = useToast();
const confirm = useConfirm();
const deleting = reactive({});

const filters = ref({
    'global': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'name': { value: null, matchMode: FilterMatchMode.CONTAINS },
});

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
    toast.add({severity:'error', summary: 'Ladefehler', detail: error.value, life: 5000});
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchCategories);

const confirmDeleteCategory = (category) => {
  confirm.require({
    message: `Sind Sie sicher, dass Sie die Kategorie "${category.name}" löschen möchten? Dies kann nicht rückgängig gemacht werden und könnte Produkte betreffen, die dieser Kategorie zugeordnet sind.`,
    header: 'Löschbestätigung',
    icon: 'pi pi-info-circle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Ja, löschen',
    rejectLabel: 'Abbrechen',
    accept: async () => {
      deleting[category.id] = true;
      error.value = '';
      try {
        await productCategoryService.deleteProductCategory(category.id);
        toast.add({severity:'success', summary: 'Gelöscht', detail: `Kategorie "${category.name}" erfolgreich gelöscht.`, life: 3000});
        fetchCategories();
      } catch (err) {
        const errorMsg = `Fehler beim Löschen der Kategorie "${category.name}": ` + (err.response?.data?.detail || err.message);
        error.value = errorMsg; // Show inline as well or just toast
        toast.add({severity:'error', summary: 'Löschfehler', detail: errorMsg, life: 5000});
      } finally {
        deleting[category.id] = false;
      }
    },
    reject: () => {
      // Optional: toast.add({severity:'info', summary:'Abgebrochen', detail:'Löschvorgang abgebrochen.', life: 3000});
    }
  });
};

const vTooltip = Tooltip;
</script>

<style scoped>
/* Using PrimeFlex for padding (p-p-4) and layout (flex, justify-content-between, etc.) */
.p-mr-2 {
    margin-right: 0.5rem;
}
:deep(.p-column-filter) {
    width: 100%;
}
</style>
