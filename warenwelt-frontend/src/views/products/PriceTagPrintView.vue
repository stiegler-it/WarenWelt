<template>
  <div class="price-tag-print-view">
    <h1>Preisschilder drucken</h1>

    <div class="product-selection controls-section non-printable">
      <p>Wählen Sie Produkte aus der Liste unten aus oder fügen Sie SKUs hinzu:</p>
      <div class="sku-input-group">
        <input type="text" v-model="skuToAdd" placeholder="SKU eingeben" @keyup.enter="addProductBySkuToList" />
        <button @click="addProductBySkuToList" :disabled="!skuToAdd.trim()">Produkt per SKU hinzufügen</button>
      </div>
       <p v-if="skuError" class="error-message">{{ skuError }}</p>
    </div>

    <div class="controls-section non-printable">
        <button @click="printPriceTags" :disabled="selectedProductsForPrint.length === 0">
            Ausgewählte Preisschilder drucken ({{ selectedProductsForPrint.length }})
        </button>
        <button @click="clearSelection" class="button secondary" v-if="selectedProductsForPrint.length > 0">
            Auswahl löschen
        </button>
    </div>

    <div class="price-tags-preview printable-area" ref="printableArea">
      <div v-if="selectedProductsForPrint.length === 0 && !isLoadingProductData" class="info-text non-printable">
        Noch keine Produkte für den Druck ausgewählt.
      </div>
      <div v-if="isLoadingProductData" class="loading non-printable">Lade Produktdaten für Preisschilder...</div>

      <div class="price-tag" v-for="tag in selectedProductsForPrint" :key="tag.sku">
        <div class="tag-product-name">{{ tag.product_name }}</div>
        <div class="tag-price">{{ formatCurrency(tag.selling_price) }}</div>
        <svg class="barcode"
          :jsbarcode-value="tag.sku"
          jsbarcode-format="CODE128"
          jsbarcode-displayValue="true"
          jsbarcode-width="2"
          jsbarcode-height="50"
          jsbarcode-margin="5"
          jsbarcode-fontSize="14"
          jsbarcode-textMargin="2">
        </svg>
      </div>
    </div>

    <hr class="non-printable" />
    <h2 class="non-printable">Verfügbare Produkte zum Auswählen</h2>
    <div class="product-list-selector non-printable">
        <!-- Using ProductListView logic or a simplified list -->
        <div v-if="isLoadingAllProducts" class="loading">Lade Produktliste...</div>
        <div v-if="allProductsError" class="error-message">{{ allProductsError }}</div>
        <table v-if="availableProducts.length > 0">
            <thead>
                <tr>
                    <th>Auswählen</th>
                    <th>SKU</th>
                    <th>Name</th>
                    <th>Preis</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="product in availableProducts" :key="product.id" @click="toggleProductSelection(product)" :class="{ 'selected-row': isSelectedForPrint(product.id) }">
                    <td><input type="checkbox" :checked="isSelectedForPrint(product.id)" @change="toggleProductSelection(product)" @click.stop /></td>
                    <td>{{ product.sku }}</td>
                    <td>{{ product.name }}</td>
                    <td>{{ formatCurrency(product.selling_price) }}</td>
                </tr>
            </tbody>
        </table>
         <p v-if="!isLoadingAllProducts && availableProducts.length === 0">Keine Produkte zum Auswählen gefunden.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import productService from '@/services/productService';
import JsBarcode from 'jsbarcode';

const skuToAdd = ref('');
const skuError = ref('');
const selectedProductsForPrint = ref([]); // Array of PriceTagData objects
const isLoadingProductData = ref(false); // For loading individual tag data via SKU
const isLoadingAllProducts = ref(false); // For loading the list of available products
const allProductsError = ref('');

const availableProducts = ref([]); // List of all products to select from

const formatCurrency = (value) => {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const fetchAvailableProducts = async () => {
    isLoadingAllProducts.value = true;
    allProductsError.value = '';
    try {
        const response = await productService.getProducts({ limit: 1000, status: "IN_STOCK" }); // Load IN_STOCK products
        availableProducts.value = response.data;
    } catch (err) {
        allProductsError.value = "Fehler beim Laden der Produktliste: " + (err.response?.data?.detail || err.message);
    } finally {
        isLoadingAllProducts.value = false;
    }
};

onMounted(() => {
    fetchAvailableProducts();
});

const addProductById = async (productId) => {
    if (selectedProductsForPrint.value.find(p => p.product_id === productId)) { // Assuming PriceTagData gets a product_id or we check by SKU
        skuError.value = `Produkt ist bereits in der Druckauswahl.`;
        return;
    }
    isLoadingProductData.value = true;
    skuError.value = '';
    try {
        const response = await productService.getPriceTagData(productId);
        // Add a temporary product_id to PriceTagData for easier selection tracking if needed
        selectedProductsForPrint.value.push({ ...response.data, product_id_temp: productId });
        await nextTick(); // Wait for DOM update
        renderBarcodes();
    } catch (err) {
        skuError.value = `Fehler beim Hinzufügen des Produkts: ${err.response?.data?.detail || err.message}`;
    } finally {
        isLoadingProductData.value = false;
    }
};


const addProductBySkuToList = async () => {
  if (!skuToAdd.value.trim()) return;
  if (selectedProductsForPrint.value.find(p => p.sku === skuToAdd.value.trim())) {
      skuError.value = `Produkt mit SKU ${skuToAdd.value.trim()} ist bereits in der Druckauswahl.`;
      return;
  }
  isLoadingProductData.value = true;
  skuError.value = '';
  try {
    // First, find the product by SKU to get its ID for the price tag data endpoint
    const productResponse = await productService.getProductBySku(skuToAdd.value.trim());
    if (productResponse.data) {
        const tagDataResponse = await productService.getPriceTagData(productResponse.data.id);
        selectedProductsForPrint.value.push({ ...tagDataResponse.data, product_id_temp: productResponse.data.id });
        await nextTick();
        renderBarcodes();
        skuToAdd.value = ''; // Clear input
    } else {
        skuError.value = `Produkt mit SKU '${skuToAdd.value.trim()}' nicht gefunden.`;
    }
  } catch (err) {
    skuError.value = `Fehler: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoadingProductData.value = false;
  }
};

const isSelectedForPrint = (productId) => {
    return selectedProductsForPrint.value.some(p => p.product_id_temp === productId);
};

const toggleProductSelection = async (product) => {
    const index = selectedProductsForPrint.value.findIndex(p => p.product_id_temp === product.id);
    if (index > -1) {
        selectedProductsForPrint.value.splice(index, 1);
    } else {
        // Fetch price tag data for this product
        isLoadingProductData.value = true;
        skuError.value = '';
        try {
            const tagDataResponse = await productService.getPriceTagData(product.id);
            selectedProductsForPrint.value.push({ ...tagDataResponse.data, product_id_temp: product.id });
            await nextTick();
            renderBarcodes();
        } catch (err) {
             skuError.value = `Fehler beim Abrufen der Preisschilddaten für ${product.sku}: ${err.response?.data?.detail || err.message}`;
        } finally {
            isLoadingProductData.value = false;
        }
    }
};


const renderBarcodes = () => {
  // Ensure JsBarcode is loaded (it is, via import)
  // Select all elements with class 'barcode' within the printable area
  const printableElement = document.querySelector('.printable-area');
  if (printableElement) {
      printableElement.querySelectorAll('.barcode').forEach(barcodeElement => {
          try {
            JsBarcode(barcodeElement).init();
          } catch (e) {
            console.error("JsBarcode Fehler:", e, "für Element:", barcodeElement);
            // Handle error, e.g. by displaying text SKU
            const skuValue = barcodeElement.getAttribute('jsbarcode-value');
            barcodeElement.parentElement.innerHTML += `<p class='barcode-error'>Barcode für ${skuValue} konnte nicht generiert werden.</p>`;
          }
      });
  }
};

const clearSelection = () => {
    selectedProductsForPrint.value = [];
};

const printPriceTags = async () => {
  if (selectedProductsForPrint.value.length === 0) return;
  // Ensure all barcodes are rendered before printing
  await nextTick(); // Wait for any DOM updates from adding products
  renderBarcodes(); // Re-render just in case
  await nextTick(); // Wait for barcodes to render
  window.print();
};

</script>

<style>
/* Styles specific to this view */
.price-tag-print-view {
  max-width: 1000px; /* Allow wider view for product list */
  margin: auto;
}

.controls-section {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  border: 1px solid #dee2e6;
}
.sku-input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
}
.sku-input-group input {
    flex-grow: 1;
}

.price-tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px; /* Abstand zwischen den Schildern */
  margin-top: 20px;
  padding: 10px;
  border: 1px dashed #ccc; /* Nur zur Visualisierung des Druckbereichs */
  min-height: 100px; /* Damit der Kasten sichtbar ist, auch wenn leer */
}

.price-tag {
  border: 1px solid black;
  padding: 10px;
  width: 200px; /* Beispielbreite, anpassen nach Bedarf */
  height: 120px; /* Beispielhöhe */
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  page-break-inside: avoid; /* Verhindert Umbruch innerhalb eines Schildes */
  background-color: white; /* Wichtig für Druck */
  box-sizing: border-box;
}

.tag-product-name {
  font-weight: bold;
  font-size: 1em;
  margin-bottom: 5px;
  word-break: break-word;
}

.tag-price {
  font-size: 1.4em;
  font-weight: bold;
  margin-bottom: 5px;
}

.barcode {
  width: 90%; /* Breite des Barcodes relativ zum Schild */
  max-height: 60px; /* Maximale Höhe des Barcodes */
}
.barcode-error {
    color: red;
    font-size: 0.8em;
}

.product-list-selector table {
    margin-top: 10px;
}
.product-list-selector tr:hover {
    cursor: pointer;
    background-color: #f0f0f0;
}
.selected-row {
    background-color: #cfe2ff !important; /* Bootstrap 'table-primary' like */
    font-weight: bold;
}

.info-text {
    width: 100%;
    text-align: center;
    color: #666;
    padding: 20px;
}


/* Print-specific styles */
@media print {
  body * {
    visibility: hidden; /* Alles ausblenden */
  }
  .printable-area, .printable-area * {
    visibility: visible; /* Nur den Druckbereich und dessen Kinder sichtbar machen */
  }
  .printable-area {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    margin: 0;
    padding: 0;
    border: none; /* Keinen Rand im Druck */
  }
  .non-printable {
    display: none !important; /* Elemente, die nicht gedruckt werden sollen */
  }
  .price-tag {
    border: 1px solid black; /* Rand für die Schilder im Druck beibehalten */
    margin: 5mm; /* Abstand zwischen Schildern im Druck anpassen */
     /* Hier können spezifische Druckgrößen eingestellt werden, z.B. für Etikettenbögen */
  }
}
</style>
