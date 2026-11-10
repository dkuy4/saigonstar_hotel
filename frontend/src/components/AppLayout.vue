<template>
  <div class="min-h-screen flex flex-col bg-slate-50 text-slate-800">
    <!-- Top Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo / Brand -->
        <router-link to="/" class="flex items-center space-x-3 text-slate-900 group">
          <div class="w-10 h-10 rounded-lg bg-sky-600 flex items-center justify-center text-white font-bold text-xl shadow-md group-hover:bg-sky-700 transition">
            ★
          </div>
          <div>
            <h1 class="font-bold text-lg leading-tight tracking-tight text-slate-900">{{ t('app.name') }}</h1>
            <p class="text-xs text-slate-500">{{ t('app.subtitle') }}</p>
          </div>
        </router-link>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1">
          <!-- Guest Navigation -->
          <template v-if="!authStore.isStaff">
            <router-link
              to="/"
              class="px-3 py-2 rounded-md text-sm font-medium transition"
              :class="$route.path === '/' ? 'text-sky-600 bg-sky-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
            >
              {{ t('nav.search') }}
            </router-link>
            <router-link
              to="/don/tra-cuu"
              class="px-3 py-2 rounded-md text-sm font-medium transition"
              :class="$route.path.startsWith('/don') ? 'text-sky-600 bg-sky-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
            >
              {{ t('nav.lookup') }}
            </router-link>
          </template>

          <!-- Staff Navigation (Role-based) -->
          <template v-else>
            <router-link
              v-if="authStore.isReceptionist || authStore.isManager"
              to="/nv/so-do-phong"
              class="px-3 py-2 rounded-md text-sm font-medium transition"
              :class="$route.path.includes('so-do-phong') ? 'text-sky-600 bg-sky-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
            >
              {{ t('nav.roomBoard') }}
            </router-link>
            <router-link
              v-if="authStore.isReceptionist || authStore.isManager"
              to="/nv/don"
              class="px-3 py-2 rounded-md text-sm font-medium transition"
              :class="$route.path.includes('/nv/don') ? 'text-sky-600 bg-sky-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
            >
              {{ t('nav.bookings') }}
            </router-link>
            <router-link
              v-if="authStore.isHousekeeping || authStore.isManager"
              to="/nv/don-phong"
              class="px-3 py-2 rounded-md text-sm font-medium transition"
              :class="$route.path.includes('don-phong') ? 'text-sky-600 bg-sky-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
            >
              {{ t('nav.housekeeping') }}
            </router-link>
            <router-link
              v-if="authStore.isManager"
              to="/nv/bao-cao"
              class="px-3 py-2 rounded-md text-sm font-medium transition"
              :class="$route.path.includes('bao-cao') ? 'text-sky-600 bg-sky-50' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'"
            >
              {{ t('nav.reports') }}
            </router-link>
          </template>
        </nav>

        <!-- Right Side Actions: Language Selector & Auth -->
        <div class="flex items-center space-x-3">
          <!-- Language Selector -->
          <select
            v-model="currentLang"
            @change="changeLanguage"
            class="bg-slate-50 border border-slate-300 text-slate-700 text-xs rounded-lg px-2.5 py-1.5 focus:ring-sky-500 focus:border-sky-500 outline-none"
          >
            <option value="vi">🇻🇳 Tiếng Việt</option>
            <option value="en">🇬🇧 English</option>
          </select>

          <!-- Staff Account State -->
          <div v-if="authStore.isAuthenticated" class="flex items-center space-x-3 border-l border-slate-200 pl-3">
            <div class="text-right hidden sm:block">
              <p class="text-xs font-semibold text-slate-900">{{ authStore.user?.full_name || authStore.user?.username }}</p>
              <p class="text-[10px] text-slate-500 font-mono">{{ authStore.user?.role }}</p>
            </div>
            <button
              @click="handleLogout"
              class="px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 border border-rose-200 rounded-md transition"
            >
              {{ t('nav.logout') }}
            </button>
          </div>
          <router-link
            v-else
            to="/nv/dang-nhap"
            class="px-3 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 border border-slate-300 rounded-md transition"
          >
            {{ t('nav.login') }}
          </router-link>
        </div>
      </div>
    </header>

    <!-- Main Content Slot -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
      <div class="max-w-7xl mx-auto px-4">
        &copy; 2026 {{ t('app.name') }}. Môn học Các hệ quản trị cơ sở dữ liệu — Oracle 23ai & FastAPI.
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/auth';

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

const currentLang = ref(authStore.language);

const changeLanguage = () => {
  authStore.setLanguage(currentLang.value);
};

const handleLogout = () => {
  authStore.logout();
  router.push('/nv/dang-nhap');
};
</script>
