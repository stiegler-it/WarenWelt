<template>
  <div class="daily-report-view p-p-4">
    <Card>
      <template #title>
        Tagesabschluss (Kassensturz)
      </template>
      <template #content>
        <div class="p-fluid grid">
          <div class="field col-12 md:col-4">
            <label for="report_date">Datum auswählen</label>
            <Calendar
              id="report_date"
              v-model="selectedDateDt"
              @date-select="handleDateSelect"
              dateFormat="dd.mm.yy"
              :showIcon="true"
              class="w-full"
            />
          </div>
           <div class="field col-12 md:col-4 flex align-items-end">
             <Button label="Bericht laden" icon="pi pi-search" @click="fetchDailyReport" :loading="isLoading" />
           </div>
        </div>

        <div v-if="isLoading && !reportData" class="text-center p-p-4">
            <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
            <p>Lade Bericht...</p>
        </div>
        <Message v-if="error" severity="error" :closable="true" @close="error=''">{{ error }}</Message>

        <div v-if="reportData" class="report-content mt-4">
          <h2 class="text-xl font-semibold mb-3">Bericht für {{ formatDateForDisplay(reportData.report_date) }}</h2>

          <Panel header="Gesamtübersicht" toggleable class="mb-3">
            <div class="grid">
                <div class="col-6 md:col-3"><strong>Gesamtumsatz:</strong></div>
                <div class="col-6 md:col-9">{{ formatCurrency(reportData.overall_total_amount) }}</div>
                <div class="col-6 md:col-3"><strong>Transaktionen:</strong></div>
                <div class="col-6 md:col-9">{{ reportData.overall_transaction_count }}</div>
            </div>
          </Panel>

          <Panel header="Umsatz nach Zahlungsart" toggleable>
            <DataTable :value="reportData.summary_by_payment_method" responsiveLayout="scroll">
              <Column field="payment_method" header="Zahlungsart">
                <template #body="{data}">{{ translatePaymentMethod(data.payment_method) }}</template>
              </Column>
              <Column field="transaction_count" header="Anzahl Transaktionen" style="text-align:right"></Column>
              <Column field="total_amount" header="Gesamtbetrag" style="text-align:right">
                <template #body="{data}">{{ formatCurrency(data.total_amount) }}</template>
              </Column>
            </DataTable>
          </Panel>
          <!-- Hier könnten später Optionen zum Drucken des Berichts hinzukommen -->
        </div>
        <Message v-if="!isLoading && !reportData && selectedDateDt" severity="info" class="mt-4">
            Keine Daten für das ausgewählte Datum gefunden.
        </Message>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import saleService from '@/services/saleService';
import { useToast } from 'primevue/usetoast';
import Calendar from 'primevue/calendar'; // Import Calendar
import Panel from 'primevue/panel'; // Import Panel
// Globally registered: Card, Button, Message, DataTable, Column

const toast = useToast();

const selectedDateDt = ref(new Date()); // Date object for Calendar
const selectedDateString = ref(new Date().toISOString().split('T')[0]); // YYYY-MM-DD string for API
const reportData = ref(null);
const isLoading = ref(false);
const error = ref('');

// Watch for changes in Calendar's Date object and update the string for API
watch(selectedDateDt, (newDate) => {
  if (newDate instanceof Date) {
    selectedDateString.value = newDate.toISOString().split('T')[0];
    // Optionally auto-fetch report on date change, or wait for button click
    // fetchDailyReport();
  }
});

const handleDateSelect = () => {
    // This callback from Calendar selection can trigger fetch if desired
    // Or rely on the "Bericht laden" button
    fetchDailyReport();
};

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};

const formatDateForDisplay = (dateString) => {
  if (!dateString) return '';
  // API returns YYYY-MM-DD, ensure it's treated as local
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('de-DE', {
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
  if (!selectedDateString.value) {
    reportData.value = null; // Clear previous data
    toast.add({severity:'warn', summary: 'Datum fehlt', detail: 'Bitte wählen Sie ein Datum.', life: 3000});
    return;
  }
  isLoading.value = true;
  error.value = '';
  reportData.value = null;

  try {
    const response = await saleService.getDailySummary(selectedDateString.value);
    reportData.value = response.data;
    if (response.data.overall_transaction_count === 0) {
        toast.add({severity:'info', summary: 'Keine Daten', detail: 'Für das gewählte Datum wurden keine Verkäufe gefunden.', life: 3000});
    }
  } catch (err) {
    const detailMsg = err.response?.data?.detail || 'Unbekannter Fehler.';
    error.value = 'Fehler beim Laden des Tagesberichts: ' + detailMsg;
    toast.add({severity:'error', summary: 'Ladefehler', detail: error.value, life: 5000});
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
/* Using PrimeFlex for padding (p-p-4), layout (grid, flex, etc.) and spacing (mt-4, mb-3) */
.field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}
.w-full { /* Ensure PrimeVue components like Calendar/Dropdown take full width of their grid cell */
    width: 100%;
}
.text-xl { font-size: 1.25rem; } /* PrimeFlex like */
.font-semibold { font-weight: 600; } /* PrimeFlex like */

/* Custom styling for Panel or DataTable if needed */
:deep(.p-panel .p-panel-header) {
    /* background-color: var(--surface-c); */
}
:deep(.p-datatable .p-datatable-thead > tr > th) {
    background-color: var(--surface-b);
    font-weight: bold;
}
</style>
