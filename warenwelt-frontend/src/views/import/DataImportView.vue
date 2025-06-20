<template>
  <div class="data-import-view p-4">
    <Toast />
    <Card>
      <template #title>Datenimport per CSV</template>
      <template #content>
        <TabView ref="tabview">
          <TabPanel header="Lieferanten Importieren">
            <div class="p-fluid grid formgrid">
              <div class="field col-12">
                <h6 class="font-semibold">Lieferanten CSV-Datei auswählen</h6>
                <FileUpload name="supplierCsvFile" ref="supplierUploadRef" @uploader="onSupplierUpload" :customUpload="true"
                            accept=".csv" :maxFileSize="5000000" chooseLabel="Datei wählen" uploadLabel="Hochladen & Importieren" cancelLabel="Abbrechen"
                            :auto="false" class="mb-3">
                  <template #empty>
                    <div class="text-center p-3 border-1 surface-border border-round">
                        <i class="pi pi-upload text-4xl text-primary mb-2"></i>
                        <p class="font-semibold">CSV-Datei hierher ziehen oder "Datei wählen" klicken.</p>
                        <p class="text-sm text-color-secondary">Erforderliche Spalten: `supplier_number`.</p>
                        <p class="text-sm text-color-secondary">Empfohlen: `company_name`, `first_name`, `last_name`, `email`, `phone`, `is_internal` (true/false).</p>
                        <p class="text-sm text-color-secondary">Trennzeichen: Semikolon (;). Kodierung: UTF-8 (empfohlen) oder Latin-1.</p>
                    </div>
                  </template>
                </FileUpload>
              </div>
              <div class="field col-12" v-if="supplierImportResult">
                <Message :severity="supplierImportResult.errors && supplierImportResult.errors.length > 0 ? 'warn' : 'success'" :closable="false">
                  Import abgeschlossen: {{ supplierImportResult.imported_count }} importiert, {{ supplierImportResult.skipped_count }} übersprungen.
                </Message>
                <DataTable v-if="supplierImportResult.errors && supplierImportResult.errors.length > 0" :value="supplierImportResult.errors" class="p-datatable-sm mt-2" responsiveLayout="scroll" :rows="5" paginator>
                  <template #header><div class="text-lg font-semibold">Fehlerdetails (Lieferanten)</div></template>
                  <Column field="row" header="Zeile CSV" style="width:10%"></Column>
                  <Column field="message" header="Fehler" style="width:40%"></Column>
                  <Column field="data" header="Fehlerhafte Daten (Auszug)" style="width:50%">
                    <template #body="{data}"> <pre>{{ JSON.stringify(data.data, truncateJsonData, 2) }}</pre> </template>
                  </Column>
                </DataTable>
              </div>
            </div>
          </TabPanel>

          <TabPanel header="Produkte Importieren">
            <div class="p-fluid grid formgrid">
              <div class="field col-12">
                <h6 class="font-semibold">Produkt CSV-Datei auswählen</h6>
                <FileUpload name="productCsvFile" ref="productUploadRef" @uploader="onProductUpload" :customUpload="true"
                            accept=".csv" :maxFileSize="10000000" chooseLabel="Datei wählen" uploadLabel="Hochladen & Importieren" cancelLabel="Abbrechen"
                            :auto="false" class="mb-3">
                  <template #empty>
                    <div class="text-center p-3 border-1 surface-border border-round">
                        <i class="pi pi-upload text-4xl text-primary mb-2"></i>
                        <p class="font-semibold">CSV-Datei hierher ziehen oder "Datei wählen" klicken.</p>
                        <p class="text-sm text-color-secondary">Erforderliche Spalten: `sku`, `name`, `supplier_number`, `category_name`, `tax_rate_name`, `purchase_price`, `selling_price`, `product_type`.</p>
                        <p class="text-sm text-color-secondary">Optionale Spalten: `description`, `status`, `entry_date`.</p>
                        <p class="text-sm text-color-secondary">Trennzeichen: Semikolon (;). Kodierung: UTF-8 (empfohlen) oder Latin-1.</p>
                    </div>
                  </template>
                </FileUpload>
              </div>
               <div class="field col-12" v-if="productImportResult">
                <Message :severity="productImportResult.errors && productImportResult.errors.length > 0 ? 'warn' : 'success'" :closable="false">
                  Import abgeschlossen: {{ productImportResult.imported_count }} importiert, {{ productImportResult.skipped_count }} übersprungen.
                </Message>
                <DataTable v-if="productImportResult.errors && productImportResult.errors.length > 0" :value="productImportResult.errors" class="p-datatable-sm mt-2" responsiveLayout="scroll" :rows="5" paginator>
                  <template #header><div class="text-lg font-semibold">Fehlerdetails (Produkte)</div></template>
                  <Column field="row" header="Zeile CSV" style="width:10%"></Column>
                  <Column field="message" header="Fehler" style="width:40%"></Column>
                  <Column field="data" header="Fehlerhafte Daten (Auszug)" style="width:50%">
                     <template #body="{data}"> <pre>{{ JSON.stringify(data.data, truncateJsonData, 2) }}</pre> </template>
                  </Column>
                </DataTable>
              </div>
            </div>
          </TabPanel>
        </TabView>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useToast } from 'primevue/usetoast';
import FileUpload from 'primevue/fileupload';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Message from 'primevue/message';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Card from 'primevue/card';
import Toast from 'primevue/toast';
import Button from 'primevue/button'; // Although not explicitly used, FileUpload might use it internally or for styling consistency

import importService from '@/services/importService';

const toast = useToast();

const supplierUploadRef = ref(null);
const productUploadRef = ref(null);

const supplierImportResult = ref(null);
const productImportResult = ref(null);

const onSupplierUpload = async (event) => {
  const file = event.files[0];
  if (!file) {
    toast.add({ severity: 'warn', summary: 'Keine Datei', detail: 'Bitte wählen Sie eine Datei für den Lieferantenimport aus.', life: 3000 });
    return;
  }

  supplierImportResult.value = null;
  try {
    const response = await importService.importSuppliersCSV(file);
    supplierImportResult.value = response.data; // Backend returns { imported_count, skipped_count, errors }
    toast.add({
      severity: response.data.errors && response.data.errors.length > 0 ? 'warn' : 'success',
      summary: 'Lieferantenimport Ergebnis',
      detail: `${response.data.imported_count} importiert, ${response.data.skipped_count} übersprungen.`,
      life: 6000
    });
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || 'Fehler beim Lieferantenimport.';
    supplierImportResult.value = { errors: [{ row: 'N/A', message: errorMsg, data:{} }], imported_count: 0, skipped_count: 'N/A' };
    toast.add({ severity: 'error', summary: 'Importfehler', detail: errorMsg, life: 6000 });
  } finally {
    if (supplierUploadRef.value) { // Check if ref is available
        supplierUploadRef.value.clear(); // PrimeVue's FileUpload clear method
    }
  }
};

const onProductUpload = async (event) => {
  const file = event.files[0];
   if (!file) {
    toast.add({ severity: 'warn', summary: 'Keine Datei', detail: 'Bitte wählen Sie eine Datei für den Produktimport aus.', life: 3000 });
    return;
  }

  productImportResult.value = null;
  try {
    const response = await importService.importProductsCSV(file);
    productImportResult.value = response.data;
    toast.add({
      severity: response.data.errors && response.data.errors.length > 0 ? 'warn' : 'success',
      summary: 'Produktimport Ergebnis',
      detail: `${response.data.imported_count} importiert, ${response.data.skipped_count} übersprungen.`,
      life: 6000
    });
  } catch (error) {
    const errorMsg = error.response?.data?.detail || error.message || 'Fehler beim Produktimport.';
    productImportResult.value = { errors: [{ row: 'N/A', message: errorMsg, data:{} }], imported_count: 0, skipped_count: 'N/A' };
    toast.add({ severity: 'error', summary: 'Importfehler', detail: errorMsg, life: 6000 });
  } finally {
    if (productUploadRef.value) {
        productUploadRef.value.clear();
    }
  }
};

// Helper to truncate long data strings in error table for better display
const truncateJsonData = (key, value) => {
  if (typeof value === 'string' && value.length > 100) {
    return value.substring(0, 97) + '...';
  }
  return value;
};

</script>

<style scoped>
.data-import-view {
  padding: 1rem;
}
.p-fileupload-content p {
    margin-bottom: 0.5rem;
}
pre {
    white-space: pre-wrap;
    white-space: -moz-pre-wrap;
    white-space: -pre-wrap;
    white-space: -o-pre-wrap;
    word-wrap: break-word;
    background-color: var(--surface-100); /* Slightly different background */
    padding: 0.5em;
    border-radius: 3px;
    font-size: 0.85em;
    border: 1px solid var(--surface-border);
    max-height: 150px; /* Limit height of pre block */
    overflow-y: auto; /* Add scroll for long data */
}
:deep(.p-fileupload-buttonbar .p-button) {
    margin-right: 0.5rem; /* Spacing for buttons in FileUpload */
}
:deep(.p-datatable-sm .p-datatable-tbody > tr > td) {
    vertical-align: top;
}
.field h6 {
    margin-bottom: 0.75rem; /* Space below the sub-header */
}
</style>
