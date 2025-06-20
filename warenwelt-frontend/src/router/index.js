import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/auth';

// View Components (Lazy loading for better performance)
const LoginView = () => import('@/views/LoginView.vue');
const DashboardView = () => import('@/views/DashboardView.vue');
const SupplierListView = () => import('@/views/suppliers/SupplierListView.vue');
const SupplierEditView = () => import('@/views/suppliers/SupplierEditView.vue'); // For create and update
const ProductListView = () => import('@/views/products/ProductListView.vue');
const ProductEditView = () => import('@/views/products/ProductEditView.vue');
const PosView = () => import('@/views/sales/PosView.vue');
const PayoutView = () => import('@/views/payouts/PayoutView.vue');
// const DailyReportView = () => import('@/views/reports/DailyReportView.vue'); // Old, replaced
const SalesSummaryReportView = () => import('@/views/reports/SalesSummaryReportView.vue');
const RevenueReportView = () => import('@/views/reports/RevenueReportView.vue');
const PriceTagPrintView = () => import('@/views/products/PriceTagPrintView.vue');
const ProductCategoryListView = () => import('@/views/categories/ProductCategoryListView.vue');
const ProductCategoryEditView = () => import('@/views/categories/ProductCategoryEditView.vue');
const DataImportView = () => import('@/views/import/DataImportView.vue'); // Added
const NotFoundView = () => import('@/views/NotFoundView.vue');
// Rental Management Views
const ShelfListView = () => import('@/views/shelves/ShelfListView.vue');
const RentalContractListView = () => import('@/views/rentalcontracts/RentalContractListView.vue');


const routes = [
  { path: '/login', name: 'Login', component: LoginView },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/suppliers',
    name: 'SupplierList',
    component: SupplierListView,
    meta: { requiresAuth: true },
  },
  {
    path: '/suppliers/new',
    name: 'SupplierNew',
    component: SupplierEditView,
    meta: { requiresAuth: true },
    props: { isNew: true }
  },
  {
    path: '/suppliers/edit/:id',
    name: 'SupplierEdit',
    component: SupplierEditView,
    meta: { requiresAuth: true },
    props: true // Passes route.params as props
  },
  {
    path: '/products',
    name: 'ProductList',
    component: ProductListView,
    meta: { requiresAuth: true },
  },
  {
    path: '/products/new',
    name: 'ProductNew',
    component: ProductEditView,
    meta: { requiresAuth: true },
    props: { isNew: true }
  },
  {
    path: '/products/edit/:id',
    name: 'ProductEdit',
    component: ProductEditView,
    meta: { requiresAuth: true },
    props: true
  },
  {
    path: '/pos', // Point of Sale
    name: 'POS',
    component: PosView,
    meta: { requiresAuth: true },
  },
  {
    path: '/payouts',
    name: 'Payouts',
    component: PayoutView,
    meta: { requiresAuth: true },
  },
  {
    path: '/reports/sales-summary',
    name: 'SalesSummaryReport',
    component: SalesSummaryReportView,
    meta: { requiresAuth: true },
  },
  {
    path: '/reports/revenue-list',
    name: 'RevenueReport',
    component: RevenueReportView,
    meta: { requiresAuth: true },
  },
  {
    path: '/products/print-price-tags',
    name: 'PriceTagPrint',
    component: PriceTagPrintView,
    meta: { requiresAuth: true },
  },
  {
    path: '/product-categories',
    name: 'ProductCategoryList',
    component: ProductCategoryListView,
    meta: { requiresAuth: true },
  },
  {
    path: '/product-categories/new',
    name: 'ProductCategoryNew',
    component: ProductCategoryEditView,
    meta: { requiresAuth: true },
    // props: { isNew: true } // Handled by checking route.params.id in component
  },
  {
    path: '/product-categories/edit/:id',
    name: 'ProductCategoryEdit',
    component: ProductCategoryEditView,
    meta: { requiresAuth: true },
    props: true
  },
  // Shelf Management Routes
  {
    path: '/shelves',
    name: 'ShelfList',
    component: ShelfListView,
    meta: { requiresAuth: true },
  },
  // Rental Contract Management Routes
  {
    path: '/rental-contracts',
    name: 'RentalContractList',
    component: RentalContractListView,
    meta: { requiresAuth: true },
  },
  // Data Import Route
  {
    path: '/import-data',
    name: 'DataImport',
    component: DataImportView,
    meta: { requiresAuth: true }, // Should typically be admin/privileged access
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/:pathMatch(.*)*', // Catch-all for 404
    name: 'NotFound',
    component: NotFoundView
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // Attempt to initialize auth state if token exists but user is not loaded
  // This is useful for page reloads.
  if (authStore.accessToken && !authStore.user) {
    await authStore.initAuth();
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

  if (requiresAuth && !authStore.isAuthenticated) {
    authStore.returnUrl = to.fullPath;
    next('/login');
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    // If user is authenticated and tries to go to login, redirect to dashboard
    next('/dashboard');
  } else {
    next();
  }
});

export default router;
