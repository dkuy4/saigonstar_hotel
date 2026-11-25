import { createRouter, createWebHistory } from 'vue-router';
import LoginView from '../views/staff/LoginView.vue';
import RoomBoardView from '../views/staff/RoomBoardView.vue';
import HousekeepingView from '../views/staff/HousekeepingView.vue';
import BookingListView from '../views/staff/BookingListView.vue';
import CounterBookingCreateView from '../views/staff/CounterBookingCreateView.vue';
import StaffBookingDetailView from '../views/staff/StaffBookingDetailView.vue';
import ReportsView from '../views/staff/ReportsView.vue';
import RoomAdminView from '../views/staff/RoomAdminView.vue';
import RoomTypeAdminView from '../views/staff/RoomTypeAdminView.vue';
import PriceAdminView from '../views/staff/PriceAdminView.vue';
import SettingAdminView from '../views/staff/SettingAdminView.vue';
import TranslationAdminView from '../views/staff/TranslationAdminView.vue';
import UserAdminView from '../views/staff/UserAdminView.vue';
import AuditLogsView from '../views/staff/AuditLogsView.vue';
import RefundManagementView from '../views/staff/RefundManagementView.vue';
import ReconciliationView from '../views/staff/ReconciliationView.vue';
import SystemManagementView from '../views/staff/SystemManagementView.vue';
import NotFoundView from '../views/NotFoundView.vue';
import { useAuthStore } from '../stores/auth';

const routes = [
  {
    path: '/',
    redirect: '/so-do-phong'
  },
  {
    path: '/dang-nhap',
    alias: '/nv/dang-nhap',
    name: 'login',
    component: LoginView
  },
  {
    path: '/so-do-phong',
    alias: '/nv/so-do-phong',
    name: 'room-board',
    component: RoomBoardView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/don',
    alias: '/nv/don',
    name: 'booking-list',
    component: BookingListView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/don/moi',
    alias: '/nv/don/moi',
    name: 'counter-booking-create',
    component: CounterBookingCreateView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/don/:id',
    alias: '/nv/don/:id',
    name: 'staff-booking-detail',
    component: StaffBookingDetailView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/don-phong',
    alias: '/nv/don-phong',
    name: 'housekeeping',
    component: HousekeepingView,
    meta: { requiresAuth: true, roles: ['BUONG_PHONG', 'LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/hoan-tien',
    alias: '/nv/hoan-tien',
    name: 'refund-management',
    component: RefundManagementView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/doi-soat',
    alias: '/nv/doi-soat',
    name: 'reconciliation',
    component: ReconciliationView,
    meta: { requiresAuth: true, roles: ['LE_TAN', 'QUAN_LY'] }
  },
  {
    path: '/bao-cao',
    alias: '/nv/bao-cao',
    name: 'reports',
    component: ReportsView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/quan-ly/phong',
    alias: '/nv/quan-ly/phong',
    name: 'room-admin',
    component: RoomAdminView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/quan-ly/hang-phong',
    alias: '/nv/quan-ly/hang-phong',
    name: 'room-type-admin',
    component: RoomTypeAdminView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/quan-ly/bang-gia',
    alias: '/nv/quan-ly/bang-gia',
    name: 'price-admin',
    component: PriceAdminView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/quan-ly/tham-so',
    alias: ['/nv/quan-ly/tham-so', '/nv/quan-ly/cau-hinh'],
    name: 'setting-admin',
    component: SettingAdminView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/quan-ly/ban-dich',
    alias: ['/nv/quan-ly/ban-dich', '/nv/quan-ly/mau-email'],
    name: 'translation-admin',
    component: TranslationAdminView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/quan-ly/tai-khoan',
    alias: '/nv/quan-ly/tai-khoan',
    name: 'user-admin',
    component: UserAdminView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/nhat-ky',
    alias: '/nv/nhat-ky',
    name: 'audit-logs',
    component: AuditLogsView,
    meta: { requiresAuth: true, roles: ['QUAN_LY'] }
  },
  {
    path: '/he-thong',
    alias: ['/nv/he-thong', '/nv/quan-ly/he-thong'],
    name: 'system-management',
    component: SystemManagementView,
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

// Guard checks auth & role
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      return next({ path: '/dang-nhap', query: { redirect: to.fullPath } });
    }
    
    if (to.meta.roles && !to.meta.roles.includes(authStore.role)) {
      if (authStore.role === 'BUONG_PHONG') {
        return next({ path: '/don-phong' });
      } else {
        return next({ path: '/so-do-phong' });
      }
    }
  }

  if (to.path === '/dang-nhap' && authStore.isAuthenticated) {
    if (authStore.role === 'BUONG_PHONG') {
      return next({ path: '/don-phong' });
    } else {
      return next({ path: '/so-do-phong' });
    }
  }

  next();
});

export default router;
