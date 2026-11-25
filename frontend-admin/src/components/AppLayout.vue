<template>
  <div class="min-h-screen flex flex-col bg-slate-100 text-slate-800">
    <!-- Top Header -->
    <header class="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-30 shadow-md">
      <div class="max-w-[1720px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo / Brand -->
        <router-link to="/so-do-phong" class="flex items-center space-x-3 text-white group">
          <div class="w-10 h-10 rounded-lg bg-sky-500 flex items-center justify-center text-white shadow-md group-hover:bg-sky-400 transition">
            <ShieldCheck class="w-5 h-5 fill-white" />
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <h1 class="font-bold text-base leading-tight tracking-tight text-white">{{ t('app.name') }}</h1>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">STAFF PORTAL</span>
            </div>
            <p class="text-xs text-slate-400">Cổng Quản Trị & Nghiệp Vụ Khách Sạn</p>
          </div>
        </router-link>

        <!-- Navigation Links for Staff -->
        <nav v-if="authStore.isAuthenticated" class="hidden md:flex items-center space-x-1">
          <router-link
            v-if="authStore.isReceptionist || authStore.isManager"
            to="/so-do-phong"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('so-do-phong') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            {{ t('nav.roomBoard') }}
          </router-link>
          <router-link
            v-if="authStore.isReceptionist || authStore.isManager"
            to="/don"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('/don') && !$route.path.includes('don-phong') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            {{ t('nav.bookings') }}
          </router-link>
          <router-link
            v-if="authStore.isHousekeeping || authStore.isManager || authStore.isReceptionist"
            to="/don-phong"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('don-phong') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            {{ t('nav.housekeeping') }}
          </router-link>
          <router-link
            v-if="authStore.isReceptionist || authStore.isManager"
            to="/hoan-tien"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('hoan-tien') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            Hoàn tiền
          </router-link>
          <router-link
            v-if="authStore.isReceptionist || authStore.isManager"
            to="/doi-soat"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('doi-soat') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            Đối soát
          </router-link>
          <router-link
            v-if="authStore.isManager"
            to="/bao-cao"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('bao-cao') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            {{ t('nav.reports') }}
          </router-link>
          <router-link
            v-if="authStore.isManager"
            to="/nhat-ky"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('nhat-ky') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            Nhật ký
          </router-link>
          <router-link
            v-if="authStore.isManager"
            to="/he-thong"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('he-thong') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            Hệ thống
          </router-link>
          <router-link
            v-if="authStore.isManager"
            to="/quan-ly/phong"
            class="px-3 py-2 rounded-md text-xs font-semibold transition"
            :class="$route.path.includes('quan-ly') ? 'text-sky-400 bg-slate-800' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'"
          >
            {{ t('nav.management') }}
          </router-link>
        </nav>

        <!-- Right Side Actions: Language Selector & Auth -->
        <div class="flex items-center space-x-3">
          <!-- Language Selector -->
          <select
            v-model="currentLang"
            @change="changeLanguage"
            class="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:ring-sky-500 focus:border-sky-500 outline-none"
          >
            <option value="vi">🇻🇳 Tiếng Việt</option>
            <option value="en">🇬🇧 English</option>
          </select>

          <!-- Staff Account State -->
          <div v-if="authStore.isAuthenticated" class="flex items-center space-x-3 border-l border-slate-800 pl-3">
            <div class="text-right hidden sm:block">
              <p class="text-xs font-semibold text-white">{{ authStore.user?.full_name || authStore.user?.username }}</p>
              <p class="text-[10px] text-amber-400 font-mono font-medium">{{ authStore.user?.role }}</p>
            </div>
            <button
              @click="handleLogout"
              class="px-3 py-1.5 text-xs font-medium text-rose-300 hover:bg-rose-950/40 border border-rose-800/60 rounded-md transition"
            >
              {{ t('nav.logout') }}
            </button>
          </div>
          <router-link
            v-else
            to="/dang-nhap"
            class="px-3 py-1.5 text-xs font-medium text-slate-200 hover:text-white hover:bg-slate-800 border border-slate-700 rounded-md transition"
          >
            {{ t('nav.login') }}
          </router-link>
        </div>
      </div>
    </header>

    <!-- Main Content Slot -->
    <main class="flex-1 max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
      <div class="max-w-[1720px] mx-auto px-4 space-y-1">
        <p class="font-medium text-slate-600">{{ t('footer.copyright', { name: t('app.name') }) }} - Cổng Quản Trị Nhân Viên</p>
        <p class="text-[11px] text-slate-400">Phiên bản nội bộ 1.1 - Bảo mật & Phân quyền theo vai trò</p>
      </div>
    </footer>

    <!-- Mandatory Password Change Modal (F17 Rule 5) -->
    <div
      v-if="authStore.isAuthenticated && authStore.user?.phaiDoiMatKhau"
      class="fixed inset-0 z-[9999] bg-slate-900/70 backdrop-blur-md flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full overflow-hidden p-6 space-y-4 animate-in fade-in zoom-in-95 duration-200">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shadow-sm">
            <Lock class="w-5 h-5 text-amber-700" />
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900">Yêu cầu đổi mật khẩu lần đầu</h3>
            <p class="text-xs text-slate-500 font-mono">{{ authStore.user?.username }}</p>
          </div>
        </div>

        <p class="text-xs text-slate-600 leading-relaxed">
          Tài khoản của bạn đang dùng mật khẩu tạm thời hoặc vừa được quản lý đặt lại mật khẩu. Bạn bắt buộc phải thiết lập mật khẩu mới (tối thiểu 8 ký tự) để tiếp tục sử dụng hệ thống.
        </p>

        <div v-if="pwdChangeError" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{{ pwdChangeError }}</span>
        </div>

        <form @submit.prevent="submitMandatoryPasswordChange" class="space-y-3">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Mật khẩu hiện tại (mật khẩu tạm)</label>
            <input
              v-model="pwdCurrent"
              type="password"
              required
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none"
              placeholder="Nhập mật khẩu tạm hiện tại"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Mật khẩu mới</label>
            <input
              v-model="pwdNew"
              type="password"
              required
              minlength="8"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none"
              placeholder="Tối thiểu 8 ký tự"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Xác nhận mật khẩu mới</label>
            <input
              v-model="pwdConfirm"
              type="password"
              required
              minlength="8"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none"
              placeholder="Nhập lại mật khẩu mới"
            />
          </div>

          <div class="pt-2 flex justify-end space-x-2">
            <button
              type="button"
              @click="handleLogout"
              class="px-4 py-2 border border-slate-200 text-slate-600 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
            >
              Đăng xuất
            </button>
            <button
              type="submit"
              :disabled="pwdChangeSubmitting"
              class="px-4 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold hover:bg-sky-700 shadow-md transition disabled:opacity-50"
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
import { ShieldCheck, Lock, AlertCircle } from 'lucide-vue-next';
import { useAuthStore } from '../stores/auth';
import apiClient from '../api/client';

const { t, locale } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

const currentLang = ref(locale.value);

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
