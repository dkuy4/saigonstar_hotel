<template>
  <div class="max-w-md mx-auto mt-12 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
    <div class="text-center mb-6">
      <div class="w-12 h-12 bg-sky-50 text-sky-600 rounded-2xl mx-auto flex items-center justify-center mb-3 shadow-sm border border-sky-100">
        <LockKeyhole class="w-6 h-6 text-sky-600" />
      </div>
      <h2 class="text-2xl font-bold text-slate-800">Đăng nhập nhân viên</h2>
      <p class="text-xs text-slate-500 mt-1">Dành cho Lễ tân, Buồng phòng và Quản lý</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2.5">
        <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
        <span class="font-medium leading-relaxed">{{ errorMessage }}</span>
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-700 mb-1">Tên đăng nhập</label>
        <input
          v-model="username"
          type="text"
          required
          autocomplete="username"
          class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
          placeholder="Nhập tên đăng nhập"
        />
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-700 mb-1">Mật khẩu</label>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          class="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm text-slate-900 focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition"
          placeholder="Nhập mật khẩu"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-3 px-4 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm rounded-xl shadow-sm transition disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
        <span>{{ loading ? 'Đang xác thực...' : 'Đăng nhập' }}</span>
      </button>
    </form>

    <!-- Quick Role Selection Hints for Testing -->
    <div class="mt-6 pt-6 border-t border-slate-100 space-y-2">
      <div class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-center">
        Tài khoản kiểm thử nhanh theo vai trò
      </div>
      <div class="grid grid-cols-3 gap-2 pt-1">
        <button
          type="button"
          @click="selectAccount('letan', 'LeTan123#')"
          class="p-2 bg-slate-50 hover:bg-sky-50 hover:border-sky-200 border border-slate-200 rounded-xl text-center transition group"
        >
          <span class="block text-xs font-bold text-slate-800 group-hover:text-sky-700">Lễ tân</span>
          <span class="block text-[10px] text-slate-400 font-mono mt-0.5">letan</span>
        </button>

        <button
          type="button"
          @click="selectAccount('buongphong', 'BuongPhong123#')"
          class="p-2 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 border border-slate-200 rounded-xl text-center transition group"
        >
          <span class="block text-xs font-bold text-slate-800 group-hover:text-emerald-700">Buồng phòng</span>
          <span class="block text-[10px] text-slate-400 font-mono mt-0.5">buongphong</span>
        </button>

        <button
          type="button"
          @click="selectAccount('quanly', 'QuanLy123#')"
          class="p-2 bg-slate-50 hover:bg-amber-50 hover:border-amber-200 border border-slate-200 rounded-xl text-center transition group"
        >
          <span class="block text-xs font-bold text-slate-800 group-hover:text-amber-700">Quản lý</span>
          <span class="block text-[10px] text-slate-400 font-mono mt-0.5">quanly</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { LockKeyhole, AlertCircle } from 'lucide-vue-next';
import { useAuthStore } from '../../stores/auth';
import apiClient from '../../api/client';

const router = useRouter();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');

const selectAccount = (u, p) => {
  username.value = u;
  password.value = p;
  errorMessage.value = '';
};

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.post('/auth/login', {
      username: username.value,
      password: password.value
    });
    const userObj = res.user || res.data?.user;
    const tokenStr = res.token || res.data?.token;
    authStore.setAuth(tokenStr, userObj);
    // Redirect based on role
    if (userObj.role === 'BUONG_PHONG') {
      router.push('/nv/don-phong');
    } else {
      router.push('/nv/so-do-phong');
    }
  } catch (err) {
    errorMessage.value = err.message || 'Sai tên đăng nhập hoặc mật khẩu';
  } finally {
    loading.value = false;
  }
};
</script>
