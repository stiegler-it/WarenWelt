<template>
  <div class="product-edit-view">
    <h1>{{ isNew ? 'Neuen Artikel anlegen' : 'Artikel bearbeiten' }}</h1>
    <form @submit.prevent="saveProduct" v-if="!pageLoading">
      <div class="form-group">
        <label for="name">Artikelname:</label>
        <input type="text" id="name" v-model="product.name" required />
      </div>
      <div class="form-group">
        <label for="sku">SKU (Barcode - leer lassen für Auto-Generierung):</label>
        <input type="text" id="sku" v-model="product.sku" :disabled="!isNew && product.sku"/>
      </div>
      <div class="form-group">
        <label for="description">Beschreibung:</label>
        <textarea id="description" v-model="product.description"></textarea>
      </div>
      <div class="form-group">
        <label for="supplier_id">Lieferant:</label>
        <select id="supplier_id" v-model.number="product.supplier_id" required>
          <option disabled value="">Bitte wählen</option>
          <option v-for="s in availableSuppliers" :key="s.id" :value="s.id">
            {{ s.supplier_number }} - {{ s.company_name || s.first_name + ' ' + s.last_name }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="category_id">Kategorie:</label>
        <select id="category_id" v-model.number="product.category_id" required>
          <option disabled value="">Bitte wählen</option>
          <option v-for="c in availableCategories" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="tax_rate_id">Steuersatz:</label>
        <select id="tax_rate_id" v-model.number="product.tax_rate_id" required>
          <option disabled value="">Bitte wählen</option>
          <option v-for="t in availableTaxRates" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.rate_percent }}%)
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="purchase_price">Einkaufspreis / Lieferantenanteil (€):</label>
        <input type="number" step="0.01" id="purchase_price" v-model.number="product.purchase_price" required />
      </div>
      <div class="form-group">
        <label for="selling_price">Verkaufspreis (€):</label>
        <input type="number" step="0.01" id="selling_price" v-model.number="product.selling_price" required />
      </div>
      <div class="form-group">
        <label for="product_type">Artikeltyp:</label>
        <select id="product_type" v-model="product.product_type" required>
          <option value="COMMISSION">Kommission</option>
          <option value="NEW_WARE">Neuware</option>
        </select>
      </div>
       <div class="form-group" v-if="!isNew">
        <label for="status">Status:</label>
        <select id="status" v-model="product.status" required>
          <option value="IN_STOCK">Auf Lager</option>
          <option value="SOLD">Verkauft</option>
          <option value="RETURNED">Retourniert</option>
          <option value="DONATED">Gespendet</option>
           <option value="RESERVED">Reserviert</option>
        </select>
      </div>
      <div class="form-group">
        <label for="entry_date">Eingangsdatum:</label>
        <input type="date" id="entry_date" v-model="product.entry_date" required />
      </div>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <button type="submit" :disabled="formLoading">{{ formLoading ? 'Speichern...' : 'Speichern' }}</button>
      <router-link to="/products" class="button secondary">Abbrechen</router-link>
    </form>
    <div v-if="pageLoading" class="loading">Lade Artikeldaten...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import productService from '@/services/productService';
import supplierService from '@/services/supplierService'; // To fetch suppliers for dropdown

const props = defineProps({
  id: [String, Number],
  isNew: { type: Boolean, default: false }
});

const router = useRouter();
const product = ref({
  name: '',
  sku: '',
  description: '',
  supplier_id: null,
  category_id: null,
  tax_rate_id: null,
  purchase_price: 0.00,
  selling_price: 0.00,
  product_type: 'COMMISSION',
  status: 'IN_STOCK',
  entry_date: new Date().toISOString().split('T')[0], // Default to today
});

const availableSuppliers = ref([]);
const availableCategories = ref([]);
const availableTaxRates = ref([]);

const pageLoading = ref(false); // For loading initial data (product, dropdowns)
const formLoading = ref(false); // For submit action
const errorMessage = ref('');

// Helper to format date for input type="date"
const formatDateForInput = (dateString) => {
  if (!dateString) return new Date().toISOString().split('T')[0];
  return new Date(dateString).toISOString().split('T')[0];
};

onMounted(async () => {
  pageLoading.value = true;
  try {
    // Fetch dropdown data
    const [suppliersRes, categoriesRes, taxRatesRes] = await Promise.all([
      supplierService.getSuppliers({ limit: 500 }), // Adjust limit as needed
      productService.getProductCategories({ limit: 500 }),
      productService.getTaxRates({ limit: 100 })
    ]);
    availableSuppliers.value = suppliersRes.data;
    availableCategories.value = categoriesRes.data;
    availableTaxRates.value = taxRatesRes.data;

    if (!props.isNew && props.id) {
      const response = await productService.getProduct(props.id);
      product.value = { ...response.data, entry_date: formatDateForInput(response.data.entry_date) };
    } else {
      // Set default tax rate if available
      const defaultTaxRate = availableTaxRates.value.find(t => t.is_default_rate);
      if (defaultTaxRate) product.value.tax_rate_id = defaultTaxRate.id;
      product.value.entry_date = formatDateForInput(null); // Ensure default for new
    }
  } catch (err) {
    errorMessage.value = 'Fehler beim Laden der Daten: ' + (err.response?.data?.detail || err.message);
  } finally {
    pageLoading.value = false;
  }
});

const saveProduct = async () => {
  formLoading.value = true;
  errorMessage.value = '';

  // Ensure prices are numbers
  const payload = {
      ...product.value,
      purchase_price: parseFloat(product.value.purchase_price) || 0,
      selling_price: parseFloat(product.value.selling_price) || 0,
      sku: product.value.sku || null, // Send null if empty for auto-generation
  };

  try {
    if (props.isNew) {
      await productService.createProduct(payload);
    } else {
      await productService.updateProduct(props.id, payload);
    }
    router.push('/products');
  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern des Artikels: ' + (err.response?.data?.detail || err.message);
  } finally {
    formLoading.value = false;
  }
};
</script>

<style scoped>
/* Form styles */
</style>
