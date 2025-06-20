<template>
  <div class="revenue-report-view p-4">
    <Toast />
    <Card>
      <template #title>Umsatzlistenbericht</template>
      <template #content>
        <div class="p-fluid grid formgrid align-items-end mb-4">
          <div class="field col-12 md:col-6 lg:col-3">
            <label for="start_date">Startdatum</label>
            <Calendar id="start_date" v-model="startDate" dateFormat="dd.mm.yy" :showIcon="true" class="w-full" />
          </div>
          <div class="field col-12 md:col-6 lg:col-3">
            <label for="end_date">Enddatum</label>
            <Calendar id="end_date" v-model="endDate" dateFormat="dd.mm.yy" :showIcon="true" class="w-full" :minDate="minCalendarEndDate" />
          </div>
          <div class="field col-12 md:col-6 lg:col-3">
            <Button label="Bericht laden" icon="pi pi-search" @click="fetchRevenueReport" :loading="isLoading" class="w-full" />
          </div>
          <div class="field col-12 md:col-6 lg:col-3" v-if="reportData && reportData.revenue_items && reportData.revenue_items.length > 0">
            <Button label="DATEV CSV Export" icon="pi pi-download" class="p-button-secondary w-full" @click="exportRevenueCSV" :loading="isExporting" />
          </div>
        </div>

        <div v-if="isLoading && !reportData" class="text-center p-4">
          <ProgressSpinner style="width:50px;height:50px" strokeWidth="8" animationDuration=".5s" />
          <p>Lade Umsatzliste...</p>
        </div>
        <Message v-if="error" severity="error" :closable="true" @close="error=''">{{ error }}</Message>

        <div v-if="reportData" class="report-content mt-4">
          <h2 class="text-xl font-semibold mb-3">
            Umsatzliste für Zeitraum: {{ formatDateForDisplay(reportData.report_period_start_date) }} - {{ formatDateForDisplay(reportData.report_period_end_date) }}
          </h2>
          <p class="text-sm text-color-secondary mb-3">Generiert am: {{ formatDateTimeForDisplay(reportData.report_generated_at) }}</p>

          <Panel header="Gesamtübersicht Umsatz" toggleable class="mb-3" :collapsed="false">
            <div class="grid text-lg">
              <div class="col-6 md:col-4"><strong>Gesamt Bruttoumsatz:</strong></div>
              <div class="col-6 md:col-8">{{ formatCurrency(reportData.total_gross_revenue_all_items) }}</div>
              <div class="col-6 md:col-4"><strong>Verkaufte Artikel (gesamt):</strong></div>
              <div class="col-6 md:col-8">{{ reportData.total_items_sold }}</div>
            </div>
          </Panel>

          <Panel header="Umsatz nach Produkttyp" toggleable class="mb-3" :collapsed="false">
             <div v-if="reportData.summary_by_product_type && Object.keys(reportData.summary_by_product_type).length > 0" class="grid">
                <template v-for="(summary, type) in reportData.summary_by_product_type" :key="type">
                    <div class="col-12 md:col-6 p-field">
                        <Card class="h-full">
                            <template #title><span class="text-lg">{{ translateProductType(type) }}</span></template>
                            <template #content>
                                <p><strong>Gesamtumsatz:</strong> {{ formatCurrency(summary.total_revenue) }}</p>
                                <p><strong>Kosten/Lieferantenanteil:</strong> {{ formatCurrency(summary.total_cost_or_commission) }}</p>
                                <p><strong>Anzahl Artikel:</strong> {{ summary.item_count }}</p>
                            </template>
                        </Card>
                    </div>
                </template>
            </div>
            <Message v-else severity="info">Keine Zusammenfassung nach Produkttyp verfügbar.</Message>
          </Panel>

          <DataTable :value="reportData.revenue_items" responsiveLayout="scroll" paginator :rows="15" :rowsPerPageOptions="[10,15,25,50,100]"
            sortField="sale_transaction_time" :sortOrder="-1" class="p-datatable-sm" stripedRows
            v-model:filters="revenueFilters" filterDisplay="row" :globalFilterFields="['product_name', 'product_sku', 'transaction_number']">
            <template #header>
                 <div class="flex justify-content-between align-items-center">
                    <h5 class="m-0">Detaillierte Umsatzposten</h5>
                    <span class="p-input-icon-left">
                        <i class="pi pi-search" />
                        <InputText v-model="revenueFilters['global'].value" placeholder="Posten suchen..." />
                    </span>
                </div>
            </template>
            <template #empty>Keine Umsatzposten im ausgewählten Zeitraum gefunden.</template>

            <Column field="sale_transaction_time" header="Verkaufsdatum" sortable dataType="date" style="min-width: 10rem;">
              <template #body="{data}">{{ formatDateTimeForDisplay(data.sale_transaction_time) }}</template>
            </Column>
            <Column field="transaction_number" header="Belegnr." sortable filterField="transaction_number" :showFilterMenu="false" style="min-width: 8rem;">
                <template #filter="{filterModel, filterCallback}"><InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter" /></template>
            </Column>
            <Column field="product_sku" header="SKU" sortable filterField="product_sku" :showFilterMenu="false" style="min-width: 8rem;">
                 <template #filter="{filterModel, filterCallback}"><InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"/></template>
            </Column>
            <Column field="product_name" header="Produktname" sortable filterField="product_name" :showFilterMenu="false" style="min-width: 15rem;">
                 <template #filter="{filterModel, filterCallback}"><InputText type="text" v-model="filterModel.value" @keydown.enter="filterCallback()" class="p-column-filter"/></template>
            </Column>
            <Column field="product_type" header="Typ" sortable filterField="product_type" :showFilterMenu="false" style="min-width: 8rem;">
                <template #filter="{filterModel, filterCallback}">
                    <Dropdown v-model="filterModel.value" :options="productTypeOptionsForFilter" optionLabel="label" optionValue="value" placeholder="Alle Typen" class="p-column-filter" @change="filterCallback()" showClear />
                </template>
                <template #body="{data}">{{ translateProductType(data.product_type) }}</template>
            </Column>
            <Column field="quantity_sold" header="Menge" sortable style="min-width: 6rem; text-align:right;"></Column>
            <Column field="price_per_unit_at_sale" header="Preis/Einheit" sortable dataType="numeric" style="min-width: 9rem; text-align:right;">
              <template #body="{data}">{{ formatCurrency(data.price_per_unit_at_sale) }}</template>
            </Column>
            <Column field="total_gross_revenue_for_item" header="Gesamt (Brutto)" sortable dataType="numeric" style="min-width: 10rem; text-align:right;">
              <template #body="{data}">{{ formatCurrency(data.total_gross_revenue_for_item) }}</template>
            </Column>
            <Column field="total_cost_or_commission_for_item" header="Kosten/Anteil Lieferant" sortable dataType="numeric" style="min-width: 10rem; text-align:right;">
              <template #body="{data}">{{ formatCurrency(data.total_cost_or_commission_for_item) }}</template>
            </Column>
             <Column field="tax_rate_percentage_at_sale" header="USt. Satz (%)" sortable dataType="numeric" style="min-width: 8rem; text-align:right;">
                <template #body="{data}">{{ data.tax_rate_percentage_at_sale ? data.tax_rate_percentage_at_sale + '%' : 'N/A' }}</template>
            </Column>
          </DataTable>
        </div>
         <Message v-if="!isLoading && !reportData && startDate && endDate" severity="info" class="mt-4">
            Keine Umsatzdaten für den ausgewählten Zeitraum gefunden.
        </Message>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import reportService from '@/services/reportService';
import { useToast } from 'primevue/usetoast';
import Calendar from 'primevue/calendar';
import Panel from 'primevue/panel';
import ProgressSpinner from 'primevue/progressspinner';
import Button from 'primevue/button';
import Message from 'primevue/message';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Toast from 'primevue/toast';
import InputText from 'primevue/inputtext'; // For table header filter
import Dropdown from 'primevue/dropdown'; // For product type filter
import { FilterMatchMode } from 'primevue/api';


const toast = useToast();

const today = new Date();
const firstDayOfCurrentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
const startDate = ref(firstDayOfCurrentMonth);
const endDate = ref(today);

const reportData = ref(null);
const isLoading = ref(false);
const isExporting = ref(false);
const error = ref('');

const revenueFilters = ref({
    'global': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'transaction_number': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'product_sku': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'product_name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'product_type': { value: null, matchMode: FilterMatchMode.EQUALS },
});
const productTypeOptionsForFilter = ref([
    {label: 'Neuware', value: 'NEW_WARE'},
    {label: 'Kommission', value: 'COMMISSION'}
]);

const minCalendarEndDate = computed(() => {
    return startDate.value || null;
});


const fetchRevenueReport = async () => {
  if (!startDate.value || !endDate.value) {
    toast.add({ severity: 'warn', summary: 'Zeitraum fehlt', detail: 'Bitte Start- und Enddatum auswählen.', life: 3000 });
    return;
  }
  if (new Date(startDate.value) > new Date(endDate.value)) {
    toast.add({ severity: 'warn', summary: 'Ungültiger Zeitraum', detail: 'Startdatum darf nicht nach dem Enddatum liegen.', life: 3000 });
    return;
  }

  isLoading.value = true;
  error.value = '';
  reportData.value = null;

  try {
    const startDateStr = startDate.value.toISOString().split('T')[0];
    const endDateStr = endDate.value.toISOString().split('T')[0];
    const response = await reportService.getRevenueListReport(startDateStr, endDateStr);
    reportData.value = response.data;
     if (reportData.value && (!reportData.value.revenue_items || reportData.value.revenue_items.length === 0)) {
      toast.add({ severity: 'info', summary: 'Keine Daten', detail: 'Für den gewählten Zeitraum wurden keine Umsatzposten gefunden.', life: 4000 });
    }
  } catch (err) {
    const detailMsg = err.response?.data?.detail || 'Unbekannter Fehler.';
    error.value = `Fehler beim Laden der Umsatzliste: ${detailMsg}`;
    toast.add({ severity: 'error', summary: 'Ladefehler', detail: error.value, life: 5000 });
  } finally {
    isLoading.value = false;
  }
};

const exportRevenueCSV = async () => {
    if (!startDate.value || !endDate.value || !reportData.value || !reportData.value.revenue_items || reportData.value.revenue_items.length === 0) {
        toast.add({ severity: 'warn', summary: 'Keine Daten', detail: 'Es gibt keine Berichtsdaten zum Exportieren.', life: 3000 });
        return;
    }
    isExporting.value = true;
    try {
        const startDateStr = startDate.value.toISOString().split('T')[0];
        const endDateStr = endDate.value.toISOString().split('T')[0];
        const response = await reportService.downloadRevenueListDatevLikeCSV(startDateStr, endDateStr);
        const blob = response.data;
        const filename = `Umsatzliste_DATEV_${startDateStr}_bis_${endDateStr}.csv`;

        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
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
  const date = (typeof dateInput === 'string' && !dateInput.includes('T')) ? new Date(dateInput + 'T00:00:00Z') : new Date(dateInput);
  return date.toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit' });
};
const formatDateTimeForDisplay = (dateTimeInput) => {
  if (!dateTimeInput) return '';
  return new Date(dateTimeInput).toLocaleString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};
const translateProductType = (type) => {
  const translations = { NEW_WARE: 'Neuware', COMMISSION: 'Kommission' };
  return translations[type] || type;
};

onMounted(() => {
  fetchRevenueReport();
});

</script>

<style scoped>
.revenue-report-view { padding: 1rem; }
.field label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.w-full { width: 100%; }
.text-xl { font-size: 1.25rem; }
.font-semibold { font-weight: 600; }
.formgrid .field { margin-bottom: 1rem; display: flex; flex-direction: column; }
.formgrid .align-items-end .field { justify-content: flex-end;}
:deep(.p-panel-content) { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.p-field { padding: 0.5rem; }
.h-full { height: 100%; }
:deep(.p-datatable-sm .p-datatable-thead > tr > th) {
    padding-top: 0.75rem;
    padding-bottom: 0.75rem;
}
:deep(.p-datatable-sm .p-datatable-tbody > tr > td) {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}
:deep(.p-column-filter) {
    width: 100%;
}
</style>
