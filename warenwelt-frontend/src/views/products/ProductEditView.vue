<template>
  <div class="product-edit-view p-p-4">
    <Card>
      <template #title>
        {{ isNewPage ? 'Neuen Artikel anlegen' : 'Artikel bearbeiten' }}
      </template>
      <template #content>
        <div v-if="pageLoading" class="text-center p-p-4">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <p>Lade Daten...</p>
        </div>
        <form @submit.prevent="saveProduct" v-else>
          <div class="p-fluid grid">
            <div class="field col-12 md:col-6">
              <label for="name">Artikelname*</label>
              <InputText id="name" v-model="product.name" required />
            </div>
            <div class="field col-12 md:col-6">
              <label for="sku">SKU (Barcode - leer für Auto-Generierung)</label>
              <InputText id="sku" v-model="product.sku" :disabled="!isNewPage && product.sku" />
            </div>
            <div class="field col-12">
              <label for="description">Beschreibung</label>
              <Textarea id="description" v-model="product.description" rows="3" />
            </div>

            <div class="field col-12 md:col-4">
              <label for="supplier_id">Lieferant*</label>
              <Dropdown id="supplier_id" v-model="product.supplier_id" :options="availableSuppliers" optionLabel="name" optionValue="id" placeholder="Lieferant wählen" required class="w-full"/>
            </div>
            <div class="field col-12 md:col-4">
              <label for="category_id">Kategorie*</label>
              <Dropdown id="category_id" v-model="product.category_id" :options="availableCategories" optionLabel="name" optionValue="id" placeholder="Kategorie wählen" required class="w-full"/>
            </div>
            <div class="field col-12 md:col-4">
              <label for="tax_rate_id">Steuersatz*</label>
              <Dropdown id="tax_rate_id" v-model="product.tax_rate_id" :options="availableTaxRates" optionLabel="label" optionValue="id" placeholder="Steuersatz wählen" required class="w-full"/>
            </div>

            <div class="field col-12 md:col-6">
              <label for="purchase_price">Einkaufspreis / Lieferantenanteil (€)*</label>
              <InputNumber id="purchase_price" v-model="product.purchase_price" mode="currency" currency="EUR" locale="de-DE" :minFractionDigits="2" :maxFractionDigits="2" required />
            </div>
            <div class="field col-12 md:col-6">
              <label for="selling_price">Verkaufspreis (€)*</label>
              <InputNumber id="selling_price" v-model="product.selling_price" mode="currency" currency="EUR" locale="de-DE" :minFractionDigits="2" :maxFractionDigits="2" required />
            </div>

            <div class="field col-12 md:col-4">
              <label for="product_type">Artikeltyp*</label>
              <Dropdown id="product_type" v-model="product.product_type" :options="productTypeOptions" optionLabel="label" optionValue="value" required class="w-full"/>
            </div>
             <div class="field col-12 md:col-4" v-if="!isNewPage">
              <label for="status">Status*</label>
              <Dropdown id="status" v-model="product.status" :options="productStatusOptions" optionLabel="label" optionValue="value" required class="w-full"/>
            </div>
            <div class="field col-12 md:col-4">
              <label for="entry_date">Eingangsdatum*</label>
              <!-- PrimeVue Calendar might be better here if time is not needed, or use InputText with type="date" -->
              <Calendar id="entry_date" v-model="product.entry_date_dt" dateFormat="dd.mm.yy" required class="w-full" :showIcon="true"/>
            </div>
            <div class="field col-12 md:col-6">
              <label for="shelf_location">Regalplatz</label>
              <InputText id="shelf_location" v-model="product.shelf_location" maxlength="100" />
            </div>
          </div>

          <!-- Image Upload Section -->
          <div class="field mt-3">
            <label for="product_image">Artikelbild</label>
            <!-- PrimeVue FileUpload for a richer experience, or simple input type="file" -->
            <FileUpload
                name="productImage"
                @select="handleImageSelectedPrime"
                :multiple="false"
                accept="image/*"
                :maxFileSize="5000000"
                chooseLabel="Bild wählen"
                :showUploadButton="false"
                :showCancelButton="false"
                :customUpload="true"
                @uploader="null"
                ref="imageUploaderRef"
            >
                <template #empty>
                    <p>Bild hierher ziehen oder klicken zum Auswählen.</p>
                </template>
            </FileUpload>

            <div v-if="imagePreviewUrl" class="image-preview mt-2">
              <img :src="imagePreviewUrl" alt="Vorschau" style="max-width: 200px; max-height: 200px; border: 1px solid var(--surface-d); border-radius: 4px;" />
            </div>
            <div v-else-if="product.image_url && !isNewPage" class="image-preview mt-2">
              <p>Aktuelles Bild:</p>
              <img :src="getFullImageUrl(product.image_url)" alt="Aktuelles Bild" style="max-width: 200px; max-height: 200px; border: 1px solid var(--surface-d); border-radius: 4px;" />
            </div>
             <small v-if="!isNewPage && product.id" class="block mt-1">Das Bild wird separat hochgeladen, nachdem die Produktdaten gespeichert wurden, falls ein neues Bild ausgewählt wurde.</small>
          </div>
          <!-- End Image Upload Section -->

          <small v-if="errorMessage" class="p-error block mt-3">{{ errorMessage }}</small>

          <div class="form-actions mt-4">
            <Button type="submit" :loading="formLoading" :disabled="imageUploading" :label="isNewPage ? 'Artikel Anlegen' : 'Änderungen Speichern'" icon="pi pi-check" />
            <Button
                v-if="!isNewPage && product.id && selectedImageFile"
                type="button"
                @click="uploadImageWrapper"
                :loading="imageUploading"
                :disabled="formLoading"
                label="Bild Hochladen"
                icon="pi pi-upload"
                class="p-button-secondary" />
            <router-link to="/products">
                <Button label="Abbrechen" class="p-button-text" icon="pi pi-times"/>
            </router-link>
          </div>
           <small v-if="imageUploadSuccessMessage" class="p-success block mt-2">{{ imageUploadSuccessMessage }}</small>
           <small v-if="imageUploadErrorMessage" class="p-error block mt-2">{{ imageUploadErrorMessage }}</small>
        </form>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import productService from '@/services/productService';
import supplierService from '@/services/supplierService';
import { useToast } from 'primevue/usetoast';
import Calendar from 'primevue/calendar'; // Import Calendar
import FileUpload from 'primevue/fileupload'; // Import FileUpload

// Globally registered: Card, InputText, Textarea, Dropdown, InputNumber, Checkbox, Button

const props = defineProps({
  id: [String, Number],
});

const router = useRouter();
const route = useRoute();
const toast = useToast();
const isNewPage = computed(() => !props.id); // Simpler check based on presence of ID prop

const product = ref({
  name: '',
  sku: '',
  description: '',
  supplier_id: null,
  category_id: null,
  tax_rate_id: null,
  purchase_price: null, // Use null for InputNumber, it handles formatting
  selling_price: null,
  product_type: 'COMMISSION',
  status: 'IN_STOCK',
  entry_date: new Date().toISOString().split('T')[0], // String for backend YYYY-MM-DD
  entry_date_dt: new Date(), // Date object for PrimeVue Calendar
  shelf_location: '',
  image_url: null,
});

const productTypeOptions = ref([
    {label: 'Kommission', value: 'COMMISSION'},
    {label: 'Neuware', value: 'NEW_WARE'}
]);
const productStatusOptions = ref([
    {label: 'Auf Lager', value: 'IN_STOCK'},
    {label: 'Verkauft', value: 'SOLD'},
    {label: 'Retourniert', value: 'RETURNED'},
    {label: 'Gespendet', value: 'DONATED'},
    {label: 'Reserviert', value: 'RESERVED'}
]);

const availableSuppliers = ref([]);
const availableCategories = ref([]);
const availableTaxRates = ref([]);

const pageLoading = ref(false);
const formLoading = ref(false);
const errorMessage = ref('');

const selectedImageFile = ref(null); // Holds the File object
const imagePreviewUrl = ref(null);
const imageUploading = ref(false);
const imageUploadErrorMessage = ref('');
const imageUploadSuccessMessage = ref('');
const imageUploaderRef = ref(null); // Ref for FileUpload component

// Convert date string from API to Date object for Calendar and back
watch(() => product.value.entry_date_dt, (newDate) => {
  if (newDate instanceof Date) {
    product.value.entry_date = newDate.toISOString().split('T')[0];
  }
});

const formatDateForInput = (dateString) => { // For Calendar initial value
  if (!dateString) return new Date();
  return new Date(dateString + 'T00:00:00'); // Ensure it's parsed as local date
};


onMounted(async () => {
  pageLoading.value = true;
  try {
    const [suppliersRes, categoriesRes, taxRatesRes] = await Promise.all([
      supplierService.getSuppliers({ limit: 1000 }),
      productService.getProductCategories({ limit: 1000 }),
      productService.getTaxRates({ limit: 100 })
    ]);
    availableSuppliers.value = suppliersRes.data.map(s => ({ ...s, name: s.company_name || `${s.first_name || ''} ${s.last_name || ''}`.trim()}));
    availableCategories.value = categoriesRes.data;
    availableTaxRates.value = taxRatesRes.data.map(t => ({ ...t, label: `${t.name} (${t.rate_percent}%)`}));

    if (!isNewPage.value) {
      const response = await productService.getProduct(props.id);
      product.value = {
        ...response.data,
        entry_date_dt: formatDateForInput(response.data.entry_date),
        // InputNumber expects numbers, not strings from Decimal
        purchase_price: response.data.purchase_price !== null ? parseFloat(response.data.purchase_price) : null,
        selling_price: response.data.selling_price !== null ? parseFloat(response.data.selling_price) : null,
      };
    } else {
      const defaultTaxRate = availableTaxRates.value.find(t => t.is_default_rate);
      if (defaultTaxRate) product.value.tax_rate_id = defaultTaxRate.id;
      product.value.entry_date_dt = formatDateForInput(null);
    }
  } catch (err) {
    errorMessage.value = 'Fehler beim Laden der Grunddaten: ' + (err.response?.data?.detail || err.message);
    toast.add({severity:'error', summary: 'Ladefehler', detail: errorMessage.value, life: 5000});
  } finally {
    pageLoading.value = false;
  }
});

const getFullImageUrl = (relativePath) => {
  if (!relativePath) return null;
  const backendRootUrl = (import.meta.env.VITE_API_BASE_URL || '').replace('/api/v1', '');
  return `${backendRootUrl}/static/${relativePath}`;
};

const handleImageSelectedPrime = (event) => {
    // For PrimeVue FileUpload with customUpload, event.files contains the selected file(s)
    const file = event.files[0];
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
  imageUploadErrorMessage.value = '';
  imageUploadSuccessMessage.value = '';

  const payload = {
      ...product.value,
      sku: product.value.sku || null,
      // entry_date is already correctly formatted string from watcher
  };
  // Remove the temporary Date object if backend doesn't expect it
  delete payload.entry_date_dt;

  try {
    let savedProductData;
    if (isNewPage.value) {
      savedProductData = await productService.createProduct(payload);
      product.value = {
        ...savedProductData.data,
        entry_date_dt: formatDateForInput(savedProductData.data.entry_date),
        purchase_price: parseFloat(savedProductData.data.purchase_price), // ensure number
        selling_price: parseFloat(savedProductData.data.selling_price), // ensure number
      };
      toast.add({severity:'success', summary: 'Erstellt', detail: 'Artikel erfolgreich angelegt.', life: 3000});

      // If an image was selected, upload it now that we have an ID
      if (selectedImageFile.value && product.value.id) {
        await uploadImage(product.value.id);
        // After image upload, redirect or stay, depending on UX preference
        if (!imageUploadErrorMessage.value) { // if image upload was successful
            router.push({ name: 'ProductEdit', params: { id: product.value.id } }); // Go to edit page of new product
        }
      } else {
         router.push('/products');
      }
    } else { // Updating existing product
      savedProductData = await productService.updateProduct(props.id, payload);
      product.value = {
        ...savedProductData.data,
        entry_date_dt: formatDateForInput(savedProductData.data.entry_date),
        purchase_price: parseFloat(savedProductData.data.purchase_price),
        selling_price: parseFloat(savedProductData.data.selling_price),
      };
      toast.add({severity:'success', summary: 'Aktualisiert', detail: 'Produktdaten erfolgreich gespeichert.', life: 3000});
      // If an image was selected while editing, it needs to be uploaded via the separate button
      // or auto-triggered if that's the desired UX. Here, we assume separate button.
      if (selectedImageFile.value) {
          // User needs to click "Bild Hochladen"
          imageUploadSuccessMessage.value = "Neues Bild ausgewählt. Bitte separat hochladen.";
      } else {
          // router.push('/products'); // Optionally redirect
      }
    }
  } catch (err) {
    errorMessage.value = 'Fehler beim Speichern der Produktdaten: ' + (err.response?.data?.detail || err.message);
    toast.add({severity:'error', summary: 'Speicherfehler', detail: errorMessage.value, life: 5000});
  } finally {
    formLoading.value = false;
  }
};

// Wrapper for the button, as product.id might not be available if it's a new product
const uploadImageWrapper = async () => {
    if (product.value && product.value.id) {
        await uploadImage(product.value.id);
    } else {
        imageUploadErrorMessage.value = "Produkt muss zuerst gespeichert werden, um ein Bild hochzuladen.";
        toast.add({severity:'warn', summary: 'Hinweis', detail: imageUploadErrorMessage.value, life: 4000});
    }
};

const uploadImage = async (productIdToUse) => {
  if (!selectedImageFile.value) {
    imageUploadErrorMessage.value = "Kein Bild zum Hochladen ausgewählt.";
    toast.add({severity:'warn', summary: 'Kein Bild', detail: imageUploadErrorMessage.value, life: 3000});
    return;
  }
  imageUploading.value = true;
  imageUploadErrorMessage.value = '';
  imageUploadSuccessMessage.value = '';

  try {
    const response = await productService.uploadProductImage(productIdToUse, selectedImageFile.value);
    product.value.image_url = response.data.image_url; // Update local product state
    toast.add({severity:'success', summary: 'Upload Erfolg', detail: 'Bild erfolgreich hochgeladen!', life: 3000});
    selectedImageFile.value = null;
    imagePreviewUrl.value = null;
    if(imageUploaderRef.value) { // Clear PrimeVue FileUpload component
        imageUploaderRef.value.clear();
    }
  } catch (err) {
    imageUploadErrorMessage.value = 'Fehler beim Hochladen des Bildes: ' + (err.response?.data?.detail || err.message);
    toast.add({severity:'error', summary: 'Upload Fehler', detail: imageUploadErrorMessage.value, life: 5000});
  } finally {
    imageUploading.value = false;
  }
};

</script>

<style scoped>
/* Using PrimeFlex for padding, grid, and spacing */
.form-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: 1.5rem; /* Increased margin */
}
.mt-1 { margin-top: 0.25rem; } /* PrimeFlex like utility */
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 1rem; } /* PrimeFlex like utility */
.block { display: block; } /* PrimeFlex like utility */

/* Ensure labels and inputs are nicely aligned */
.field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}
.p-inputnumber, .p-calendar, .p-dropdown {
    width: 100%; /* Make dropdowns and other inputs full width within their grid cell */
}

/* Style for FileUpload component to look more integrated if needed */
:deep(.p-fileupload-buttonbar) {
    /* padding: 0.5rem; */
}
:deep(.p-button.p-fileupload-choose) {
    /* margin-right: 0.5rem; */
}
</style>
