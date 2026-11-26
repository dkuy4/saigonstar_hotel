<template>
  <div class="min-h-screen flex flex-col bg-darkbeige-950 text-[#EDE8DF] antialiased font-sans">
    <!-- Top Bar -->
    <header class="bg-darkbeige-900/95 backdrop-blur-sm border-b border-darkbeige-800 sticky top-0 z-40 h-14 flex items-center justify-between px-4 sm:px-6">
      <!-- Left: Sidebar Toggle + Brand -->
      <div class="flex items-center space-x-3">
        <button
          v-if="authStore.isAuthenticated"
          @click="toggleSidebar"
          class="p-2 rounded-lg text-stone-400 hover:text-white hover:bg-darkbeige-800 transition"
          :title="t('nav.toggleSidebar')"
        >
          <Menu class="w-5 h-5 md:hidden" />
          <PanelLeftClose v-if="!sidebarCollapsed" class="w-4 h-4 hidden md:block" />
          <PanelLeftOpen v-else class="w-4 h-4 hidden md:block" />
        </button>

        <router-link to="/so-do-phong" class="flex items-center space-x-2.5 text-white">
          <div class="w-8 h-8 rounded-lg bg-amberbrown-500 flex items-center justify-center text-white shadow-sm">
            <ShieldCheck class="w-4 h-4" />
          </div>
          <div class="flex items-center space-x-2">
            <h1 class="font-display font-bold text-lg leading-tight tracking-tight text-white">
              {{ t('app.name') }}
            </h1>
            <span class="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30">
              {{ t('app.portal') }}
            </span>
          </div>
        </router-link>
      </div>

      <!-- Right Actions: Language Selector & Staff Account -->
      <div class="flex items-center space-x-2.5">
        <select
          v-model="currentLang"
          @change="changeLanguage"
          class="bg-darkbeige-850 border border-darkbeige-700 text-stone-200 text-xs rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-amberbrown-500 outline-none"
        >
          <option value="vi">🇻🇳 Tiếng Việt</option>
          <option value="en">🇬🇧 English</option>
        </select>

        <div v-if="authStore.isAuthenticated" class="flex items-center space-x-3 border-l border-darkbeige-800 pl-3">
          <div class="text-right hidden sm:block">
            <p class="text-xs font-semibold text-[#EDE8DF]">{{ authStore.user?.full_name || authStore.user?.username }}</p>
            <p class="text-[10px] text-amberbrown-400 font-mono font-medium">{{ authStore.user?.role }}</p>
          </div>
          <button
            @click="handleLogout"
            class="px-2.5 py-1.5 text-xs font-medium text-rose-300 hover:bg-rose-950/40 border border-rose-800/60 rounded-lg transition"
          >
            {{ t('nav.logout') }}
          </button>
        </div>
        <router-link
          v-else
          to="/dang-nhap"
          class="px-3 py-1.5 text-xs font-medium text-stone-200 hover:text-white bg-darkbeige-850 hover:bg-darkbeige-800 border border-darkbeige-700 rounded-lg transition"
        >
          {{ t('nav.login') }}
        </router-link>
      </div>
    </header>

    <!-- Body: Collapsible Sidebar + Main Content -->
    <div class="flex-1 flex relative">
      <!-- Mobile Overlay -->
      <div
        v-if="authStore.isAuthenticated && mobileMenuOpen"
        @click="mobileMenuOpen = false"
        class="fixed inset-0 bg-black/60 z-30 md:hidden"
      ></div>

      <!-- Left Sidebar -->
      <aside
        v-if="authStore.isAuthenticated"
        class="fixed md:sticky top-14 left-0 z-30 h-[calc(100vh-3.5rem)] bg-darkbeige-900 border-r border-darkbeige-800 flex flex-col justify-between transition-all duration-200 overflow-y-auto"
        :class="[
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
          sidebarCollapsed ? 'md:w-16 w-60' : 'w-60'
        ]"
      >
        <nav class="p-3 space-y-5 text-xs">
          <!-- Group 1: Operations -->
          <div class="space-y-1">
            <p v-if="!sidebarCollapsed" class="px-3 text-[10px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
              {{ t('nav.groupOperations') }}
            </p>
            <router-link
              v-if="authStore.isReceptionist || authStore.isManager"
              to="/so-do-phong"
              @click="mobileMenuOpen = false"
              :title="t('nav.roomBoard')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('so-do-phong') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <LayoutGrid class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.roomBoard') }}</span>
            </router-link>

            <router-link
              v-if="authStore.isReceptionist || authStore.isManager"
              to="/don"
              @click="mobileMenuOpen = false"
              :title="t('nav.bookings')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path === '/don' || ($route.path.startsWith('/don/') && !$route.path.includes('moi')) ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <ClipboardList class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.bookings') }}</span>
            </router-link>

            <router-link
              v-if="authStore.isReceptionist || authStore.isManager"
              to="/don/moi"
              @click="mobileMenuOpen = false"
              :title="t('nav.createBooking')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('/don/moi') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <PlusSquare class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.createBooking') }}</span>
            </router-link>

            <router-link
              v-if="authStore.isHousekeeping || authStore.isManager || authStore.isReceptionist"
              to="/don-phong"
              @click="mobileMenuOpen = false"
              :title="t('nav.housekeeping')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('don-phong') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <Sparkles class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.housekeeping') }}</span>
            </router-link>
          </div>

          <!-- Group 2: Finance & Audit -->
          <div v-if="authStore.isReceptionist || authStore.isManager" class="space-y-1">
            <p v-if="!sidebarCollapsed" class="px-3 text-[10px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
              {{ t('nav.groupFinance') }}
            </p>
            <router-link
              to="/hoan-tien"
              @click="mobileMenuOpen = false"
              :title="t('nav.refunds')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('hoan-tien') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <RotateCcw class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.refunds') }}</span>
            </router-link>

            <router-link
              to="/doi-soat"
              @click="mobileMenuOpen = false"
              :title="t('nav.reconciliation')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('doi-soat') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <Scale class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.reconciliation') }}</span>
            </router-link>

            <router-link
              v-if="authStore.isManager"
              to="/bao-cao"
              @click="mobileMenuOpen = false"
              :title="t('nav.reports')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('bao-cao') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <BarChart3 class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.reports') }}</span>
            </router-link>
          </div>

          <!-- Group 3: Administration -->
          <div v-if="authStore.isManager" class="space-y-1">
            <p v-if="!sidebarCollapsed" class="px-3 text-[10px] font-bold uppercase tracking-wider text-stone-500 mb-1.5">
              {{ t('nav.groupAdmin') }}
            </p>
            <router-link
              to="/quan-ly/phong"
              @click="mobileMenuOpen = false"
              :title="t('nav.management')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('quan-ly') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <Settings class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.management') }}</span>
            </router-link>

            <router-link
              to="/nhat-ky"
              @click="mobileMenuOpen = false"
              :title="t('nav.auditLogs')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('nhat-ky') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <FileText class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.auditLogs') }}</span>
            </router-link>

            <router-link
              to="/he-thong"
              @click="mobileMenuOpen = false"
              :title="t('nav.system')"
              class="flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition"
              :class="$route.path.includes('he-thong') ? 'bg-amberbrown-500/20 text-amberbrown-300 border border-amberbrown-500/30' : 'text-stone-400 hover:text-white hover:bg-darkbeige-850'"
            >
              <Server class="w-4 h-4 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="truncate">{{ t('nav.system') }}</span>
            </router-link>
          </div>
        </nav>

        <div v-if="!sidebarCollapsed" class="p-3 border-t border-darkbeige-800 text-[10px] text-stone-500">
          {{ t('app.subtitle') }}
        </div>
      </aside>

      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col min-w-0">
        <main class="flex-1 w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <slot />
        </main>

        <!-- Footer -->
        <footer class="bg-darkbeige-900 border-t border-darkbeige-800 py-4 text-center text-xs text-stone-500">
          <div class="max-w-[1600px] mx-auto px-4 space-y-1">
            <p class="font-medium text-stone-400">{{ t('footer.copyright') }}</p>
            <p class="text-[11px] text-stone-500">{{ t('footer.version') }}</p>
          </div>
        </footer>
      </div>
    </div>

    <!-- Mandatory Password Change Modal (F17 Rule 5) -->
    <div
      v-if="authStore.isAuthenticated && authStore.user?.phaiDoiMatKhau"
      class="fixed inset-0 z-[9999] bg-black/75 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-darkbeige-850 rounded-2xl border border-darkbeige-700 shadow-2xl max-w-md w-full overflow-hidden p-6 space-y-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-amberbrown-500/20 text-amberbrown-300 flex items-center justify-center">
            <Lock class="w-5 h-5" />
          </div>
          <div>
            <h3 class="font-display text-base font-bold text-white">Yêu cầu đổi mật khẩu lần đầu</h3>
            <p class="text-xs text-stone-400 font-mono">{{ authStore.user?.username }}</p>
          </div>
        </div>

        <p class="text-xs text-stone-400 leading-relaxed">
          Tài khoản của bạn đang dùng mật khẩu tạm thời hoặc vừa được quản lý đặt lại mật khẩu. Bạn bắt buộc phải thiết lập mật khẩu mới (tối thiểu 8 ký tự) để tiếp tục sử dụng hệ thống.
        </p>

        <div v-if="pwdChangeError" class="p-3 bg-rose-950/40 border border-rose-800 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{{ pwdChangeError }}</span>
        </div>

        <form @submit.prevent="submitMandatoryPasswordChange" class="space-y-3">
          <div>
            <label class="block text-xs font-semibold text-stone-300 mb-1">Mật khẩu hiện tại (mật khẩu tạm)</label>
            <input
              v-model="pwdCurrent"
              type="password"
              required
              class="w-full px-3.5 py-2.5 bg-darkbeige-900 border border-darkbeige-700 rounded-xl text-xs text-white focus:ring-2 focus:ring-amberbrown-500 outline-none"
              placeholder="Nhập mật khẩu tạm hiện tại"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-300 mb-1">Mật khẩu mới</label>
            <input
              v-model="pwdNew"
              type="password"
              required
              minlength="8"
              class="w-full px-3.5 py-2.5 bg-darkbeige-900 border border-darkbeige-700 rounded-xl text-xs text-white focus:ring-2 focus:ring-amberbrown-500 outline-none"
              placeholder="Tối thiểu 8 ký tự"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-300 mb-1">Xác nhận mật khẩu mới</label>
            <input
              v-model="pwdConfirm"
              type="password"
              required
              minlength="8"
              class="w-full px-3.5 py-2.5 bg-darkbeige-900 border border-darkbeige-700 rounded-xl text-xs text-white focus:ring-2 focus:ring-amberbrown-500 outline-none"
              placeholder="Nhập lại mật khẩu mới"
            />
          </div>

          <div class="pt-2 flex justify-end space-x-2">
            <button
              type="button"
              @click="handleLogout"
              class="px-4 py-2 border border-darkbeige-700 text-stone-300 rounded-xl text-xs font-semibold hover:bg-darkbeige-800 transition"
            >
              {{ t('nav.logout') }}
            </button>
            <button
              type="submit"
              :disabled="pwdChangeSubmitting"
              class="px-4 py-2 bg-amberbrown-500 text-white rounded-xl text-xs font-semibold hover:bg-amberbrown-600 shadow-md transition disabled:opacity-50"
            >
              {{ pwdChangeSubmitting ? 'Đang lưu...' : 'Lưu mật khẩu & Tiếp tục' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import {
  ShieldCheck, Lock, AlertCircle, Menu, PanelLeftClose, PanelLeftOpen,
  LayoutGrid, ClipboardList, PlusSquare, Sparkles, RotateCcw, Scale,
  BarChart3, Settings, FileText, Server
} from 'lucide-vue-next';
import { useAuthStore } from '../stores/auth';
import apiClient from '../api/client';

const { t, locale } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

const currentLang = ref(locale.value);
const sidebarCollapsed = ref(false);
const mobileMenuOpen = ref(false);

const toggleSidebar = () => {
  if (window.innerWidth < 768) {
    mobileMenuOpen.value = !mobileMenuOpen.value;
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value;
  }
};

const changeLanguage = () => {
  locale.value = currentLang.value;
  localStorage.setItem('lang', currentLang.value);
};

const handleLogout = () => {
  authStore.logout();
  router.push('/dang-nhap');
};

// Mandatory Password Change Handling
const pwdCurrent = ref('');
const pwdNew = ref('');
const pwdConfirm = ref('');
const pwdChangeError = ref('');
const pwdChangeSubmitting = ref(false);

const submitMandatoryPasswordChange = async () => {
  pwdChangeError.value = '';
  if (pwdNew.value !== pwdConfirm.value) {
    pwdChangeError.value = 'Mật khẩu mới và xác nhận mật khẩu không khớp.';
    return;
  }
  if (pwdNew.value.length < 8) {
    pwdChangeError.value = 'Mật khẩu mới phải có tối thiểu 8 ký tự.';
    return;
  }

  pwdChangeSubmitting.value = true;
  try {
    await apiClient.post('/auth/change-password', {
      current_password: pwdCurrent.value,
      new_password: pwdNew.value
    });

    if (authStore.user) {
      authStore.user.phaiDoiMatKhau = false;
      localStorage.setItem('user', JSON.stringify(authStore.user));
    }
  } catch (err) {
    pwdChangeError.value = err.response?.data?.detail || 'Không thể đổi mật khẩu. Vui lòng kiểm tra lại mật khẩu tạm.';
  } finally {
    pwdChangeSubmitting.value = false;
  }
};
</script>
