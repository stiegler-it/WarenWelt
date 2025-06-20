<template>
  <div class="sales-summary-report-view p-4">
    <Toast />
    <Card>
      <template #title>Verkaufsübersicht</template>
      <template #content>
        <div class="p-fluid grid formgrid align-items-end">
          <div class="field col-12 md:col-6 lg:col-3">
            <label for="reportType">Berichtstyp</label>
            <Dropdown id="reportType" v-model="selectedReportType" :options="reportTypeOptions" optionLabel="label" optionValue="value" @change="onReportTypeChange" class="w-full" />
          </div>

          <div v-if="selectedReportType === 'DAILY'" class="field col-12 md:col-6 lg:col-3">
            <label for="report_date_daily">Datum</label>
            <Calendar id="report_date_daily" v-model="selectedDailyDate" dateFormat="dd.mm.yy" :showIcon="true" class="w-full" />
          </div>

          <div v-if="selectedReportType === 'WEEKLY'" class="field col-12 md:col-6 lg:col-3">
            <label for="report_date_weekly">Datum innerhalb der Woche</label>
            <Calendar id="report_date_weekly" v-model="selectedWeeklyDate" dateFormat="dd.mm.yy" :showIcon="true" class="w-full" />
          </div>

          <div v-if="selectedReportType === 'MONTHLY'" class="field col-12 sm:col-6 md:col-3 lg:col-2">
            <label for="report_month">Monat</label>
            <Dropdown id="report_month" v-model="selectedMonth" :options="monthOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div v-if="selectedReportType === 'MONTHLY'" class="field col-12 sm:col-6 md:col-3 lg:col-2">
            <label for="report_year">Jahr</label>
            <InputNumber id="report_year" v-model="selectedYear" mode="decimal" :useGrouping="false" :min="2000" :max="currentYear + 5" class="w-full" />
          </div>

          <div class="field col-12 md:col-4 lg:col-2">
            <Button label="Bericht laden" icon="pi pi-search" @click="fetchReportData" :loading="isLoading" class="w-full" />
          </div>
           <div class="field col-12 md:col-4 lg:col-2" v-if="canExportCurrentReport()">
             <Button label="CSV Export" icon="pi pi-download" class="p-button-secondary w-full" @click="exportReportCSV" :loading="isExporting" />
           </div>
        </div>

        <div v-if="isLoading && !reportData" class="text-center p-4">
            <ProgressSpinner style="width:50px;height:50px" strokeWidth="8" animationDuration=".5s" />
            <p>Lade Bericht...</p>
        </div>
        <Message v-if="error" severity="error" :closable="true" @close="error=''">{{ error }}</Message>

        <div v-if="reportData" class="report-content mt-4">
          <h2 class="text-xl font-semibold mb-3">
            {{ reportTitle }}
          </h2>

          <Panel header="Gesamtübersicht" toggleable class="mb-3" :collapsed="false">
            <div class="grid text-lg">
                <div class="col-6 md:col-4"><strong>Gesamtumsatz:</strong></div>
                <div class="col-6 md:col-8">{{ formatCurrency(reportData.overall_total_amount) }}</div>
                <div class="col-6 md:col-4"><strong>Transaktionen:</strong></div>
                <div class="col-6 md:col-8">{{ reportData.overall_transaction_count }}</div>
                 <div class="col-6 md:col-4" v-if="reportData.total_commission_paid_to_suppliers !== null && reportData.total_commission_paid_to_suppliers !== undefined">
                    <strong>Kommissionen (Lieferanten):</strong>
                </div>
                <div class="col-6 md:col-8" v-if="reportData.total_commission_paid_to_suppliers !== null && reportData.total_commission_paid_to_suppliers !== undefined">
                    {{ formatCurrency(reportData.total_commission_paid_to_suppliers) }}
                </div>
            </div>
          </Panel>

          <Panel header="Umsatz nach Zahlungsart" toggleable :collapsed="false">
            <DataTable :value="reportData.summary_by_payment_method" responsiveLayout="scroll" :rows="5" :paginator="reportData.summary_by_payment_method && reportData.summary_by_payment_method.length > 5">
              <Column field="payment_method" header="Zahlungsart">
                <template #body="{data}">{{ translatePaymentMethod(data.payment_method) }}</template>
              </Column>
              <Column field="transaction_count" header="Anzahl Transaktionen" style="text-align:right" />
              <Column field="total_amount" header="Gesamtbetrag" style="text-align:right">
                <template #body="{data}">{{ formatCurrency(data.total_amount) }}</template>
              </Column>
            </DataTable>
          </Panel>
        </div>
        <Message v-if="!isLoading && !reportData && (selectedDailyDate || selectedReportType === 'MONTHLY' || selectedReportType === 'WEEKLY')" severity="info" class="mt-4">
            Keine Daten für den ausgewählten Zeitraum gefunden oder Berichtstyp noch nicht geladen.
        </Message>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import reportService from '@/services/reportService';
import { useToast } from 'primevue/usetoast';
import Calendar from 'primevue/calendar';
import Panel from 'primevue/panel';
import Dropdown from 'primevue/dropdown';
import InputNumber from 'primevue/inputnumber';
import ProgressSpinner from 'primevue/progressspinner';
import Button from 'primevue/button';
import Message from 'primevue/message';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Toast from 'primevue/toast'; // Ensure Toast is imported if not global


const toast = useToast();

const currentYear = new Date().getFullYear();
const selectedReportType = ref('DAILY');
const selectedDailyDate = ref(new Date());
const selectedWeeklyDate = ref(new Date());
const selectedMonth = ref(new Date().getMonth() + 1);
const selectedYear = ref(currentYear);
const isExporting = ref(false);

const reportData = ref(null);
const isLoading = ref(false);
const error = ref('');

const reportTypeOptions = ref([
  { label: 'Tagesbericht', value: 'DAILY' },
  { label: 'Wochenbericht', value: 'WEEKLY' },
  { label: 'Monatsbericht', value: 'MONTHLY' },
]);

const monthOptions = ref(
  Array.from({ length: 12 }, (_, i) => ({ label: new Date(0, i).toLocaleString('de-DE', { month: 'long' }), value: i + 1 }))
);

const onReportTypeChange = () => {
  reportData.value = null;
  error.value = '';
  if (selectedReportType.value === 'DAILY') selectedDailyDate.value = new Date();
  else if (selectedReportType.value === 'WEEKLY') selectedWeeklyDate.value = new Date();
  else if (selectedReportType.value === 'MONTHLY') {
    selectedMonth.value = new Date().getMonth() + 1;
    selectedYear.value = new Date().getFullYear();
  }
};

const reportTitle = computed(() => {
  if (!reportData.value) return 'Bericht wird geladen...';
  // Check for report_date (daily) or start_date (period)
  if (reportData.value.report_date) { // Daily report structure
    return `Tagesbericht für ${formatDateForDisplay(reportData.value.report_date)}`;
  } else if (reportData.value.start_date && reportData.value.end_date) { // Period report structure
    const typeLabel = reportTypeOptions.value.find(opt => opt.value === reportData.value.report_type)?.label || reportData.value.report_type;
    return `${typeLabel}: ${formatDateForDisplay(reportData.value.start_date)} - ${formatDateForDisplay(reportData.value.end_date)}`;
  }
  return 'Verkaufsübersicht';
});

const fetchReportData = async () => {
  isLoading.value = true;
  error.value = '';
  reportData.value = null;
  let dateStr;

  try {
    let response;
    if (selectedReportType.value === 'DAILY') {
      if (!selectedDailyDate.value) {
        toast.add({ severity: 'warn', summary: 'Datum fehlt', detail: 'Bitte Datum für Tagesbericht wählen.', life: 3000 });
        isLoading.value = false; return;
      }
      dateStr = selectedDailyDate.value.toISOString().split('T')[0];
      response = await reportService.getDailySalesReport(dateStr);
    } else if (selectedReportType.value === 'WEEKLY') {
      if (!selectedWeeklyDate.value) {
        toast.add({ severity: 'warn', summary: 'Datum fehlt', detail: 'Bitte Datum für Wochenbericht wählen.', life: 3000 });
        isLoading.value = false; return;
      }
      dateStr = selectedWeeklyDate.value.toISOString().split('T')[0];
      response = await reportService.getWeeklySalesReport(dateStr);
    } else if (selectedReportType.value === 'MONTHLY') {
      if (!selectedYear.value || !selectedMonth.value) {
        toast.add({ severity: 'warn', summary: 'Zeitraum fehlt', detail: 'Bitte Monat und Jahr wählen.', life: 3000 });
        isLoading.value = false; return;
      }
      response = await reportService.getMonthlySalesReport(selectedYear.value, selectedMonth.value);
    } else {
      toast.add({ severity: 'warn', summary: 'Ungültiger Typ', detail: 'Unbekannter Berichtstyp.', life: 3000 });
      isLoading.value = false; return;
    }
    reportData.value = response.data;
    if (reportData.value && reportData.value.overall_transaction_count === 0) {
      toast.add({ severity: 'info', summary: 'Keine Daten', detail: 'Für den gewählten Zeitraum wurden keine Verkäufe gefunden.', life: 3000 });
    }
  } catch (err) {
    const detailMsg = err.response?.data?.detail || 'Unbekannter Fehler.';
    error.value = `Fehler beim Laden des Berichts: ${detailMsg}`;
    toast.add({ severity: 'error', summary: 'Ladefehler', detail: error.value, life: 5000 });
  } finally {
    isLoading.value = false;
  }
};

const canExportCurrentReport = () => {
    return reportData.value && reportData.value.overall_transaction_count > 0 &&
           (selectedReportType.value === 'DAILY' || selectedReportType.value === 'MONTHLY');
};

const exportReportCSV = async () => {
    if (!canExportCurrentReport()) {
        toast.add({ severity: 'warn', summary: 'Aktion nicht möglich', detail: 'Berichtstyp oder Zeitraum für CSV-Export nicht gültig oder keine Daten vorhanden.', life: 3000 });
        return;
    }
    isExporting.value = true;
    try {
        let blobData; // Changed from blob to blobData to avoid conflict
        let filename;
        if (selectedReportType.value === 'DAILY' && selectedDailyDate.value) {
            const dateStr = selectedDailyDate.value.toISOString().split('T')[0];
            const response = await reportService.downloadDailySalesSummaryCSV(dateStr);
            blobData = response.data; // Axios puts blob in response.data
            filename = `Tagesbericht_${dateStr}.csv`;
        } else if (selectedReportType.value === 'MONTHLY' && selectedYear.value && selectedMonth.value) {
            const response = await reportService.downloadMonthlySalesSummaryCSV(selectedYear.value, selectedMonth.value);
            blobData = response.data;
            filename = `Monatsbericht_${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}.csv`;
        } else {
             isExporting.value = false; return; // Should be caught by canExportCurrentReport
        }

        const link = document.createElement('a');
        link.href = URL.createObjectURL(blobData);
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
        toast.add({ severity: 'success', summary: 'Export erfolgreich', detail: `${filename} heruntergeladen.`, life: 3000 });

    } catch (err) {
        const detailMsg = err.response?.data?.detail || (err.message || 'CSV Export fehlgeschlagen.');
        toast.add({ severity: 'error', summary: 'Exportfehler', detail: detailMsg, life: 5000 });
    } finally {
        isExporting.value = false;
    }
};

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(value));
};
const formatDateForDisplay = (dateInput) => {
  if (!dateInput) return '';
  const date = (typeof dateInput === 'string') ? new Date(dateInput + 'T00:00:00Z') : new Date(dateInput); // Assume UTC if only date string
  return date.toLocaleDateString('de-DE', { year: 'numeric', month: 'long', day: 'numeric' });
};
const translatePaymentMethod = (method) => {
  const translations = { CASH: 'Bar', CARD: 'Karte', VOUCHER: 'Gutschein', MIXED: 'Gemischt' };
  return translations[method] || method;
};

onMounted(() => {
  fetchReportData();
});
</script>

<style scoped>
.sales-summary-report-view { padding: 1rem; }
.field label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.w-full { width: 100%; }
.text-xl { font-size: 1.25rem; }
.font-semibold { font-weight: 600; }
/* :deep(.p-panel .p-panel-header) { } */
/* :deep(.p-datatable .p-datatable-thead > tr > th) { background-color: var(--surface-b); font-weight: bold; } */
.formgrid .field { margin-bottom: 1rem; display: flex; flex-direction: column; }
.formgrid .align-items-end .field { justify-content: flex-end;} /* Align button correctly */

/* Ensure Calendar input takes full width */
:deep(.p-calendar) {
    width: 100%;
}
</style>
