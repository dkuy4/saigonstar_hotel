<template>
  <div class="max-w-md mx-auto mt-12 bg-darkbeige-850 p-8 rounded-2xl border border-darkbeige-800 shadow-lg">
    <div class="text-center mb-6">
      <h2 class="font-display text-2xl font-bold text-white tracking-tight">Đăng nhập nhân viên</h2>
      <p class="text-xs text-stone-400 mt-1">Dành cho Lễ tân, Buồng phòng và Quản lý</p>
    </div>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-950/40 border border-rose-800 text-rose-300 text-xs rounded-xl flex items-center space-x-2.5">
        <AlertCircle class="w-4 h-4 text-rose-400 flex-shrink-0" />
        <span class="font-medium leading-relaxed">{{ errorMessage }}</span>
      </div>

      <div>
        <label class="block text-xs font-semibold text-stone-300 mb-1">Tên đăng nhập</label>
        <input
          v-model="username"
          type="text"
          required
          autocomplete="username"
          class="w-full px-3.5 py-2.5 bg-darkbeige-900 border border-darkbeige-700 rounded-xl text-sm text-white focus:ring-2 focus:ring-amberbrown-500 focus:border-amberbrown-500 outline-none transition"
          placeholder="Nhập tên đăng nhập"
        />
      </div>

      <div>
        <label class="block text-xs font-semibold text-stone-300 mb-1">Mật khẩu</label>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          class="w-full px-3.5 py-2.5 bg-darkbeige-900 border border-darkbeige-700 rounded-xl text-sm text-white focus:ring-2 focus:ring-amberbrown-500 focus:border-amberbrown-500 outline-none transition"
          placeholder="Nhập mật khẩu"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-3 px-4 bg-amberbrown-500 hover:bg-amberbrown-600 text-white font-semibold text-sm rounded-xl shadow-sm transition disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
        <span>{{ loading ? 'Đang xác thực...' : 'Đăng nhập' }}</span>
      </button>
    </form>

    <!-- Quick Role Selection Hints for Testing -->
    <div class="mt-6 pt-6 border-t border-darkbeige-800 space-y-2">
      <div class="text-[11px] font-semibold text-stone-500 uppercase tracking-wider text-center">
        Tài khoản kiểm thử nhanh theo vai trò
      </div>
      <div class="grid grid-cols-3 gap-2 pt-1">
        <button
          type="button"
          @click="selectAccount('letan', 'LeTan123#')"
          class="p-2 bg-darkbeige-900 hover:border-amberbrown-500 border border-darkbeige-700 rounded-xl text-center transition"
        >
          <span class="block text-xs font-bold text-[#EDE8DF]">Lễ tân</span>
          <span class="block text-[10px] text-stone-400 font-mono mt-0.5">letan</span>
        </button>

        <button
          type="button"
          @click="selectAccount('buongphong', 'BuongPhong123#')"
          class="p-2 bg-darkbeige-900 hover:border-amberbrown-500 border border-darkbeige-700 rounded-xl text-center transition"
        >
          <span class="block text-xs font-bold text-[#EDE8DF]">Buồng phòng</span>
          <span class="block text-[10px] text-stone-400 font-mono mt-0.5">buongphong</span>
        </button>

        <button
          type="button"
          @click="selectAccount('quanly', 'QuanLy123#')"
          class="p-2 bg-darkbeige-900 hover:border-amberbrown-500 border border-darkbeige-700 rounded-xl text-center transition"
        >
          <span class="block text-xs font-bold text-[#EDE8DF]">Quản lý</span>
          <span class="block text-[10px] text-stone-400 font-mono mt-0.5">quanly</span>
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
