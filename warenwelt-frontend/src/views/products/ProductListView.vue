<template>
  <div class="product-list-view p-p-4">
    <Card>
      <template #title>
        <div class="flex justify-content-between align-items-center">
          <span>Artikelübersicht</span>
          <div>
            <router-link to="/products/print-price-tags" class="mr-2">
                <Button label="Preisschilder drucken" icon="pi pi-print" class="p-button-outlined" />
            </router-link>
            <router-link to="/products/new">
                <Button label="Neuen Artikel anlegen" icon="pi pi-plus" />
            </router-link>
          </div>
        </div>
      </template>
      <template #content>
        <DataTable
          :value="products"
          :loading="isLoading"
          paginator
          :rows="10"
          :rowsPerPageOptions="[5, 10, 20, 50]"
          responsiveLayout="scroll"
          v-model:filters="filters"
          filterDisplay="menu"
          :globalFilterFields="['sku', 'name', 'supplier.name', 'category.name', 'shelf_location']"
          dataKey="id"
        >
          <template #header>
            <div class="flex justify-content-between align-items-center">
              <div>
                <!-- Advanced filter options could go here -->
              </div>
              <span class="p-input-icon-left">
                <i class="pi pi-search" />
                <InputText v-model="filters['global'].value" placeholder="Globale Suche..." />
              </span>
            </div>
          </template>
          <template #empty>
            Keine Artikel gefunden.
          </template>
          <template #loading>
            Lade Artikeldaten...
          </template>

          <Column header="Bild" style="width: 80px">
            <template #body="{data}">
              <img v-if="data.image_url" :src="getFullImageUrl(data.image_url)" :alt="data.name" class="thumbnail" />
              <span v-else class="no-image-placeholder"><i class="pi pi-image" style="font-size: 2rem; color: var(--surface-400);"></i></span>
            </template>
          </Column>
          <Column field="sku" header="SKU" sortable filterField="sku" :showFilterMatchModes="false">
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach SKU"/>
            </template>
          </Column>
          <Column field="name" header="Name" sortable filterField="name" :showFilterMatchModes="false">
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Name"/>
            </template>
          </Column>
          <Column field="supplier.name" header="Lieferant" sortable filterField="supplier.name" :showFilterMatchModes="false">
            <template #body="{data}">
              {{ data.supplier?.supplier_number }} - {{ data.supplier?.company_name || data.supplier?.first_name }}
            </template>
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Lieferant"/>
            </template>
          </Column>
          <Column field="category.name" header="Kategorie" sortable filterField="category.name" :showFilterMatchModes="false">
             <template #body="{data}">{{ data.category?.name }}</template>
             <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Kategorie"/>
            </template>
          </Column>
          <Column field="shelf_location" header="Regalplatz" sortable filterField="shelf_location" :showFilterMatchModes="false">
            <template #body="{data}">{{ data.shelf_location || '-' }}</template>
            <template #filter="{filterModel,filterCallback}">
              <InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" placeholder="Filter nach Regal"/>
            </template>
          </Column>
          <Column field="selling_price" header="VK-Preis" sortable dataType="numeric">
            <template #body="{data}">{{ formatCurrency(data.selling_price) }}</template>
          </Column>
          <Column field="status" header="Status" sortable filterField="status" :showFilterMatchModes="false">
             <template #filter="{filterModel,filterCallback}">
                <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="productStatusOptions" placeholder="Status wählen" :showClear="true" class="p-column-filter">
                    <template #option="slotProps">
                        <span>{{translateProductStatus(slotProps.option)}}</span>
                    </template>
                     <template #value="slotProps">
                        <span v-if="slotProps.value">{{translateProductStatus(slotProps.value)}}</span>
                        <span v-else>{{slotProps.placeholder}}</span>
                    </template>
                </Dropdown>
            </template>
            <template #body="{data}">
                <Tag :value="translateProductStatus(data.status)" :severity="getStatusSeverity(data.status)" />
            </template>
          </Column>
          <Column header="Aktionen" style="min-width:8rem; text-align:center;">
            <template #body="{data}">
              <router-link :to="{ name: 'ProductEdit', params: { id: data.id } }">
                <Button icon="pi pi-pencil" class="p-button-rounded p-button-success p-mr-2" v-tooltip.top="'Bearbeiten'" />
              </router-link>
              <!-- Delete button -->
            </template>
          </Column>
        </DataTable>
        <small v-if="error" class="p-error block mt-2">{{ error }}</small>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import productService from '@/services/productService';
import { FilterMatchMode } from 'primevue/api';
import Tooltip from 'primevue/tooltip';
import Tag from 'primevue/tag'; // For status display

// Globally registered: Card, Button, DataTable, Column, InputText, Dropdown

const products = ref([]);
const isLoading = ref(true);
const error = ref('');

const filters = ref({
    'global': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'sku': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'supplier.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'category.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'shelf_location': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'status': { value: null, matchMode: FilterMatchMode.EQUALS },
});

// Options for status filter dropdown
const productStatusOptions = ref([
    'IN_STOCK', 'SOLD', 'RETURNED', 'DONATED', 'RESERVED'
]);

const translateProductStatus = (status) => {
  const translations = {
    IN_STOCK: 'Auf Lager',
    SOLD: 'Verkauft',
    RETURNED: 'Retourniert',
    DONATED: 'Gespendet',
    RESERVED: 'Reserviert'
  };
  return translations[status] || status;
};

const getStatusSeverity = (status) => {
  switch (status) {
    case 'IN_STOCK': return 'success';
    case 'SOLD': return 'info';
    case 'RETURNED': return 'warning';
    case 'DONATED': return 'contrast';
    case 'RESERVED': return 'primary';
    default: return null;
  }
};


const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const getFullImageUrl = (relativePath) => {
  if (!relativePath) return null;
  const backendRootUrl = (import.meta.env.VITE_API_BASE_URL || '').replace('/api/v1', '');
  return `${backendRootUrl}/static/${relativePath}`;
};

onMounted(async () => {
  isLoading.value = true;
  try {
    // Fetch all products, potentially with default filters or pagination from backend later
    const response = await productService.getProducts({ limit: 1000 }); // Example limit
    products.value = response.data.map(p => ({
        ...p,
        // Ensure supplier and category objects exist for nested field access in DataTable
        supplier: p.supplier || { name: '', supplier_number: ''},
        category: p.category || { name: ''}
    }));
  } catch (err) {
    error.value = 'Fehler beim Laden der Artikel: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoading.value = false;
  }
});

const vTooltip = Tooltip;
</script>

<style scoped>
.thumbnail {
  width: 50px; /* Fixed width */
  height: 50px; /* Fixed height */
  border-radius: 4px;
  object-fit: cover; /* Ensures the image covers the area without distortion */
  border: 1px solid var(--surface-d);
}
.no-image-placeholder {
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    /* background-color: var(--surface-c); */
    border-radius: 4px;
}
.p-error.block {
    display: block;
}
.mt-2 {
    margin-top: 0.5rem;
}
.mr-2 {
    margin-right: 0.5rem;
}

/* Ensure filter inputs in DataTable header are not too wide */
:deep(.p-column-filter) {
    width: 100%;
}
</style>
