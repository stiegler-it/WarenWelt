<template>
  <div class="shelf-list-view card">
    <Toast />
    <ConfirmDialog></ConfirmDialog>

    <Toolbar class="mb-4">
      <template #start>
        <Button label="Neues Regal" icon="pi pi-plus" class="p-button-success mr-2" @click="openNewShelfDialog" />
      </template>
      <template #end>
        <Button label="Exportieren" icon="pi pi-upload" class="p-button-help" @click="exportCSV" disabled />
        <!-- TODO: Export CSV Funktion für Regale, falls benötigt -->
      </template>
    </Toolbar>

    <DataTable :value="shelves" :loading="isLoading" responsiveLayout="scroll" dataKey="id"
      paginator :rows="10" :rowsPerPageOptions="[5,10,25]"
      v-model:filters="filters" filterDisplay="menu" :globalFilterFields="['name', 'location_description', 'status']">
      <template #header>
        <div class="flex justify-content-between align-items-center">
          <h5 class="m-0">Regalübersicht</h5>
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="filters['global'].value" placeholder="Global suchen..." />
          </span>
        </div>
      </template>
      <template #empty>
        Keine Regale gefunden.
      </template>
      <template #loading>
        Lade Regaldaten...
      </template>

      <Column field="name" header="Name" sortable style="min-width: 12rem">
        <template #body="{data}">{{data.name}}</template>
      </Column>
      <Column field="location_description" header="Standort" sortable style="min-width: 12rem">
         <template #body="{data}">{{data.location_description}}</template>
      </Column>
      <Column field="size_description" header="Größe" style="min-width: 10rem">
        <template #body="{data}">{{data.size_description}}</template>
      </Column>
      <Column field="monthly_rent_price" header="Mietpreis/Monat" sortable style="min-width: 10rem">
        <template #body="{data}">{{ formatCurrency(data.monthly_rent_price) }}</template>
      </Column>
      <Column field="status" header="Status" sortable :showFilterMatchModes="false" style="min-width:10rem">
        <template #filter="{filterModel, filterCallback}">
             <Dropdown v-model="filterModel.value" :options="shelfStatusOptions" optionLabel="label" optionValue="value" placeholder="Alle Status" class="p-column-filter" @change="filterCallback()">
                <template #option="slotProps">
                    <Tag :value="slotProps.option.label" :severity="getSeverityForStatusTag(slotProps.option.value)" />
                </template>
             </Dropdown>
        </template>
        <template #body="{data}">
          <Tag :value="data.status" :severity="getSeverityForStatusTag(data.status)" />
        </template>
      </Column>
       <Column field="is_active" header="Aktiv" sortable dataType="boolean" bodyClass="text-center" style="min-width:8rem">
          <template #body="{data}">
              <i class="pi" :class="{'true-icon pi-check-circle': data.is_active, 'false-icon pi-times-circle': !data.is_active }"></i>
          </template>
           <template #filter="{filterModel, filterCallback}">
                <TriStateCheckbox v-model="filterModel.value" @change="filterCallback()"/>
            </template>
      </Column>
      <Column headerStyle="min-width:10rem;" header="Aktionen">
        <template #body="slotProps">
          <Button icon="pi pi-pencil" class="p-button-rounded p-button-success mr-2" @click="editShelf(slotProps.data)" />
          <Button icon="pi pi-trash" class="p-button-rounded p-button-warning" @click="confirmDeleteShelf(slotProps.data)" />
        </template>
      </Column>
    </DataTable>

    <!-- Dialog für neues/editierendes Regal -->
    <Dialog v_model:visible="shelfDialogVisible" :style="{width: '450px'}" header="Regaldetails" :modal="true" class="p-fluid" @hide="hideShelfDialog">
        <!-- Annahme: ShelfEditForm.vue wird als Komponente hier eingebunden -->
        <ShelfEditForm
            v-if="shelfDialogVisible"
            :shelf-data-prop="currentShelf"
            :is-saving="isSubmittingShelf"
            @shelf-save-event="onShelfSubmit"
            @close-dialog-event="hideShelfDialog"
        />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'; // computed entfernt, da nicht direkt verwendet
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Toolbar from 'primevue/toolbar';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Dropdown from 'primevue/dropdown';
import TriStateCheckbox from 'primevue/tristatecheckbox';
import { FilterMatchMode } from 'primevue/api'; // Import für FilterMatchMode

import shelfService from '@/services/shelfService';
// Platzhalter für die Edit-Form Komponente. Pfad muss ggf. angepasst werden.
import ShelfEditForm from '@/components/shelves/ShelfEditForm.vue';

const toast = useToast();
const confirm = useConfirm();

const shelves = ref([]);
const isLoading = ref(true);
const shelfDialogVisible = ref(false);
const currentShelf = ref({}); // Für das Editieren/Erstellen eines Regals
const isSubmittingShelf = ref(false); // Für Ladezustand des Speicherbuttons in ShelfEditForm

const filters = ref({
    'global': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'status': { value: null, matchMode: FilterMatchMode.EQUALS },
    'is_active': { value: null, matchMode: FilterMatchMode.EQUALS }
});

const shelfStatusOptions = ref([
    {label: 'Verfügbar', value: 'AVAILABLE'},
    {label: 'Vermietet', value: 'RENTED'},
    {label: 'Wartung', value: 'MAINTENANCE'}
]);

const fetchShelves = async () => {
  isLoading.value = true;
  try {
    const response = await shelfService.getAllShelves({ limit: 1000 }); // Beispiel: Lade initial mehr, Paginator im Frontend
    shelves.value = response.data;
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Fehler', detail: 'Regale konnten nicht geladen werden.', life: 3000 });
    console.error("Error fetching shelves:", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchShelves);

const openNewShelfDialog = () => {
  currentShelf.value = { is_active: true, status: 'AVAILABLE', monthly_rent_price: null }; // Standardwerte
  shelfDialogVisible.value = true;
};

const editShelf = (shelf) => {
  currentShelf.value = { ...shelf }; // Kopie des Objekts für Bearbeitung
  shelfDialogVisible.value = true;
};

const hideShelfDialog = () => {
  shelfDialogVisible.value = false;
  currentShelf.value = {}; // Reset
  // Das erneute Setzen von currentShelf auf {} ist eventuell nicht mehr nötig,
  // da die ShelfEditForm-Komponente durch v-if="shelfDialogVisible" bei jedem Schließen zerstört
  // und bei jedem Öffnen neu erstellt wird, wodurch ihr interner Zustand zurückgesetzt wird.
  // Das hängt davon ab, wie die Initialisierung in ShelfEditForm genau gehandhabt wird (props vs. interner State).
};

// Umbenannt von onShelfSaved zu onShelfSubmit und Logik angepasst
const onShelfSubmit = async (shelfToSave) => {
  isSubmittingShelf.value = true;
  try {
    let savedShelfData;
    if (shelfToSave.id) { // Update
      const response = await shelfService.updateShelf(shelfToSave.id, shelfToSave);
      savedShelfData = response.data;
    } else { // Create
      const response = await shelfService.createShelf(shelfToSave);
      savedShelfData = response.data;
    }
    toast.add({ severity: 'success', summary: 'Erfolgreich', detail: `Regal "${savedShelfData.name}" gespeichert.`, life: 3000 });
    hideShelfDialog(); // Schließt den Dialog
    await fetchShelves(); // Lädt die Regalliste neu
  } catch (error) {
    const errorMsg = error.response?.data?.detail || 'Regal konnte nicht gespeichert werden.';
    toast.add({ severity: 'error', summary: 'Fehler beim Speichern', detail: errorMsg, life: 5000 });
    console.error("Error saving shelf:", error);
  } finally {
    isSubmittingShelf.value = false;
  }
};

const confirmDeleteShelf = (shelf) => {
  confirm.require({
    message: `Möchten Sie das Regal "${shelf.name}" wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`,
    header: 'Löschen bestätigen',
    icon: 'pi pi-info-circle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Löschen',
    rejectLabel: 'Abbrechen',
    accept: async () => {
      try {
        await shelfService.deleteShelf(shelf.id);
        toast.add({ severity: 'success', summary: 'Gelöscht', detail: `Regal "${shelf.name}" wurde gelöscht.`, life: 3000 });
        await fetchShelves(); // Daten neu laden
      } catch (error) {
        // Fehlerbehandlung aus der Backend-Antwort
        const errorMsg = error.response?.data?.detail || 'Regal konnte nicht gelöscht werden. Möglicherweise bestehen noch aktive Mietverträge.';
        toast.add({ severity: 'error', summary: 'Fehler beim Löschen', detail: errorMsg, life: 5000 });
        console.error("Error deleting shelf:", error);
      }
    },
  });
};

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(value));
};

const getSeverityForStatusTag = (status) => {
  switch (status) {
    case 'AVAILABLE': return 'success';
    case 'RENTED': return 'info';
    case 'MAINTENANCE': return 'warning';
    default: return 'secondary'; // Fallback
  }
};

const exportCSV = () => {
    toast.add({ severity: 'info', summary: 'Info', detail: 'CSV-Export für Regale ist noch nicht implementiert.', life: 3000 });
};

</script>

<style scoped>
.shelf-list-view {
  padding: 1rem;
}
.true-icon {
  color: var(--green-500);
  font-size: 1.2rem;
}
.false-icon {
  color: var(--pink-500); /* Geändert von red-500 für besseren Kontrast evtl. */
  font-size: 1.2rem;
}
/* PrimeVue dataTable filter anpassungen */
:deep(.p-column-filter-overlay) {
    min-width: 200px;
}
</style>
