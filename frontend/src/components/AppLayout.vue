<template>
  <div class="min-h-screen flex flex-col bg-slate-50 text-slate-800 antialiased font-sans">
    <!-- Top Header for Guests (Quiet Chrome, Unslop) -->
    <header class="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo / Brand -->
        <router-link to="/" class="flex items-center space-x-3 text-slate-900 group">
          <div class="w-9 h-9 rounded-xl bg-sky-700 flex items-center justify-center text-white shadow-sm group-hover:bg-sky-800 transition">
            <Star class="w-4 h-4 fill-white" />
          </div>
          <div>
            <h1 class="font-bold text-base leading-tight tracking-tight text-slate-900">Khách sạn Sài Gòn Star</h1>
            <p class="text-[11px] text-slate-500 font-normal">Dịch vụ lưu trú & nghỉ dưỡng tiêu chuẩn</p>
          </div>
        </router-link>

        <!-- Guest Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1">
          <router-link
            to="/"
            class="px-3 py-2 rounded-xl text-xs font-medium transition"
            :class="$route.path === '/' ? 'text-sky-700 bg-sky-50 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
          >
            Tìm phòng
          </router-link>

          <router-link
            v-if="guestAuth.isLoggedIn"
            to="/chuyen-di-cua-toi"
            class="px-3 py-2 rounded-xl text-xs font-medium transition"
            :class="$route.path.includes('chuyen-di') ? 'text-sky-700 bg-sky-50 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
          >
            Chuyến đi của tôi
          </router-link>

          <router-link
            to="/don/tra-cuu"
            class="px-3 py-2 rounded-xl text-xs font-medium transition"
            :class="$route.path.startsWith('/don') ? 'text-sky-700 bg-sky-50 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
          >
            Tra cứu đơn phòng
          </router-link>
        </nav>

        <!-- Right Actions: Language Selector + Guest Account + Link to Staff Portal -->
        <div class="flex items-center space-x-2.5">
          <!-- 7 Languages Selector -->
          <select
            v-model="currentLang"
            @change="changeLanguage"
            class="bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl px-2.5 py-1.5 focus:ring-2 focus:ring-sky-500 outline-none"
          >
            <option value="vi">🇻🇳 Tiếng Việt</option>
            <option value="en">🇬🇧 English</option>
            <option value="zh-CN">🇨🇳 中文</option>
            <option value="ko">🇰🇷 한국어</option>
            <option value="ja">🇯🇵 日本語</option>
            <option value="es">🇪🇸 Español</option>
            <option value="fr">🇫🇷 Français</option>
          </select>

          <!-- Guest Account Area -->
          <template v-if="guestAuth.isLoggedIn">
            <div class="flex items-center space-x-2 border-l border-slate-200 pl-2.5">
              <router-link
                to="/chuyen-di-cua-toi"
                class="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl hover:bg-slate-100 text-xs font-medium text-slate-800 transition"
              >
                <User class="w-3.5 h-3.5 text-sky-700" />
                <span class="max-w-[120px] truncate">{{ guestAuth.guestName }}</span>
              </router-link>
              <button
                @click="handleLogout"
                class="px-2.5 py-1.5 text-xs text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-xl transition font-medium"
                title="Đăng xuất khỏi tài khoản"
              >
                Đăng xuất
              </button>
            </div>
          </template>

          <template v-else>
            <div class="flex items-center space-x-1.5 border-l border-slate-200 pl-2.5">
              <router-link
                to="/dang-nhap"
                class="px-3 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition"
              >
                Đăng nhập
              </router-link>
              <router-link
                to="/dang-ky"
                class="px-3 py-1.5 text-xs font-semibold text-white bg-sky-700 hover:bg-sky-800 rounded-xl shadow-sm transition"
              >
                Đăng ký
              </router-link>
            </div>
          </template>

          <!-- Discreet Internal Staff Portal Link -->
          <a
            href="http://127.0.0.1:5174/dang-nhap"
            target="_blank"
            class="hidden lg:flex items-center space-x-1 px-2.5 py-1.5 text-[11px] font-medium text-slate-400 hover:text-slate-700 hover:bg-slate-100 border border-slate-200 rounded-xl transition"
            title="Dành riêng cho nhân viên khách sạn"
          >
            <Building2 class="w-3.5 h-3.5" />
            <span>Nội bộ</span>
          </a>
        </div>
      </div>
    </header>

    <!-- Main Content Slot -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-8 text-center text-xs text-slate-500">
      <div class="max-w-7xl mx-auto px-4 space-y-2">
        <div class="flex items-center justify-center space-x-2 text-slate-700 font-medium">
          <Star class="w-4 h-4 fill-sky-700 text-sky-700" />
          <span>Khách sạn Sài Gòn Star</span>
        </div>
        <p class="text-xs text-slate-500">Địa chỉ: 123 Đường Nguyễn Thị Minh Khai, Quận 1, TP. Hồ Chí Minh</p>
        <p class="text-[11px] text-slate-400 pt-1">
          Hỗ trợ khách hàng 24/7 • Đặt phòng trực tuyến nhanh chóng và thuận tiện
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Star, User, Building2 } from 'lucide-vue-next';
import { useGuestAuthStore } from '../stores/guestAuth';

const { locale } = useI18n();
const router = useRouter();
const guestAuth = useGuestAuthStore();

const currentLang = ref(locale.value);

const changeLanguage = () => {
  locale.value = currentLang.value;
  localStorage.setItem('lang', currentLang.value);
};

const handleLogout = () => {
  guestAuth.logout();
  router.push('/');
};
</script>
