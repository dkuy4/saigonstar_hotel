<template>
  <div class="max-w-xl mx-auto py-10 px-4">
    <div class="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
      <!-- Header -->
      <div class="bg-gradient-to-r from-blue-700 to-indigo-800 text-white p-6 text-center">
        <div class="inline-flex items-center justify-center w-12 h-12 bg-white/20 rounded-full mb-3">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold tracking-tight">Cổng thanh toán giả lập</h1>
        <p class="text-blue-100 text-xs mt-1 uppercase tracking-wider font-semibold">Sandbox Payment Gateway (Mock)</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="p-12 text-center text-gray-500">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p class="text-sm">Đang tải thông tin giao dịch...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="p-8 text-center">
        <div class="inline-flex items-center justify-center w-12 h-12 bg-red-100 text-red-600 rounded-full mb-3">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Không thể tải giao dịch</h3>
        <p class="text-gray-600 text-sm mb-6">{{ error }}</p>
        <router-link to="/" class="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition">
          Quay về trang chủ
        </router-link>
      </div>

      <!-- Content -->
      <div v-else-if="info" class="p-6">
        <!-- Amount Banner -->
        <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 text-center mb-6">
          <div class="text-xs text-blue-600 font-semibold uppercase tracking-wider">Số tiền thanh toán</div>
          <div class="text-3xl font-extrabold text-blue-900 mt-1">
            <MoneyText :amount="info.so_tien || info.amount" />
          </div>
        </div>

        <!-- Details -->
        <div class="space-y-3 mb-6 text-sm">
          <div class="flex justify-between py-2 border-b border-gray-100">
            <span class="text-gray-500">Mã giao dịch (Ref)</span>
            <span class="font-mono font-medium text-gray-800">{{ info.reference_code }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-100">
            <span class="text-gray-500">Mã đơn đặt phòng</span>
            <span class="font-mono font-bold text-blue-700">{{ info.ma_dat_phong }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-100">
            <span class="text-gray-500">Khách hàng</span>
            <span class="font-medium text-gray-800">{{ info.ten_khach || 'Khách vãng lai' }}</span>
          </div>
          <div class="flex justify-between py-2">
            <span class="text-gray-500">Trạng thái hiện tại</span>
            <span class="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
              {{ info.trang_thai }}
            </span>
          </div>
        </div>

        <div class="bg-gray-50 rounded-xl p-4 mb-6 border border-gray-200">
          <div class="text-xs font-semibold text-gray-600 uppercase mb-2">Môi trường thử nghiệm</div>
          <p class="text-xs text-gray-500 leading-relaxed">
            Đây là cổng thanh toán mô phỏng phục vụ đồ án hệ quản trị CSDL. Dữ liệu chữ ký số HMAC-SHA256 được mã hóa tự động để xác thực callback.
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-3">
          <button
            @click="submitPayment(true)"
            :disabled="processing"
            class="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <svg v-if="!processing" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
            <span>Xác nhận thanh toán thành công</span>
          </button>

          <button
            @click="submitPayment(false)"
            :disabled="processing"
            class="w-full py-3.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span>Hủy / Mô phỏng thanh toán thất bại</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../api/client';
import MoneyText from '../components/MoneyText.vue';

const route = useRoute();
const router = useRouter();

const info = ref(null);
const signatures = ref({});
const loading = ref(true);
const processing = ref(false);
const error = ref('');

const loadInfo = async () => {
  loading.value = true;
  error.value = '';
  try {
    const res = await apiClient.get(`/payments/mock-info/${route.params.ref}`);
    info.value = res.info;
    signatures.value = res.signatures || {};
  } catch (err) {
    error.value = err.message || 'Không thể tìm thấy giao dịch';
  } finally {
    loading.value = false;
  }
};

const submitPayment = async (isSuccess) => {
  if (processing.value || !info.value) return;
  processing.value = true;
  const sig = isSuccess ? signatures.value.success : signatures.value.fail;

  try {
    const res = await apiClient.post('/payments/callback', {
      reference_code: info.value.reference_code,
      is_success: isSuccess,
      signature: sig
    });

    router.push({
      path: '/thanh-toan/ket-qua',
      query: {
        result: res.result,
        code: info.value.ma_dat_phong,
        ref: info.value.reference_code
      }
    });
  } catch (err) {
    alert(err.message || 'Xử lý kết quả thanh toán thất bại');
  } finally {
    processing.value = false;
  }
};

onMounted(loadInfo);
</script>
