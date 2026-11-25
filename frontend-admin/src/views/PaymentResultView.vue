<template>
  <div class="max-w-xl mx-auto py-12 px-4">
    <div class="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 text-center">
      
      <!-- 1. XAC_NHAN (Thành công chuẩn) -->
      <div v-if="result === 'XAC_NHAN'">
        <div class="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Thanh toán thành công!</h2>
        <p class="text-gray-600 text-sm mb-6">
          Đơn đặt phòng của quý khách đã được xác nhận. Email xác nhận chi tiết đã được gửi đến hòm thư của bạn.
        </p>
      </div>

      <!-- 2. XAC_NHAN_MUON (Thanh toán về muộn nhưng còn phòng) -->
      <div v-else-if="result === 'XAC_NHAN_MUON'">
        <div class="w-16 h-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Xác nhận thanh toán (Ghi nhận muộn)</h2>
        <p class="text-gray-600 text-sm mb-6">
          Giao dịch thanh toán được ghi nhận sau khi hết hạn 15 phút giữ chỗ. Rất may mắn phòng vẫn còn trống nên hệ thống đã khôi phục và xác nhận thành công đơn cho quý khách.
        </p>
      </div>

      <!-- 3. HOAN_TIEN (Thanh toán muộn & phòng đã bị chiếm lại) -->
      <div v-else-if="result === 'HOAN_TIEN'">
        <div class="w-16 h-16 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Đang hoàn tiền (Phòng đã hết)</h2>
        <p class="text-gray-600 text-sm mb-6">
          Giao dịch hoàn tất sau hạn giữ chỗ và phòng đã được khách khác đặt trước. Hệ thống đã tự động kích hoạt hoàn tiền 100% về tài khoản ban đầu theo quy định BR-19.
        </p>
      </div>

      <!-- 4. THAT_BAI (Thất bại hoặc hủy) -->
      <div v-else-if="result === 'THAT_BAI'">
        <div class="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Thanh toán không thành công</h2>
        <p class="text-gray-600 text-sm mb-6">
          Giao dịch đã bị hủy hoặc không thể hoàn tất. Đơn giữ chỗ của quý khách đã bị hủy giải phóng phòng.
        </p>
      </div>

      <!-- 5. DA_XU_LY hoặc khác -->
      <div v-else>
        <div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Giao dịch đã được ghi nhận</h2>
        <p class="text-gray-600 text-sm mb-6">
          Giao dịch này đã được hệ thống xử lý trước đó. Quý khách vui lòng kiểm tra trạng thái đơn đặt phòng.
        </p>
      </div>

      <!-- Details Block -->
      <div v-if="bookingCode || refCode" class="bg-gray-50 rounded-xl p-4 text-left text-sm mb-6 space-y-2 border border-gray-100">
        <div v-if="bookingCode" class="flex justify-between">
          <span class="text-gray-500">Mã đơn đặt phòng:</span>
          <span class="font-mono font-bold text-gray-900">{{ bookingCode }}</span>
        </div>
        <div v-if="refCode" class="flex justify-between">
          <span class="text-gray-500">Mã giao dịch cổng:</span>
          <span class="font-mono text-gray-700">{{ refCode }}</span>
        </div>
      </div>

      <!-- Navigation Actions -->
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <router-link
          v-if="bookingCode && result !== 'THAT_BAI'"
          :to="`/don/${bookingCode}`"
          class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow transition"
        >
          Xem chi tiết đơn phòng
        </router-link>

        <router-link
          to="/"
          class="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl transition"
        >
          Trang chủ
        </router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const result = computed(() => route.query.result || 'UNKNOWN');
const bookingCode = computed(() => route.query.code || '');
const refCode = computed(() => route.query.ref || '');
</script>
