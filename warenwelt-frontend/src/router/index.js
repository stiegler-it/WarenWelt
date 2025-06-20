import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/auth';

// View Components (Lazy loading for better performance)
const LoginView = () => import('@/views/LoginView.vue');
const DashboardView = () => import('@/views/DashboardView.vue');
const SupplierListView = () => import('@/views/suppliers/SupplierListView.vue');
const SupplierEditView = () => import('@/views/suppliers/SupplierEditView.vue'); // For create and update
const ProductListView = () => import('@/views/products/ProductListView.vue');
const ProductEditView = () => import('@/views/products/ProductEditView.vue'); // For create and update
const PosView = () => import('@/views/sales/PosView.vue');
const PayoutView = () => import('@/views/payouts/PayoutView.vue');
const NotFoundView = () => import('@/views/NotFoundView.vue'); // Simple 404 page

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
