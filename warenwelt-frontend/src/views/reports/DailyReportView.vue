<template>
  <div class="daily-report-view">
    <h1>Tagesabschluss (Kassensturz)</h1>

    <div class="form-group date-selector">
      <label for="report_date">Datum auswählen:</label>
      <input type="date" id="report_date" v-model="selectedDate" @change="fetchDailyReport" />
    </div>

    <div v-if="isLoading" class="loading">Lade Bericht...</div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="reportData" class="report-content">
      <h2>Bericht für {{ formatDate(reportData.report_date) }}</h2>

      <div class="summary-card">
        <h3>Gesamtübersicht</h3>
        <p><strong>Gesamtumsatz:</strong> {{ formatCurrency(reportData.overall_total_amount) }}</p>
        <p><strong>Anzahl Transaktionen:</strong> {{ reportData.overall_transaction_count }}</p>
      </div>

      <div class="payment-methods-summary">
        <h3>Umsatz nach Zahlungsart</h3>
        <table>
          <thead>
            <tr>
              <th>Zahlungsart</th>
              <th>Anzahl Transaktionen</th>
              <th>Gesamtbetrag</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pm_summary in reportData.summary_by_payment_method" :key="pm_summary.payment_method">
              <td>{{ translatePaymentMethod(pm_summary.payment_method) }}</td>
              <td>{{ pm_summary.transaction_count }}</td>
              <td>{{ formatCurrency(pm_summary.total_amount) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Hier könnten später Optionen zum Drucken des Berichts hinzukommen -->
    </div>
     <p v-if="!isLoading && !reportData && selectedDate">Keine Daten für das ausgewählte Datum gefunden oder es wurde noch kein Datum gewählt.</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import saleService from '@/services/saleService';

const selectedDate = ref(new Date().toISOString().split('T')[0]); // Default to today
const reportData = ref(null);
const isLoading = ref(false);
const error = ref('');

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('de-DE', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
};

const translatePaymentMethod = (method) => {
  const translations = {
    CASH: 'Bar',
    CARD: 'Karte',
    VOUCHER: 'Gutschein',
    MIXED: 'Gemischt'
  };
  return translations[method] || method;
};

const fetchDailyReport = async () => {
  if (!selectedDate.value) {
    reportData.value = null;
    error.value = 'Bitte wählen Sie ein Datum.';
    return;
  }
  isLoading.value = true;
  error.value = '';
  reportData.value = null;

  try {
    const response = await saleService.getDailySummary(selectedDate.value);
    reportData.value = response.data;
  } catch (err) {
    error.value = 'Fehler beim Laden des Tagesberichts: ' + (err.response?.data?.detail || err.message);
    reportData.value = null;
  } finally {
    isLoading.value = false;
  }
};

// Fetch report for default date on component mount
import { onMounted } from 'vue';
onMounted(() => {
  fetchDailyReport();
});

</script>

<style scoped>
.daily-report-view {
  max-width: 800px;
  margin: auto;
}
.date-selector {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.date-selector input[type="date"] {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.report-content {
  margin-top: 20px;
}
.summary-card {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
}
.summary-card h3 {
  margin-top: 0;
}
.payment-methods-summary table {
  margin-top: 10px;
}
/* Globale Stile für table, loading, error-message werden angenommen */
</style>
