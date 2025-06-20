<template>
  <div class="price-tag-print-view p-p-4">
    <Card>
      <template #title>Preisschilder drucken</template>
      <template #content>
        <Panel header="Produktauswahl" toggleable class="non-printable mb-4">
          <p class="mb-2">Wählen Sie Produkte aus der Liste unten aus oder fügen Sie SKUs hinzu:</p>
          <div class="p-fluid grid align-items-center">
            <div class="field col-12 md:col-8">
              <label for="sku_to_add">SKU eingeben</label>
              <InputText id="sku_to_add" type="text" v-model="skuToAdd" placeholder="SKU" @keyup.enter="addProductBySkuToList" />
            </div>
            <div class="field col-12 md:col-4 flex align-items-end">
              <Button label="Hinzufügen" icon="pi pi-plus" @click="addProductBySkuToList" :disabled="!skuToAdd.trim() || isLoadingProductData" :loading="isLoadingProductData" class="w-full"/>
            </div>
          </div>
          <Message v-if="skuError" severity="error" :closable="true" @close="skuError=''">{{ skuError }}</Message>
        </Panel>

        <div class="controls-section non-printable mb-4">
            <Button
                label="Drucken"
                icon="pi pi-print"
                @click="printPriceTags"
                :disabled="selectedProductsForPrint.length === 0"
                class="p-button-lg"
            />
            <Button
                label="Auswahl löschen"
                icon="pi pi-times"
                @click="clearSelection"
                class="p-button-text p-button-danger ml-2"
                v-if="selectedProductsForPrint.length > 0"
            />
        </div>

        <div class="price-tags-preview printable-area p-p-2 surface-ground" ref="printableArea">
          <div v-if="selectedProductsForPrint.length === 0 && !isLoadingProductData" class="info-text non-printable text-center p-4">
            Noch keine Produkte für den Druck ausgewählt.
          </div>
          <div v-if="isLoadingProductData && selectedProductsForPrint.length === 0" class="text-center p-4 non-printable">
            <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
            <p>Lade Produktdaten...</p>
          </div>

          <div class="price-tag p-d-flex p-flex-column p-jc-between p-ai-center" v-for="tag in selectedProductsForPrint" :key="tag.sku">
            <div class="tag-product-name">{{ tag.product_name }}</div>
            <div class="tag-price">{{ formatCurrency(tag.selling_price) }}</div>
            <svg class="barcode"
              :jsbarcode-value="tag.sku"
              jsbarcode-format="CODE128"
              jsbarcode-displayValue="true"
              jsbarcode-width="1.8"
              jsbarcode-height="40"
              jsbarcode-margin="5"
              jsbarcode-fontSize="12"
              jsbarcode-textMargin="2">
            </svg>
          </div>
        </div>

        <Divider layout="horizontal" class="my-4 non-printable" />
        <h3 class="text-lg font-semibold mb-3 non-printable">Verfügbare Produkte zum Auswählen (IN_STOCK)</h3>
        <DataTable
            v-model:selection="dataTableSelectedProducts"
            :value="availableProducts"
            :loading="isLoadingAllProducts"
            paginator :rows="10" :rowsPerPageOptions="[5,10,20,50]"
            responsiveLayout="scroll"
            dataKey="id"
            @rowSelect="onProductRowSelect"
            @rowUnselect="onProductRowUnselect"
            @selectAllChange="onSelectAllChange"
            class="non-printable product-data-table"
            selectionMode="multiple"
        >
            <template #header>
                <div class="flex justify-content-end">
                    <span class="p-input-icon-left">
                        <i class="pi pi-search" />
                        <InputText v-model="productTableFilters['global'].value" placeholder="Produkte durchsuchen..." />
                    </span>
                </div>
            </template>
            <template #empty>Keine Produkte zum Auswählen gefunden.</template>
            <template #loading>Lade Produktliste...</template>

            <Column selectionMode="multiple" headerStyle="width: 3rem"></Column>
            <Column field="sku" header="SKU" sortable></Column>
            <Column field="name" header="Name" sortable></Column>
            <Column field="selling_price" header="Preis" sortable dataType="numeric">
                 <template #body="{data}">{{ formatCurrency(data.selling_price) }}</template>
            </Column>
        </DataTable>
        <Message v-if="allProductsError" severity="error" :closable="false" class="mt-2 non-printable">{{ allProductsError }}</Message>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import productService from '@/services/productService';
import JsBarcode from 'jsbarcode';
import { useToast } from 'primevue/usetoast';
import Panel from 'primevue/panel';
import Divider from 'primevue/divider';
// Globally registered: Card, Button, InputText, Message, DataTable, Column

const toast = useToast();
const skuToAdd = ref('');
const skuError = ref('');
const selectedProductsForPrint = ref([]); // Array of PriceTagData objects with product_id_temp
const isLoadingProductData = ref(false);
const isLoadingAllProducts = ref(false);
const allProductsError = ref('');

const availableProducts = ref([]);
const dataTableSelectedProducts = ref([]); // For DataTable v-model:selection

const productTableFilters = ref({
    'global': { value: null, matchMode: 'contains' }, // Using PrimeVue's FilterMatchMode.CONTAINS implicitly
});


const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const fetchAvailableProducts = async () => {
    isLoadingAllProducts.value = true;
    allProductsError.value = '';
    try {
        const response = await productService.getProducts({ limit: 2000, status: "IN_STOCK" });
        availableProducts.value = response.data;
        // Sync dataTableSelectedProducts with selectedProductsForPrint
        dataTableSelectedProducts.value = availableProducts.value.filter(p =>
            selectedProductsForPrint.value.some(sp => sp.product_id_temp === p.id)
        );
    } catch (err) {
        allProductsError.value = "Fehler beim Laden der Produktliste: " + (err.response?.data?.detail || err.message);
        toast.add({severity:'error', summary:'Produktliste Fehler', detail: allProductsError.value, life: 3000});
    } finally {
        isLoadingAllProducts.value = false;
    }
};

onMounted(() => {
    fetchAvailableProducts();
});

const addProductToPrintList = async (productId, sku, name, price) => {
    if (selectedProductsForPrint.value.find(p => p.product_id_temp === productId)) {
        skuError.value = `Produkt ${sku} ist bereits in der Druckauswahl.`;
        toast.add({severity:'warn', summary:'Bereits vorhanden', detail: skuError.value, life:3000});
        return false;
    }
    try {
        // Use existing data if passed (from table selection), else fetch
        let tagData;
        if (name && price !== undefined) {
            tagData = { product_name: name, sku: sku, selling_price: price };
        } else {
             isLoadingProductData.value = true; // Show loading for individual fetch
            const response = await productService.getPriceTagData(productId);
            tagData = response.data;
        }
        selectedProductsForPrint.value.push({ ...tagData, product_id_temp: productId });
        await nextTick();
        renderBarcodes();
        return true;
    } catch (err) {
        const errorMsg = `Fehler beim Hinzufügen von ${sku || 'Produkt'}: ${err.response?.data?.detail || err.message}`;
        skuError.value = errorMsg;
        toast.add({severity:'error', summary:'Fehler', detail: errorMsg, life:3000});
        return false;
    } finally {
        isLoadingProductData.value = false;
    }
};

const addProductBySkuToList = async () => {
  if (!skuToAdd.value.trim()) return;
  skuError.value = '';
  isLoadingProductData.value = true;
  try {
    const productResponse = await productService.getProductBySku(skuToAdd.value.trim());
    if (productResponse.data) {
        await addProductToPrintList(productResponse.data.id, productResponse.data.sku, productResponse.data.name, productResponse.data.selling_price);
        skuToAdd.value = '';
    } else {
        skuError.value = `Produkt mit SKU '${skuToAdd.value.trim()}' nicht gefunden.`;
        toast.add({severity:'error', summary:'Nicht gefunden', detail: skuError.value, life:3000});
    }
  } catch (err) {
    const errorMsg = `Fehler bei SKU-Suche: ${err.response?.data?.detail || err.message}`;
    skuError.value = errorMsg;
    toast.add({severity:'error', summary:'Fehler', detail: errorMsg, life:3000});
  } finally {
    isLoadingProductData.value = false;
  }
};

const removeProductFromPrintList = (productId) => {
    const index = selectedProductsForPrint.value.findIndex(p => p.product_id_temp === productId);
    if (index > -1) {
        selectedProductsForPrint.value.splice(index, 1);
    }
};

const onProductRowSelect = (event) => {
    addProductToPrintList(event.data.id, event.data.sku, event.data.name, event.data.selling_price);
};

const onProductRowUnselect = (event) => {
    removeProductFromPrintList(event.data.id);
};

const onSelectAllChange = (event) => {
    if (event.checked) { // All items on current page selected
        event.originalEvent.target.value.forEach(product => { // originalEvent.target.value is not standard, need to check PrimeVue docs
            // This is tricky with paginated DataTable. A better approach might be a separate "Add all visible" / "Add all filtered" button.
            // For now, let's assume event.data is the list of items that got selected due to "select all" on current page.
            // PrimeVue's selectAll event is complex with pagination. A simpler way:
            // If "select all" is checked, iterate `availableProducts` if filtered, or all if not.
            // This example will just add the currently selected items in dataTableSelectedProducts.
            dataTableSelectedProducts.value.forEach(p => addProductToPrintList(p.id, p.sku, p.name, p.selling_price));
        });
    } else { // All items unselected
        // This also needs careful handling with pagination.
        // For now, if unselect all, clear all from print list that are in current availableProducts.
        const availableIds = availableProducts.value.map(p => p.id);
        selectedProductsForPrint.value = selectedProductsForPrint.value.filter(
            sp => !availableIds.includes(sp.product_id_temp)
        );
    }
};
// Watch to keep DataTable selection in sync if selectedProductsForPrint changes externally (e.g. by SKU add)
watch(selectedProductsForPrint, (newSelection) => {
    dataTableSelectedProducts.value = availableProducts.value.filter(p =>
        newSelection.some(sp => sp.product_id_temp === p.id)
    );
}, { deep: true });


const renderBarcodes = () => {
  const printableElement = document.querySelector('.printable-area');
  if (printableElement) {
      printableElement.querySelectorAll('.barcode').forEach(barcodeElement => {
          try {
            JsBarcode(barcodeElement).init();
          } catch (e) {
            console.error("JsBarcode Fehler:", e, "für Element:", barcodeElement);
            const skuValue = barcodeElement.getAttribute('jsbarcode-value');
            const errorP = document.createElement('p');
            errorP.className = 'barcode-error p-error text-xs';
            errorP.textContent = `Barcode für ${skuValue} Fehler.`;
            barcodeElement.parentElement.appendChild(errorP);
          }
      });
  }
};

const clearSelection = () => {
    selectedProductsForPrint.value = [];
    dataTableSelectedProducts.value = []; // Clear DataTable selection as well
};

const printPriceTags = async () => {
  if (selectedProductsForPrint.value.length === 0) return;
  await nextTick();
  renderBarcodes();
  await nextTick();
  window.print();
};

</script>

<style>
/* Styles specific to this view */
.price-tag-print-view {
  /* max-width: 1000px; Using Card, it will manage width */
}

.controls-section {
  /* background-color: var(--surface-section); PrimeVue Panel has its own bg */
  /* padding: 15px; */ /* Use PrimeFlex or Panel's own padding */
  /* border-radius: var(--border-radius); */
  /* margin-bottom: 20px; */
  /* border: 1px solid var(--surface-border); */
}

.price-tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 1rem; /* PrimeFlex my-4 */
  padding: 1rem; /* PrimeFlex p-4 */
  border: 1px dashed var(--surface-d);
  min-height: 100px;
}

.price-tag {
  border: 1px solid black;
  padding: 10px;
  width: 180px; /* Adjusted width */
  height: 100px; /* Adjusted height */
  text-align: center;
  /* display: flex; -> PrimeFlex p-d-flex */
  /* flex-direction: column; -> PrimeFlex p-flex-column */
  /* justify-content: space-between; -> PrimeFlex p-jc-between */
  /* align-items: center; -> PrimeFlex p-ai-center */
  page-break-inside: avoid;
  background-color: white;
  box-sizing: border-box;
}

.tag-product-name {
  font-weight: bold;
  font-size: 0.9em; /* Adjusted */
  margin-bottom: 3px; /* Adjusted */
  word-break: break-word;
  line-height: 1.2;
  max-height: 2.4em; /* Approx 2 lines */
  overflow: hidden;
}

.tag-price {
  font-size: 1.2em; /* Adjusted */
  font-weight: bold;
  margin-bottom: 3px; /* Adjusted */
}

.barcode {
  width: 100%;
  max-height: 40px; /* Adjusted */
}
.barcode-error {
    /* color: var(--red-500); PrimeVue p-error */
    font-size: 0.7rem; /* PrimeFlex text-xs */
}

.product-data-table .p-datatable-tbody > tr.p-highlight { /* Style for selected rows in DataTable */
    background-color: var(--primary-100) !important; /* Example, adjust as needed */
    font-weight: bold;
}
.info-text {
    width: 100%;
    text-align: center;
    color: var(--text-color-secondary);
    /* padding: 20px; PrimeFlex p-4 */
}

/* Print-specific styles */
@media print {
  body * {
    visibility: hidden;
  }
  .printable-area, .printable-area * {
    visibility: visible;
  }
  .printable-area {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    margin: 0;
    padding: 0;
    border: none;
  }
  .non-printable {
    display: none !important;
  }
  .price-tag {
    border: 1px solid black;
    margin: 3mm; /* Adjusted margin for print */
    width: 60mm; /* Example: Zettle L (62mm x 29mm) - adjust width */
    height: 25mm; /* Adjust height */
    padding: 2mm;
  }
  .tag-product-name { font-size: 8pt; max-height: 2.5em; margin-bottom: 1mm;}
  .tag-price { font-size: 10pt; margin-bottom: 1mm;}
  .barcode { max-height: 10mm; }
  svg.barcode > g > text { font-size: 7pt !important; } /* Force font size for barcode text */
}
</style>
