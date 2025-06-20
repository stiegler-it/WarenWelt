<template>
  <div class="payout-view p-p-4">
    <Card>
      <template #title>
        Auszahlungen an Lieferanten
      </template>
      <template #content>
        <div class="p-fluid grid">
          <div class="field col-12 md:col-6">
            <label for="selected_supplier">Lieferant auswählen</label>
            <Dropdown
              id="selected_supplier"
              v-model="selectedSupplierId"
              :options="availableSuppliers"
              optionLabel="displayName"
              optionValue="id"
              placeholder="-- Bitte Lieferant wählen --"
              @change="fetchPayoutSummary"
              :filter="availableSuppliers.length > 10"
              showClear
              class="w-full"
            />
          </div>
        </div>

        <div v-if="isLoadingSummary" class="text-center p-p-4">
             <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
             <p>Lade Auszahlungsübersicht...</p>
        </div>
        <Message v-if="summaryError" severity="error" :closable="false">{{ summaryError }}</Message>

        <div v-if="payoutSummary && selectedSupplierId" class="payout-summary mt-4">
          <Panel :header="`Übersicht für ${payoutSummary.supplier_name}`" toggleable>
            <p><strong>Gesamtauszahlung fällig: {{ formatCurrency(payoutSummary.total_due) }}</strong></p>
            <p>Anzahl abrechenbarer Artikel: {{ payoutSummary.eligible_items_count }}</p>

            <div v-if="payoutSummary.items_preview.length > 0" class="mt-3">
              <h4 class="text-md font-semibold mb-2">Vorschau einiger abrechenbarer Artikel:</h4>
              <ul class="list-none p-0 m-0">
                <li v-for="item in payoutSummary.items_preview" :key="item.product_id + '_' + item.sale_id" class="p-mb-1 text-sm">
                  {{ item.product_name }} (SKU: {{ item.product_sku }}) - verkauft am {{ formatDate(item.sale_date) }} - Provision: {{ formatCurrency(item.commission_amount) }}
                </li>
              </ul>
            </div>
            <p v-else-if="payoutSummary.eligible_items_count === 0 && !isLoadingSummary" class="mt-3 text-sm">
              Keine Artikel zur Auszahlung fällig für diesen Lieferanten.
            </p>

            <div class="mt-4" v-if="payoutSummary.eligible_items_count > 0">
                <Button
                    label="Auszahlung erstellen"
                    icon="pi pi-send"
                    @click="confirmProcessPayout"
                    :loading="isLoadingPayout"
                    :disabled="payoutSummary.total_due <= 0"
                />
            </div>
          </Panel>
        </div>
         <Message v-else-if="!isLoadingSummary && selectedSupplierId && !summaryError" severity="info">
            Keine Auszahlungsdaten für den gewählten Lieferanten oder es wurden keine fälligen Posten gefunden.
        </Message>

        <Divider layout="horizontal" class="my-4" />

        <h3 class="text-lg font-semibold mb-3">Vergangene Auszahlungen</h3>
        <DataTable
            :value="pastPayouts"
            :loading="isLoadingPastPayouts"
            paginator :rows="10"
            responsiveLayout="scroll"
            sortField="payout_date" :sortOrder="-1"
        >
            <template #empty>Keine vergangenen Auszahlungen gefunden.</template>
            <template #loading>Lade vergangene Auszahlungen...</template>

            <Column field="payout_number" header="Auszahlungsnr." sortable></Column>
            <Column field="supplier.displayName" header="Lieferant" sortable>
                 <template #body="{data}">{{ data.supplier.supplier_number }} - {{ data.supplier.company_name || (data.supplier.first_name + ' ' + data.supplier.last_name).trim() }}</template>
            </Column>
            <Column field="payout_date" header="Datum" sortable>
                <template #body="{data}">{{ formatDate(data.payout_date) }}</template>
            </Column>
            <Column field="total_amount" header="Betrag" sortable dataType="numeric" style="text-align:right">
                <template #body="{data}">{{ formatCurrency(data.total_amount) }}</template>
            </Column>
             <Column header="Aktionen" style="width:10rem; text-align:center;">
                <template #body="{data}">
                    <Button icon="pi pi-eye" class="p-button-rounded p-button-info p-button-text" @click="viewPayoutDetails(data)" v-tooltip.top="'Details anzeigen'" />
                </template>
            </Column>
        </DataTable>
      </template>
    </Card>

    <!-- Dialog for Payout Details -->
    <Dialog header="Auszahlungsdetails" v-model:visible="showPayoutDetailDialog" :modal="true" :style="{width: '70vw'}">
        <div v-if="selectedPayoutDetail">
            <p><strong>Auszahlungsnr.:</strong> {{ selectedPayoutDetail.payout_number }}</p>
            <p><strong>Lieferant:</strong> {{ selectedPayoutDetail.supplier.displayName }}</p>
            <p><strong>Datum:</strong> {{ formatDate(selectedPayoutDetail.payout_date) }}</p>
            <p><strong>Betrag:</strong> {{ formatCurrency(selectedPayoutDetail.total_amount) }}</p>
            <p><strong>Notizen:</strong> {{ selectedPayoutDetail.notes || '-' }}</p>
            <h4 class="mt-3">Abgerechnete Artikel:</h4>
            <DataTable :value="selectedPayoutDetail.items_paid_out" responsiveLayout="scroll" :rows="5" paginator>
                <Column field="product.sku" header="SKU"></Column>
                <Column field="product.name" header="Artikel"></Column>
                <Column field="price_at_sale" header="Verkaufspreis">
                    <template #body="{data}">{{ formatCurrency(data.price_at_sale) }}</template>
                </Column>
                <Column field="commission_amount_at_sale" header="Provision">
                     <template #body="{data}">{{ formatCurrency(data.commission_amount_at_sale) }}</template>
                </Column>
                 <Column field="sale.transaction_time" header="Verkaufsdatum">
                    <template #body="{data}">{{ formatDate(data.sale?.transaction_time) }}</template>
                </Column>
            </DataTable>
        </div>
        <template #footer>
            <Button label="Schließen" icon="pi pi-times" @click="showPayoutDetailDialog = false" class="p-button-text"/>
        </template>
    </Dialog>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import supplierService from '@/services/supplierService';
import payoutService from '@/services/payoutService';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from "primevue/useconfirm"; // For confirmation dialog
import Panel from 'primevue/panel'; // Import Panel
import Divider from 'primevue/divider'; // Import Divider
// Globally registered: Card, Dropdown, Button, Message, DataTable, Column, Dialog, Tooltip

const toast = useToast();
const confirm = useConfirm();

const availableSuppliers = ref([]);
const selectedSupplierId = ref(null);

const payoutSummary = ref(null);
const isLoadingSummary = ref(false);
const summaryError = ref('');

const isLoadingPayout = ref(false);

const pastPayouts = ref([]);
const isLoadingPastPayouts = ref(false);

const showPayoutDetailDialog = ref(false);
const selectedPayoutDetail = ref(null);


const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
};
const formatDate = (dateString) => {
  if (!dateString) return '';
  // Ensure correct parsing for dates that might just be YYYY-MM-DD
  const date = new Date(dateString);
  if (dateString && dateString.length === 10) { // Likely YYYY-MM-DD, add time to avoid UTC issues
      return new Date(dateString + 'T00:00:00').toLocaleDateString('de-DE');
  }
  return date.toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit', hour:'2-digit', minute: '2-digit' });
};

onMounted(async () => {
  try {
    const response = await supplierService.getSuppliers({ limit: 1000, is_internal: false });
    availableSuppliers.value = response.data.map(s => ({
        ...s,
        displayName: `${s.supplier_number} - ${s.company_name || (s.first_name + ' ' + s.last_name).trim()}`
    }));
    fetchPastPayouts();
  } catch (err) {
    toast.add({severity:'error', summary: 'Fehler', detail: 'Lieferanten konnten nicht geladen werden.', life: 3000});
  }
});

const fetchPayoutSummary = async () => {
  if (!selectedSupplierId.value) {
    payoutSummary.value = null;
    summaryError.value = '';
    return;
  }
  isLoadingSummary.value = true;
  summaryError.value = '';
  try {
    const response = await payoutService.getPayoutSummary(selectedSupplierId.value);
    payoutSummary.value = response.data;
  } catch (err) {
    summaryError.value = 'Fehler beim Laden der Auszahlungsübersicht: ' + (err.response?.data?.detail || err.message);
    payoutSummary.value = null;
     toast.add({severity:'error', summary: 'Fehler Auszahlungsübersicht', detail: summaryError.value, life: 5000});
  } finally {
    isLoadingSummary.value = false;
  }
};

const confirmProcessPayout = () => {
    if (!selectedSupplierId.value || !payoutSummary.value || payoutSummary.value.total_due <= 0) {
        toast.add({severity:'warn', summary: 'Ungültig', detail: 'Keine gültige Auszahlung möglich.', life: 3000});
        return;
    }
    confirm.require({
        message: `Möchten Sie wirklich eine Auszahlung über ${formatCurrency(payoutSummary.value.total_due)} an ${payoutSummary.value.supplier_name} erstellen?`,
        header: 'Auszahlung bestätigen',
        icon: 'pi pi-info-circle',
        acceptClass: 'p-button-success',
        acceptLabel: 'Ja, erstellen',
        rejectLabel: 'Abbrechen',
        accept: () => {
            processPayout();
        },
        reject: () => {
            toast.add({severity:'info', summary: 'Abgebrochen', detail: 'Auszahlung nicht erstellt.', life: 3000});
        }
    });
};

const processPayout = async () => {
  isLoadingPayout.value = true;
  try {
    const payload = { supplier_id: selectedSupplierId.value };
    const response = await payoutService.createPayout(payload);
    toast.add({
        severity:'success',
        summary: 'Erfolgreich',
        detail: `Auszahlung ${response.data.payout_number} über ${formatCurrency(response.data.total_amount)} erstellt.`,
        life: 5000
    });
    fetchPayoutSummary();
    fetchPastPayouts();
  } catch (err) {
    const detailMsg = err.response?.data?.detail || 'Unbekannter Fehler beim Erstellen der Auszahlung.';
    toast.add({severity:'error', summary: 'Fehler bei Auszahlung', detail: detailMsg, life: 7000});
  } finally {
    isLoadingPayout.value = false;
  }
};

const fetchPastPayouts = async () => {
    isLoadingPastPayouts.value = true;
    try {
        const response = await payoutService.getPayouts({limit: 50}); // Get recent 50
        pastPayouts.value = response.data.map(p => ({
            ...p,
            supplier: {
                ...p.supplier,
                displayName: `${p.supplier.supplier_number} - ${p.supplier.company_name || (p.supplier.first_name + ' ' + p.supplier.last_name).trim()}`
            }
        }));
    } catch (err) {
        toast.add({severity:'error', summary: 'Fehler', detail: 'Vergangene Auszahlungen konnten nicht geladen werden.', life: 3000});
    } finally {
        isLoadingPastPayouts.value = false;
    }
};

const viewPayoutDetails = async (payoutData) => {
    // For full details including items, we might need to fetch the specific payout again
    // if the list view doesn't contain all item details.
    // Assuming the `payoutData` from the list is sufficient or we fetch more.
    try {
        isLoadingPastPayouts.value = true; // Or a new loading state for dialog
        const response = await payoutService.getPayout(payoutData.id);
        selectedPayoutDetail.value = {
            ...response.data,
             supplier: { // Ensure displayName is available for dialog
                ...response.data.supplier,
                displayName: `${response.data.supplier.supplier_number} - ${response.data.supplier.company_name || (response.data.supplier.first_name + ' ' + response.data.supplier.last_name).trim()}`
            }
        };
        showPayoutDetailDialog.value = true;
    } catch (err) {
         toast.add({severity:'error', summary: 'Fehler', detail: 'Details der Auszahlung konnten nicht geladen werden.', life: 3000});
    } finally {
        isLoadingPastPayouts.value = false;
    }
};

</script>

<style scoped>
/* Using PrimeFlex for padding (p-p-4), layout (grid, flex, etc.) and spacing (mt-4, mb-2, my-4) */
.payout-summary ul {
    list-style-type: disc; /* More standard list style */
    padding-left: 20px;
}
.payout-summary li {
    margin-bottom: 0.25rem;
}
.text-sm { font-size: 0.875rem; } /* PrimeFlex like */
.text-md { font-size: 1rem; } /* PrimeFlex like */

:deep(.p-panel-header) { /* Example of styling a PrimeVue component's internals */
    /* background-color: var(--primary-color); */
    /* color: var(--primary-color-text); */
}
:deep(.p-datatable) {
    margin-top: 1rem;
}
</style>
