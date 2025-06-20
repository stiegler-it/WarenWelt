<template>
  <div class="payout-view">
    <h1>Auszahlungen an Lieferanten</h1>

    <div class="supplier-selection">
      <label for="selected_supplier">Lieferant auswählen:</label>
      <select id="selected_supplier" v-model="selectedSupplierId" @change="fetchPayoutSummary">
        <option :value="null" disabled>-- Bitte Lieferant wählen --</option>
        <option v-for="s in availableSuppliers" :key="s.id" :value="s.id">
          {{ s.supplier_number }} - {{ s.company_name || s.first_name + ' ' + s.last_name }}
        </option>
      </select>
    </div>

    <div v-if="isLoadingSummary" class="loading">Lade Auszahlungsübersicht...</div>
    <div v-if="summaryError" class="error-message">{{ summaryError }}</div>

    <div v-if="payoutSummary && selectedSupplierId" class="payout-summary">
      <h2>Übersicht für {{ payoutSummary.supplier_name }}</h2>
      <p><strong>Gesamtauszahlung fällig: {{ formatCurrency(payoutSummary.total_due) }}</strong></p>
      <p>Anzahl abrechenbarer Artikel: {{ payoutSummary.eligible_items_count }}</p>

      <div v-if="payoutSummary.items_preview.length > 0">
        <h3>Vorschau einiger abrechenbarer Artikel:</h3>
        <ul>
          <li v-for="item in payoutSummary.items_preview" :key="item.product_id + '_' + item.sale_id">
            {{ item.product_name }} (SKU: {{ item.product_sku }}) - verkauft am {{ formatDate(item.sale_date) }} - Provision: {{ formatCurrency(item.commission_amount) }}
          </li>
        </ul>
      </div>
      <p v-else-if="payoutSummary.eligible_items_count === 0">Keine Artikel zur Auszahlung fällig.</p>

      <button
        @click="processPayout"
        :disabled="isLoadingPayout || payoutSummary.total_due <= 0"
        v-if="payoutSummary.eligible_items_count > 0">
        {{ isLoadingPayout ? 'Verarbeite...' : `Auszahlung von ${formatCurrency(payoutSummary.total_due)} erstellen` }}
      </button>
    </div>

    <p v-if="payoutSuccessMessage" class="success-message">{{ payoutSuccessMessage }}</p>
    <p v-if="payoutErrorMessage" class="error-message">{{ payoutErrorMessage }}</p>

    <hr style="margin: 20px 0;"/>
    <h2>Vergangene Auszahlungen</h2>
     <div v-if="isLoadingPastPayouts" class="loading">Lade vergangene Auszahlungen...</div>
    <table v-if="pastPayouts.length > 0">
        <thead>
            <tr>
                <th>Auszahlungsnr.</th>
                <th>Lieferant</th>
                <th>Datum</th>
                <th>Betrag</th>
                <th>Aktion</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="payout in pastPayouts" :key="payout.id">
                <td>{{ payout.payout_number }}</td>
                <td>{{ payout.supplier.supplier_number }} - {{ payout.supplier.company_name || payout.supplier.first_name }}</td>
                <td>{{ formatDate(payout.payout_date) }}</td>
                <td>{{ formatCurrency(payout.total_amount) }}</td>
                <td><button @click="viewPayoutDetails(payout.id)" class="button small secondary">Details</button></td>
            </tr>
        </tbody>
    </table>
    <p v-if="!isLoadingPastPayouts && pastPayouts.length === 0">Keine vergangenen Auszahlungen gefunden.</p>
    <!-- TODO: Details Modal for past payouts -->

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import supplierService from '@/services/supplierService';
import payoutService from '@/services/payoutService';

const availableSuppliers = ref([]);
const selectedSupplierId = ref(null);

const payoutSummary = ref(null);
const isLoadingSummary = ref(false);
const summaryError = ref('');

const isLoadingPayout = ref(false);
const payoutSuccessMessage = ref('');
const payoutErrorMessage = ref('');

const pastPayouts = ref([]);
const isLoadingPastPayouts = ref(false);


const formatCurrency = (value) => {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};
const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('de-DE');
};

onMounted(async () => {
  try {
    const response = await supplierService.getSuppliers({ limit: 500, is_internal: false }); // Exclude internal for payouts typically
    availableSuppliers.value = response.data;
    fetchPastPayouts();
  } catch (err) {
    summaryError.value = 'Fehler beim Laden der Lieferanten.'; // Use a general error ref or specific one
  }
});

const fetchPayoutSummary = async () => {
  if (!selectedSupplierId.value) {
    payoutSummary.value = null;
    return;
  }
  isLoadingSummary.value = true;
  summaryError.value = '';
  payoutSuccessMessage.value = ''; // Clear previous messages
  payoutErrorMessage.value = '';
  try {
    const response = await payoutService.getPayoutSummary(selectedSupplierId.value);
    payoutSummary.value = response.data;
  } catch (err) {
    summaryError.value = 'Fehler beim Laden der Auszahlungsübersicht: ' + (err.response?.data?.detail || err.message);
    payoutSummary.value = null;
  } finally {
    isLoadingSummary.value = false;
  }
};

const processPayout = async () => {
  if (!selectedSupplierId.value || !payoutSummary.value || payoutSummary.value.total_due <= 0) {
    payoutErrorMessage.value = "Keine gültige Auszahlung möglich.";
    return;
  }
  isLoadingPayout.value = true;
  payoutSuccessMessage.value = '';
  payoutErrorMessage.value = '';
  try {
    const payload = { supplier_id: selectedSupplierId.value }; // Payout date is optional in schema
    const response = await payoutService.createPayout(payload);
    payoutSuccessMessage.value = `Auszahlung ${response.data.payout_number} über ${formatCurrency(response.data.total_amount)} erfolgreich erstellt.`;
    // Refresh summary and past payouts
    fetchPayoutSummary();
    fetchPastPayouts();
  } catch (err) {
    payoutErrorMessage.value = 'Fehler beim Erstellen der Auszahlung: ' + (err.response?.data?.detail || err.message);
  } finally {
    isLoadingPayout.value = false;
  }
};

const fetchPastPayouts = async () => {
    isLoadingPastPayouts.value = true;
    try {
        const response = await payoutService.getPayouts({limit: 20}); // Get recent 20
        pastPayouts.value = response.data;
    } catch (err) {
        // Handle error fetching past payouts
        console.error("Error fetching past payouts:", err);
    } finally {
        isLoadingPastPayouts.value = false;
    }
};

const viewPayoutDetails = (payoutId) => {
    alert(`Details für Payout ID ${payoutId} anzeigen (Implementierung ausstehend)`);
    // router.push({ name: 'PayoutDetails', params: { id: payoutId } }); // If a detail route exists
};

// Watch for changes in selectedSupplierId to auto-fetch summary
// watch(selectedSupplierId, (newVal, oldVal) => {
//   if (newVal) {
//     fetchPayoutSummary();
//   } else {
//     payoutSummary.value = null;
//   }
// });

</script>

<style scoped>
.supplier-selection {
  margin-bottom: 20px;
}
.payout-summary {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #eee;
  background-color: #f9f9f9;
}
.payout-summary ul {
    list-style-type: none;
    padding-left: 0;
}
.payout-summary li {
    padding: 5px 0;
    font-size: 0.9em;
}
.success-message {
  color: green;
  margin-top: 1rem;
}
/* error-message, button, table styles are somewhat global or defined here/App.vue */
</style>
