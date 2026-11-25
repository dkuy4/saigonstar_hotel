import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import ResultsView from '../views/ResultsView.vue';
import BookingView from '../views/BookingView.vue';
import BookingHoldView from '../views/BookingHoldView.vue';
import BookingDetailView from '../views/BookingDetailView.vue';
import MockPayView from '../views/MockPayView.vue';
import PaymentResultView from '../views/PaymentResultView.vue';
import NotFoundView from '../views/NotFoundView.vue';

// Guest Account Views
import GuestLoginView from '../views/guest/GuestLoginView.vue';
import GuestRegisterView from '../views/guest/GuestRegisterView.vue';
import GuestForgotPasswordView from '../views/guest/GuestForgotPasswordView.vue';
import GuestBookingsView from '../views/guest/GuestBookingsView.vue';

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
  // Guest Account Routes
  {
    path: '/dang-nhap',
    name: 'guest-login',
    component: GuestLoginView
  },
  {
    path: '/dang-ky',
    name: 'guest-register',
    component: GuestRegisterView
  },
  {
    path: '/quen-mat-khau',
    name: 'guest-forgot-password',
    component: GuestForgotPasswordView
  },
  {
    path: '/chuyen-di-cua-toi',
    name: 'guest-bookings',
    component: GuestBookingsView,
    meta: { requiresGuestAuth: true }
  },
  {
    // Chuyển hướng người dùng/nhân viên sang cổng Admin độc lập port 5174
    path: '/nv/:pathMatch(.*)*',
    beforeEnter() {
      window.location.href = 'http://127.0.0.1:5174/';
    }
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

// Navigation guard for guest protected routes
router.beforeEach((to, from, next) => {
  const guestToken = localStorage.getItem('guest_token');
  if (to.meta.requiresGuestAuth && !guestToken) {
    return next({ path: '/dang-nhap', query: { redirect: to.fullPath } });
  }
  next();
});

export default router;
