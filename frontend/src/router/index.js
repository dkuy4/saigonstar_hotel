import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import ResultsView from '../views/ResultsView.vue';
import BookingView from '../views/BookingView.vue';
import BookingHoldView from '../views/BookingHoldView.vue';
import BookingDetailView from '../views/BookingDetailView.vue';
import MockPayView from '../views/MockPayView.vue';
import PaymentResultView from '../views/PaymentResultView.vue';
import NotFoundView from '../views/NotFoundView.vue';
import LoginView from '../views/staff/LoginView.vue';
import RoomBoardView from '../views/staff/RoomBoardView.vue';
import HousekeepingView from '../views/staff/HousekeepingView.vue';
import BookingListView from '../views/staff/BookingListView.vue';
import CounterBookingCreateView from '../views/staff/CounterBookingCreateView.vue';
import StaffBookingDetailView from '../views/staff/StaffBookingDetailView.vue';
import ReportsView from '../views/staff/ReportsView.vue';
import { useAuthStore } from '../stores/auth';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/ket-qua',
    name: 'results',
    component: ResultsView
  },
  {
    path: '/dat-phong',
    name: 'booking',
    component: BookingView
  },
  {
    path: '/giu-cho/:code',
    name: 'booking-hold',
    component: BookingHoldView
  },
  {
    path: '/mock-pay/:ref',
    name: 'mock-pay',
    component: MockPayView
  },
  {
    path: '/thanh-toan/ket-qua',
    name: 'payment-result',
    component: PaymentResultView
  },
  {
    path: '/don/tra-cuu',
    name: 'booking-lookup',
    component: BookingDetailView
  },
  {
    path: '/don/:code',
    name: 'booking-detail',
    component: BookingDetailView
  },
  {
    path: '/nv/dang-nhap',
    name: 'login',
    component: LoginView
  },
  {
    path: '/nv/so-do-phong',
    name: 'room-board',
    component: RoomBoardView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/nv/don',
    name: 'booking-list',
    component: BookingListView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/nv/don/moi',
    name: 'counter-booking-create',
    component: CounterBookingCreateView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/nv/don/:id',
    name: 'staff-booking-detail',
    component: StaffBookingDetailView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/nv/don-phong',
    name: 'housekeeping',
    component: HousekeepingView,
    meta: { requiresAuth: true, roles: ['BUONG_PHONG', 'QUAN_LY'] }
  },
  {
    path: '/nv/bao-cao',
    name: 'reports',
    component: ReportsView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/404',
    name: 'not-found',
    component: NotFoundView
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard for role-based routes
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      return next({ path: '/nv/dang-nhap', query: { redirect: to.fullPath } });
    }
    
    if (to.meta.roles && !to.meta.roles.includes(authStore.role)) {
      // Forbidden: redirect to their default home or 404
      if (authStore.role === 'BUONG_PHONG') {
        return next({ path: '/nv/don-phong' });
      } else {
        return next({ path: '/nv/so-do-phong' });
      }
    }
  }

  // If authenticated user visits login, redirect to dashboard
  if (to.path === '/nv/dang-nhap' && authStore.isAuthenticated) {
    if (authStore.role === 'BUONG_PHONG') {
      return next({ path: '/nv/don-phong' });
    } else {
      return next({ path: '/nv/so-do-phong' });
    }
  }

  next();
});

export default router;
