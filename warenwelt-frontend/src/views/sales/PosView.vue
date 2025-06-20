<template>
  <div class="pos-view p-p-4">
    <Card>
      <template #title>
        <div class="text-xl font-semibold">Kasse</div>
      </template>
      <template #content>
        <div class="p-fluid grid">
          <div class="field col-12 md:col-8">
            <label for="sku_input">SKU eingeben oder scannen</label>
            <span class="p-input-icon-right">
                <i v-if="isAddingProduct" class="pi pi-spin pi-spinner" />
                <InputText
                    id="sku_input"
                    type="text"
                    v-model="skuInput"
                    placeholder="SKU"
                    @keyup.enter="addProductBySku"
                    ref="skuInputRef"
                />
            </span>
          </div>
          <div class="field col-12 md:col-4 flex align-items-end">
            <Button
                label="Artikel hinzufügen"
                icon="pi pi-plus"
                @click="addProductBySku"
                :disabled="!skuInput.trim() || isAddingProduct"
                class="w-full"
            />
          </div>
        </div>

        <Message v-if="scanError" severity="error" :closable="true" @close="scanError=''">{{ scanError }}</Message>

        <div class="cart-section mt-4">
          <h3 class="text-lg font-semibold mb-2">Warenkorb</h3>
          <DataTable :value="cartItems" responsiveLayout="scroll" :rows="5" :paginator="cartItems.length > 5">
            <template #empty>Warenkorb ist leer.</template>
            <Column field="sku" header="SKU"></Column>
            <Column field="name" header="Name"></Column>
            <Column field="selling_price" header="Preis" style="width:120px; text-align:right;">
              <template #body="{data}">{{ formatCurrency(data.selling_price) }}</template>
            </Column>
            <Column header="Aktion" style="width:100px; text-align:center;">
              <template #body="slotProps">
                <Button icon="pi pi-trash" class="p-button-rounded p-button-danger p-button-text" @click="removeFromCart(slotProps.index)" />
              </template>
            </Column>
          </DataTable>

          <div v-if="cartItems.length > 0" class="cart-summary text-right mt-3 p-p-3 surface-ground border-round">
            <div class="text-xl font-bold">Gesamt: {{ formatCurrency(totalAmount) }}</div>
          </div>
        </div>

        <div class="payment-section mt-4" v-if="cartItems.length > 0">
          <div class="p-fluid grid align-items-center">
            <div class="field col-12 md:col-6">
              <label for="payment_method">Zahlungsmethode</label>
              <Dropdown
                id="payment_method"
                v-model="paymentMethod"
                :options="paymentMethodOptions"
                optionLabel="label"
                optionValue="value"
                class="w-full"
              />
            </div>
            <div class="field col-12 md:col-6 flex align-items-end">
              <Button
                label="Verkauf abschließen"
                icon="pi pi-check-circle"
                @click="processSale"
                :loading="isLoadingSale"
                :disabled="cartItems.length === 0"
                class="w-full p-button-lg"
              />
            </div>
          </div>
        </div>
        <!-- Success/Error messages for sale are handled by Toast -->
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue';
import productService from '@/services/productService';
import saleService from '@/services/saleService';

import { ref, computed, nextTick } from 'vue'; // Added nextTick

const skuInput = ref('');
const skuInputRef = ref(null); // Template ref for the SKU input field
const cartItems = ref([]); // Stores full product objects fetched from backend
const scanError = ref(''); // For inline error messages related to SKU input
const paymentMethod = ref('CASH');
const isLoadingSale = ref(false); // For the "Verkauf abschließen" button
const isAddingProduct = ref(false); // For the "Artikel hinzufügen" button and spinner

const paymentMethodOptions = ref([
    {label: 'Bar', value: 'CASH'},
    {label: 'Karte', value: 'CARD'},
    // {label: 'Gutschein', value: 'VOUCHER'} // If enabled later
]);

import { useToast } from 'primevue/usetoast';
const toast = useToast();
// onMounted is already imported by previous change

onMounted(() => {
  skuInputRef.value?.focus();
});

const formatCurrency = (value) => {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const addProductBySku = async () => {
  if (!skuInput.value.trim()) return;
  isAddingProduct.value = true;
  scanError.value = '';
  // saleSuccessMessage.value = ''; // Not used anymore, relying on Toast
  // saleErrorMessage.value = ''; // Not used anymore, scanError is for this part
  try {
    const response = await productService.getProductBySku(skuInput.value.trim());
    const product = response.data;

    if (product.status !== 'IN_STOCK') {
        scanError.value = `Artikel ${product.sku} ist nicht verfügbar (Status: ${product.status}).`;
        return;
    }
    // Check if product already in cart (for unique items)
    if (cartItems.value.find(item => item.id === product.id)) {
        scanError.value = `Artikel ${product.sku} ist bereits im Warenkorb.`;
        return;
    }

    cartItems.value.push(product);
    skuInput.value = ''; // Clear input after adding
    await nextTick(); // Wait for DOM to update (input value cleared)
    skuInputRef.value?.focus(); // Focus the input field again
  } catch (err) {
    scanError.value = `Fehler: Artikel mit SKU '${skuInput.value.trim()}' nicht gefunden oder nicht verfügbar.`;
    // console.error(err);
    await nextTick();
    skuInputRef.value?.select(); // Select the text in case of error for easy correction
  } finally {
    isAddingProduct.value = false;
  }
};

const removeFromCart = (index) => {
  cartItems.value.splice(index, 1);
};

const totalAmount = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + parseFloat(item.selling_price), 0);
});

const processSale = async () => {
  if (cartItems.value.length === 0) {
    toast.add({ severity: 'warn', summary: 'Warenkorb leer', detail: 'Bitte fügen Sie zuerst Artikel zum Warenkorb hinzu.', life: 3000 });
    return;
  }
  isLoadingSale.value = true;
  // saleSuccessMessage.value = ''; // Handled by Toast
  // saleErrorMessage.value = ''; // Handled by Toast

  const salePayload = {
    payment_method: paymentMethod.value,
    items: cartItems.value.map(p => ({ product_id: p.id, quantity: 1 /* Assuming 1 for MVP */ }))
  };

  try {
    const response = await saleService.createSale(salePayload);
    toast.add({
        severity: 'success',
        summary: 'Verkauf erfolgreich',
        detail: `Transaktion ${response.data.transaction_number} über ${formatCurrency(response.data.total_amount)} abgeschlossen.`,
        life: 5000
    });
    cartItems.value = []; // Clear cart
    skuInput.value = '';
    scanError.value = '';
    await nextTick();
    skuInputRef.value?.focus(); // Focus SKU input for next sale
  } catch (err) {
    const detail = err.response?.data?.detail || 'Unbekannter Fehler beim Abschluss des Verkaufs.';
    toast.add({ severity: 'error', summary: 'Verkaufsfehler', detail: detail, life: 7000 });
  } finally {
    isLoadingSale.value = false;
  }
};
</script>

<style scoped>
/* Using PrimeFlex for padding (p-p-4) and layout (grid, flex, etc.) */
/* Specific styling for POS view can be added here */

.pos-view .field label { /* Example of more specific label styling if needed */
    font-weight: 500; /* Slightly less bold than default form labels if desired */
}

.cart-section .p-datatable .p-datatable-thead > tr > th {
    background-color: var(--surface-b); /* Light background for cart header */
}

.cart-summary {
    /* background-color: var(--surface-section); */ /* Already surface-ground */
}

.p-button-lg { /* PrimeVue utility class for larger buttons */
    /* font-size: 1.1rem; */ /* Custom size if needed */
}

/* Styles for the scan error Message component are handled by PrimeVue themes */
</style>
