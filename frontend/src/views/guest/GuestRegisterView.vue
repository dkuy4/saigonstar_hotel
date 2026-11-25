<template>
  <div class="max-w-md mx-auto my-12 bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm">
    <div class="text-center mb-8">
      <div class="w-12 h-12 bg-amber-50 text-amber-700 rounded-xl mx-auto flex items-center justify-center mb-3 border border-amber-100">
        <Sparkles class="w-6 h-6" />
      </div>
      <h2 class="text-2xl font-semibold text-slate-900 tracking-tight">Đăng ký thành viên</h2>
      <p class="text-xs text-slate-500 mt-1">Lưu trữ chuyến đi và quản lý phòng đã đặt dễ dàng</p>
    </div>

    <form @submit.prevent="handleRegister" class="space-y-4">
      <div v-if="errorMessage" class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Họ và tên</label>
        <input
          v-model="fullName"
          type="text"
          required
          placeholder="Ví dụ: Nguyễn Văn An"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Số điện thoại liên hệ</label>
        <input
          v-model="phone"
          type="tel"
          required
          placeholder="Ví dụ: 0912345678"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Địa chỉ Email</label>
        <input
          v-model="email"
          type="email"
          required
          placeholder="Ví dụ: ban@email.com"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-slate-700 mb-1.5">Mật khẩu</label>
        <input
          v-model="password"
          type="password"
          required
          minlength="6"
          placeholder="Tối thiểu 6 ký tự"
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 outline-none transition"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs rounded-xl shadow-sm transition disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <div v-if="loading" class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
        <span>{{ loading ? 'Đang tạo tài khoản...' : 'Tạo tài khoản' }}</span>
      </button>
    </form>

    <div class="mt-6 pt-6 border-t border-slate-100 text-center">
      <p class="text-xs text-slate-500">
        Quý khách đã có tài khoản?
        <router-link to="/dang-nhap" class="text-sky-600 hover:text-sky-700 font-semibold ml-1 transition">
          Đăng nhập ngay
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Sparkles, AlertCircle } from 'lucide-vue-next';
import apiClient from '../../api/client';
import { useGuestAuthStore } from '../../stores/guestAuth';

const router = useRouter();
const guestAuth = useGuestAuthStore();

const fullName = ref('');
const phone = ref('');
const email = ref('');
const password = ref('');
const errorMessage = ref('');
const loading = ref(false);

const handleRegister = async () => {
  errorMessage.value = '';
  loading.value = true;
  try {
    const res = await apiClient.post('/guest/register', {
      ho_ten: fullName.value,
      sdt: phone.value,
      email: email.value,
      mat_khau: password.value,
      quoc_tich: 'VNM',
      ngon_ngu: 'vi'
    });

    const token = res?.access_token || res?.data?.access_token;
    const user = res?.user || res?.data?.user;
    if (token) {
      guestAuth.setAuth(token, user);
      router.push('/chuyen-di-cua-toi');
    } else {
      throw new Error('Dữ liệu phản hồi không hợp lệ');
    }
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || err.message || 'Không thể tạo tài khoản. Xin quý khách kiểm tra lại thông tin.';
  } finally {
    loading.value = false;
  }
};
</script>
