<template>
  <div class="pos-view">
    <h1>Kasse</h1>
    <div class="product-input">
      <input
        type="text"
        v-model="skuInput"
        placeholder="SKU eingeben oder scannen"
        @keyup.enter="addProductBySku"
        ref="skuInputRef" />
      <button @click="addProductBySku" :disabled="!skuInput.trim()">Artikel hinzufügen</button>
    </div>

    <div v-if="scanError" class="error-message">{{ scanError }}</div>

    <div class="cart" v-if="cartItems.length > 0">
      <h2>Warenkorb</h2>
      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Preis</th>
            <th>Aktion</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in cartItems" :key="item.id">
            <td>{{ item.sku }}</td>
            <td>{{ item.name }}</td>
            <td>{{ formatCurrency(item.selling_price) }}</td>
            <td><button @click="removeFromCart(index)" class="button danger small">Entfernen</button></td>
          </tr>
        </tbody>
      </table>
      <div class="cart-summary">
        <h3>Gesamt: {{ formatCurrency(totalAmount) }}</h3>
      </div>
    </div>
    <p v-else>Warenkorb ist leer.</p>

    <div class="payment-section" v-if="cartItems.length > 0">
      <label for="payment_method">Zahlungsmethode:</label>
      <select id="payment_method" v-model="paymentMethod">
        <option value="CASH">Bar</option>
        <option value="CARD">Karte</option>
        <!-- <option value="VOUCHER">Gutschein</option> -->
      </select>
      <button @click="processSale" :disabled="isLoadingSale || cartItems.length === 0">
        {{ isLoadingSale ? 'Verarbeite...' : 'Verkauf abschließen' }}
      </button>
    </div>
     <p v-if="saleSuccessMessage" class="success-message">{{ saleSuccessMessage }}</p>
     <p v-if="saleErrorMessage" class="error-message">{{ saleErrorMessage }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import productService from '@/services/productService';
import saleService from '@/services/saleService';

import { ref, computed, nextTick } from 'vue'; // Added nextTick

const skuInput = ref('');
const skuInputRef = ref(null); // Template ref for the SKU input field
const cartItems = ref([]); // Stores full product objects fetched from backend
const scanError = ref('');
const paymentMethod = ref('CASH'); // Default payment method
const isLoadingSale = ref(false);
const saleSuccessMessage = ref('');
const saleErrorMessage = ref('');

import { onMounted } from 'vue'; // Ensure onMounted is imported

onMounted(() => {
  skuInputRef.value?.focus();
});

const formatCurrency = (value) => {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const addProductBySku = async () => {
  if (!skuInput.value.trim()) return;
  scanError.value = '';
  saleSuccessMessage.value = '';
  saleErrorMessage.value = '';
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
    saleErrorMessage.value = "Warenkorb ist leer.";
    return;
  }
  isLoadingSale.value = true;
  saleSuccessMessage.value = '';
  saleErrorMessage.value = '';

  const salePayload = {
    payment_method: paymentMethod.value,
    items: cartItems.value.map(p => ({ product_id: p.id, quantity: 1 /* Assuming 1 for MVP */ }))
  };

  try {
    const response = await saleService.createSale(salePayload);
    saleSuccessMessage.value = `Verkauf ${response.data.transaction_number} erfolgreich abgeschlossen! Gesamtsumme: ${formatCurrency(response.data.total_amount)}.`;
    cartItems.value = []; // Clear cart
    skuInput.value = '';
    scanError.value = '';
  } catch (err) {
    saleErrorMessage.value = 'Fehler beim Abschluss des Verkaufs: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoadingSale.value = false;
  }
};
</script>

<style scoped>
.pos-view {
  max-width: 800px;
  margin: auto;
}
.product-input {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.product-input input {
  flex-grow: 1;
}
.cart, .payment-section {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 4px;
  background-color: #f9f9f9;
}
.cart-summary {
  text-align: right;
  margin-top: 10px;
  font-size: 1.2em;
}
.payment-section {
  display: flex;
  align-items: center;
  gap: 15px;
}
.success-message {
  color: green;
  margin-top: 1rem;
}
/* error-message, button, table styles are somewhat global or defined here/App.vue */
.button.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}
</style>
