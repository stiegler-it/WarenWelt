import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ShelfEditForm from '../ShelfEditForm.vue'; // Adjust path as needed
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice'; // If toasts are used within component

// Mock PrimeVue components that are complex or have external dependencies
// For simple inputs, often direct interaction is fine.
// For Dropdown, Calendar, InputNumber, stubs or more detailed setup might be needed
// if their internal logic/rendering affects the test.

// Simple stubs to prevent rendering errors if not testing their internals
const simpleStubs = {
    InputText: { template: '<input />' },
    InputNumber: { template: '<input type="number" />' },
    Dropdown: { template: '<select><option value="AVAILABLE">Available</option></select>' }, // Basic stub
    Checkbox: { template: '<input type="checkbox" />' },
    Button: { template: '<button><slot /></button>' },
};


describe('ShelfEditForm.vue', () => {
  let wrapper;

  const mountForm = (propsData = {}) => {
    return mount(ShelfEditForm, {
      props: {
        shelfDataProp: {
            name: '',
            monthly_rent_price: null,
            status: 'AVAILABLE',
            is_active: true,
            location_description: '',
            size_description: ''
        },
        isSaving: false,
        ...propsData // Merge any specific props for a test
      },
      global: {
        plugins: [PrimeVue, ToastService], // ToastService if useToast is called within setup
        stubs: { // Stubbing components to simplify testing and avoid deep rendering issues
            // More robust stubs might be needed for components like Dropdown/InputNumber
            // if you need to test their specific interactions.
            // For this unit test, we focus on the form's logic.
            InputText: true,
            InputNumber: true,
            Dropdown: true,
            Checkbox: true,
            Button: true,
        }
      }
    });
  };

  beforeEach(() => {
    // Default mounting for most tests, can be overridden in specific 'it' blocks
    // wrapper = mountForm();
  });

  it('renders correctly when created (new shelf)', () => {
    wrapper = mountForm();
    // Check if form elements are present (e.g., by class or id if set)
    // This depends on how much you stubbed. If fully stubbed, check for stubs.
    // expect(wrapper.findComponent({ name: 'InputText' }).exists()).toBe(true); // Example with component name
    expect(wrapper.html()).toContain('Regalname'); // Basic check
    expect(wrapper.vm.editableShelf.status).toBe('AVAILABLE'); // Check default status
  });

  it('initializes with prop data when editing an existing shelf', () => {
    const existingShelf = {
      id: 1, name: 'Existing Regal', monthly_rent_price: 123.45,
      status: 'RENTED', is_active: false,
      location_description: 'Fenster', size_description: 'Groß'
    };
    wrapper = mountForm({ shelfDataProp: existingShelf });

    expect(wrapper.vm.editableShelf.id).toBe(1);
    expect(wrapper.vm.editableShelf.name).toBe('Existing Regal');
    expect(wrapper.vm.editableShelf.monthly_rent_price).toBe(123.45);
    expect(wrapper.vm.editableShelf.status).toBe('RENTED');
    expect(wrapper.vm.editableShelf.is_active).toBe(false);
  });

  it('validates required fields on submit attempt', async () => {
    wrapper = mountForm(); // Mount with default empty/new data
    await wrapper.vm.submitForm(); // Call submit method

    // Vuelidate should mark fields as invalid
    expect(wrapper.vm.v$.editableShelf.name.$invalid).toBe(true);
    expect(wrapper.vm.v$.editableShelf.name.$errors[0].$message).toContain('Pflichtfeld');

    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$invalid).toBe(true);
    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$errors[0].$message).toContain('Pflichtfeld');

    expect(wrapper.vm.v$.editableShelf.status.$invalid).toBe(true); // Status has default 'AVAILABLE'

    // Check that no save event was emitted
    expect(wrapper.emitted('shelf-save-event')).toBeUndefined();
  });

  it('emits "shelf-save-event" with correct payload on valid submission', async () => {
    wrapper = mountForm();
    // Set valid data
    wrapper.vm.editableShelf.name = 'My Test Shelf';
    wrapper.vm.editableShelf.monthly_rent_price = 99.99;
    wrapper.vm.editableShelf.status = 'AVAILABLE';
    // Other fields are optional or have defaults

    await wrapper.vm.submitForm();

    expect(wrapper.vm.v$.$invalid).toBe(false); // Form should be valid
    expect(wrapper.emitted('shelf-save-event')).toBeTruthy();
    expect(wrapper.emitted('shelf-save-event')[0][0]).toEqual(
      expect.objectContaining({
        name: 'My Test Shelf',
        monthly_rent_price: 99.99,
        status: 'AVAILABLE',
        is_active: true, // Default
      })
    );
  });

   it('emits "close-dialog-event" when cancel button is clicked (conceptual)', async () => {
    // This test assumes the Button stub allows finding and clicking, or you test the method directly.
    // For a real Button, you'd do: await wrapper.find('button.p-button-text').trigger('click');
    wrapper = mountForm();
    wrapper.vm.closeDialog(); // Call method directly for simplicity with stubs
    expect(wrapper.emitted('close-dialog-event')).toBeTruthy();
  });

  it('validates monthly_rent_price correctly (positive number)', async () => {
    wrapper = mountForm();

    // Test invalid (negative)
    wrapper.vm.editableShelf.monthly_rent_price = -10;
    await wrapper.vm.v$.editableShelf.monthly_rent_price.$validate();
    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$invalid).toBe(true);
    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$errors[0].$message).toContain('positive Zahl');

    // Test valid
    wrapper.vm.editableShelf.monthly_rent_price = 0.50;
    await wrapper.vm.v$.editableShelf.monthly_rent_price.$validate();
    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$invalid).toBe(false);

     // Test null (should be caught by required if that's the intent, or validPrice handles it)
    wrapper.vm.editableShelf.monthly_rent_price = null;
    await wrapper.vm.v$.editableShelf.monthly_rent_price.$validate();
    // Depending on if null is allowed before 'required' kicks in
    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$invalid).toBe(true); // because it's required
    expect(wrapper.vm.v$.editableShelf.monthly_rent_price.$errors.some(e => e.$message.includes('Pflichtfeld'))).toBe(true);

  });

  // Note: Testing interactions with PrimeVue components like Dropdown selection or InputNumber formatting
  // often requires more complex setup, potentially avoiding stubs for those components or using
  // specific helper methods to interact with them if @vue/test-utils doesn't handle it easily.
  // For unit tests, focusing on the component's own logic (validation rules, event emission, data handling)
  // is often prioritized, with complex child interactions covered in integration/E2E tests.
});
