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

      <div class="form-group">
        <label for="shelf_location">Regalplatz:</label>
        <input type="text" id="shelf_location" v-model="product.shelf_location" maxlength="100" />
      </div>

      <!-- Image Upload Section -->
      <div class="form-group">
        <label for="product_image">Artikelbild:</label>
        <input type="file" id="product_image" @change="handleImageSelected" accept="image/png, image/jpeg, image/gif, image/webp" />
        <div v-if="imagePreviewUrl" class="image-preview mt-2">
          <img :src="imagePreviewUrl" alt="Vorschau" style="max-width: 200px; max-height: 200px; border: 1px solid #ccc;" />
        </div>
        <div v-if="product.image_url && !imagePreviewUrl && !isNew" class="image-preview mt-2">
          <p>Aktuelles Bild:</p>
          <img :src="getFullImageUrl(product.image_url)" alt="Aktuelles Bild" style="max-width: 200px; max-height: 200px; border: 1px solid #ccc;" />
        </div>
         <small v-if="!isNew && product.id">Das Bild kann nach dem Speichern der Produktdaten separat hochgeladen/geändert werden.</small>
      </div>
      <!-- End Image Upload Section -->

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <div class="form-actions">
        <button type="submit" :disabled="formLoading || imageUploading">{{ (formLoading || imageUploading) ? 'Speichern...' : 'Produktdaten Speichern' }}</button>
        <button
            v-if="!isNew && product.id && selectedImageFile"
            type="button"
            @click="uploadImage"
            :disabled="imageUploading || formLoading"
            class="button secondary">
            {{ imageUploading ? 'Lädt Bild hoch...' : 'Bild jetzt hochladen' }}
        </button>
        <router-link to="/products" class="button secondary">Abbrechen</router-link>
      </div>
    </form>
    <div v-if="pageLoading" class="loading">Lade Artikeldaten...</div>
     <p v-if="imageUploadSuccessMessage" class="success-message">{{ imageUploadSuccessMessage }}</p>
     <p v-if="imageUploadErrorMessage" class="error-message">{{ imageUploadErrorMessage }}</p>
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
  shelf_location: '', // Initialize shelf_location
});

const availableSuppliers = ref([]);
const availableCategories = ref([]);
const availableTaxRates = ref([]);

const pageLoading = ref(false); // For loading initial data (product, dropdowns)
const formLoading = ref(false); // For submit action for product data
const errorMessage = ref(''); // For product data form

const selectedImageFile = ref(null);
const imagePreviewUrl = ref(null);
const imageUploading = ref(false);
const imageUploadErrorMessage = ref('');
const imageUploadSuccessMessage = ref('');


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

const getFullImageUrl = (relativePath) => {
  if (!relativePath) return null;
  // Assuming VITE_API_BASE_URL is set up to point to the root of the backend API (e.g., http://localhost:8000/api/v1)
  // and static files are served from /static path relative to the backend root.
  // So, if VITE_API_BASE_URL is http://localhost:8000/api/v1, we need http://localhost:8000/static/...
  const backendRootUrl = (import.meta.env.VITE_API_BASE_URL || '').replace('/api/v1', '');
  return `${backendRootUrl}/static/${relativePath}`;
};

const handleImageSelected = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedImageFile.value = file;
    imagePreviewUrl.value = URL.createObjectURL(file);
    imageUploadErrorMessage.value = '';
    imageUploadSuccessMessage.value = '';
  } else {
    selectedImageFile.value = null;
    imagePreviewUrl.value = null;
  }
};

const saveProduct = async () => {
  formLoading.value = true;
  errorMessage.value = '';
  imageUploadErrorMessage.value = ''; // Clear image errors on main save
  imageUploadSuccessMessage.value = '';

  // Ensure prices are numbers
  const payload = {
      ...product.value,
      purchase_price: parseFloat(product.value.purchase_price) || 0,
      selling_price: parseFloat(product.value.selling_price) || 0,
      sku: product.value.sku || null, // Send null if empty for auto-generation
  };

  try {
    let savedProductData;
    if (props.isNew) {
      // If creating a new product and an image is selected,
      // it's better to first create the product, get ID, then upload image.
      // For simplicity in MVP Phase 1, we'll require saving product first, then uploading image.
      // Or, if we change backend to accept image_url directly (e.g. from external source), it could be included here.
      // For now, image_url is not part of create payload directly for file uploads.
      savedProductData = await productService.createProduct(payload);
      // Update the product ref with the newly created product's data, including ID
      // This is important so the user can then upload an image if they selected one.
      product.value = { ...savedProductData.data, entry_date: formatDateForInput(savedProductData.data.entry_date) };
      // Manually set isNew to false and id to allow image upload button to appear
      // This is a bit of a hack for component state; ideally router would navigate to edit view.
      // For now, we update component state.
      // props.isNew = false; // Props are read-only. This won't work.
      // Instead, we can use a local reactive variable if needed or rely on user navigating back to edit.
      // Let's assume for now: after creating, user can go back to edit list and select product to upload image.
      // OR, we trigger upload if selectedImageFile exists and now we have an ID.
      if (selectedImageFile.value && savedProductData.data.id) {
        await uploadImage(savedProductData.data.id); // Pass the new ID
      } else {
         router.push('/products'); // Go to list if no image was pending
      }
      // If image was uploaded successfully by uploadImage, it will handle success message.
      // If not, we might need a general success message here.
      if (!selectedImageFile.value) { // If no image was selected to be uploaded with the new product
        // No explicit success message for product data save, router push is enough.
      }


    } else { // Updating existing product
      savedProductData = await productService.updateProduct(props.id, payload);
      product.value = { ...savedProductData.data, entry_date: formatDateForInput(savedProductData.data.entry_date) };
      // If an image was selected while editing, upload it now.
      if (selectedImageFile.value) {
        await uploadImage(props.id);
      } else {
        // No explicit success message for product data save, router push is enough if no image change.
        // If we want to stay on page:
        // errorMessage.value = ''; // Clear any previous errors
        // imageUploadSuccessMessage.value = "Produktdaten erfolgreich gespeichert."; // Generic success
      }
       // Only redirect if no image was pending or if image upload also succeeded without error
      if (!selectedImageFile.value || (selectedImageFile.value && !imageUploadErrorMessage.value)) {
         // Potentially delay this push if an image upload is about to happen and might show its own message
         // For now, if no image selected, or if image upload succeeded, go to products
         if (!selectedImageFile.value) router.push('/products');
      }
    }

  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern der Produktdaten: ' + (err.response?.data?.detail || err.message);
  } finally {
    formLoading.value = false;
  }
};

const uploadImage = async (productIdToUse) => {
  if (!selectedImageFile.value || !productIdToUse) {
    imageUploadErrorMessage.value = "Kein Bild ausgewählt oder keine Produkt-ID vorhanden.";
    return;
  }
  imageUploading.value = true;
  imageUploadErrorMessage.value = '';
  imageUploadSuccessMessage.value = '';

  try {
    const response = await productService.uploadProductImage(productIdToUse, selectedImageFile.value);
    // Update the local product's image_url with the one from the response
    if (product.value && product.value.id === productIdToUse) {
        product.value.image_url = response.data.image_url;
    }
    imageUploadSuccessMessage.value = 'Bild erfolgreich hochgeladen!';
    selectedImageFile.value = null; // Clear selection
    imagePreviewUrl.value = null; // Clear preview
    // Optionally, redirect or refresh data
    // router.push('/products'); // Or stay on page
  } catch (err) {
    imageUploadErrorMessage.value = 'Fehler beim Hochladen des Bildes: ' + (err.response?.data?.detail || err.message);
  } finally {
    imageUploading.value = false;
  }
};

</script>

<style scoped>
/* Form styles */
.form-actions {
  display: flex;
  gap: 10px; /* Space between buttons */
  align-items: center;
  margin-top: 1rem;
}
.mt-2 { margin-top: 0.5rem; }
</style>
