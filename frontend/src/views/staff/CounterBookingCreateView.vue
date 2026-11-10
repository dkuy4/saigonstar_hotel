<template>
  <div class="max-w-4xl mx-auto space-y-6 pb-12">
    <!-- Breadcrumb & Header -->
    <div class="flex items-center justify-between pb-4 border-b border-slate-200">
      <div class="space-y-1">
        <div class="flex items-center space-x-2 text-xs text-slate-500">
          <router-link to="/nv/don" class="hover:text-sky-600 transition">Quản lý đơn</router-link>
          <span>/</span>
          <span class="text-slate-800 font-semibold">Tạo đơn tại quầy</span>
        </div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">Tiếp nhận đặt phòng tại quầy</h1>
      </div>
      <router-link
        to="/nv/don"
        class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
      >
        ← Quay lại danh sách
      </router-link>
    </div>

    <!-- Error Alert -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center space-x-2">
      <span class="text-lg">⚠️</span>
      <div class="flex-1">
        <div class="font-bold">Không thể tạo đơn:</div>
        <div>{{ errorMessage }}</div>
        
        <!-- Suggested Rooms if ROOM_CONFLICT -->
        <div v-if="suggestedRooms.length" class="mt-2 pt-2 border-t border-rose-200">
          <span class="font-semibold block mb-1">Gợi ý phòng cùng hạng còn trống:</span>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="s in suggestedRooms"
              :key="s.room_id"
              @click="selectedRoomId = s.room_id"
              type="button"
              class="px-2.5 py-1 bg-white hover:bg-rose-100 border border-rose-300 rounded font-mono font-bold text-rose-900 transition"
            >
              Phòng {{ s.room_number }} (Tầng {{ s.floor }})
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Booking Form -->
    <form @submit.prevent="handleSubmit" class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Left Column: Stay & Room (2 cols) -->
      <div class="md:col-span-2 space-y-6">
        <!-- Room Configuration Box -->
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
            1. Cấu hình phòng & Khung giờ
          </h3>

          <!-- Booking Type: Daily or Hourly -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1.5">Loại hình đặt phòng</label>
            <div class="grid grid-cols-2 gap-3">
              <button
                type="button"
                @click="bookingType = 'NGAY'"
                :class="bookingType === 'NGAY' ? 'bg-sky-600 text-white font-bold ring-2 ring-sky-600' : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200'"
                class="py-2.5 rounded-xl text-xs transition"
              >
                Theo ngày (Đêm)
              </button>
              <button
                type="button"
                @click="bookingType = 'GIO'"
                :class="bookingType === 'GIO' ? 'bg-sky-600 text-white font-bold ring-2 ring-sky-600' : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200'"
                class="py-2.5 rounded-xl text-xs transition"
              >
                Theo giờ (Chỉ Standard)
              </button>
            </div>
          </div>

          <!-- Room Category -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1.5">Hạng phòng</label>
              <select
                v-model="roomType"
                @change="handleRoomTypeChange"
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="STANDARD">Standard (Phổ thông - 550.000đ/đêm)</option>
                <option value="SUPERIOR" :disabled="bookingType === 'GIO'">Superior (Cao cấp - 850.000đ/đêm)</option>
                <option value="DELUXE" :disabled="bookingType === 'GIO'">Deluxe (Sang trọng - 1.250.000đ/đêm)</option>
                <option value="SUITE" :disabled="bookingType === 'GIO'">Suite (Tổng thống - 2.100.000đ/đêm)</option>
              </select>
            </div>

            <!-- Specific Physical Room (Counter feature) -->
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1.5">
                Chỉ định phòng cụ thể
                <span class="text-slate-400 font-normal">(tùy chọn)</span>
              </label>
              <input
                v-model="selectedRoomId"
                type="number"
                placeholder="Để trống = Tự động gán phòng tối ưu"
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <!-- Dates & Times -->
          <div v-if="bookingType === 'NGAY'" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Ngày nhận phòng (14:00)</label>
              <input
                v-model="checkinDate"
                type="date"
                required
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Ngày trả phòng (12:00)</label>
              <input
                v-model="checkoutDate"
                type="date"
                required
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <!-- Hourly times -->
          <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Giờ bắt đầu</label>
              <input
                v-model="hourlyCheckin"
                type="datetime-local"
                required
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Giờ kết thúc</label>
              <input
                v-model="hourlyCheckout"
                type="datetime-local"
                required
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <!-- Guests -->
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Số lượng khách</label>
            <input
              v-model.number="guestsCount"
              type="number"
              min="1"
              max="10"
              required
              class="w-32 px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
        </div>

        <!-- Customer Info Box -->
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
            2. Thông tin khách lưu trú
          </h3>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Họ và tên khách</label>
              <input
                v-model="custName"
                type="text"
                required
                placeholder="Nguyễn Văn A"
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Số điện thoại</label>
              <input
                v-model="custPhone"
                type="tel"
                required
                placeholder="0912345678"
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Email</label>
              <input
                v-model="custEmail"
                type="email"
                required
                placeholder="guest@example.com"
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Quốc tịch</label>
              <input
                v-model="custNationality"
                type="text"
                required
                placeholder="VN"
                class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium outline-none focus:ring-2 focus:ring-sky-500 uppercase"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Payment & Confirmation (1 col) -->
      <div class="space-y-6">
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5 sticky top-6">
          <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
            3. Thanh toán & Xác nhận
          </h3>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-2">Phương thức thanh toán</label>
            <div class="space-y-2 text-xs">
              <label class="flex items-center space-x-2.5 p-3 rounded-xl border border-sky-200 bg-sky-50/50 cursor-pointer">
                <input type="radio" v-model="paymentMethod" value="KHI_NHAN_PHONG" class="text-sky-600 focus:ring-sky-500" />
                <span class="font-bold text-slate-800">Thu tiền khi nhận phòng</span>
              </label>
              <label class="flex items-center space-x-2.5 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer">
                <input type="radio" v-model="paymentMethod" value="TRUC_TUYEN" class="text-sky-600 focus:ring-sky-500" />
                <span class="font-medium text-slate-700">Thanh toán trực tuyến / Cổng</span>
              </label>
            </div>
          </div>

          <div class="bg-slate-50 rounded-xl p-4 text-xs space-y-1.5 border border-slate-100">
            <span class="font-bold text-slate-600 uppercase text-[10px] tracking-wider block">Ghi chú nghiệp vụ</span>
            <p class="text-slate-500 leading-relaxed text-[11px]">
              Đơn tạo tại quầy sẽ được chuyển sang trạng thái <strong>CONFIRMED</strong> ngay lập tức, không qua đếm ngược 15 phút (BR-13).
            </p>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="submitting"
            class="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            <div v-if="submitting" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            <span>{{ submitting ? 'Đang tạo đơn...' : 'Xác nhận tạo đơn' }}</span>
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '../../api/client';

const route = useRoute();
const router = useRouter();

const bookingType = ref('NGAY');
const roomType = ref('STANDARD');
const selectedRoomId = ref(null);

// Dates
const checkinDate = ref('');
const checkoutDate = ref('');
const hourlyCheckin = ref('');
const hourlyCheckout = ref('');
const guestsCount = ref(2);

// Customer
const custName = ref('');
const custPhone = ref('');
const custEmail = ref('');
const custNationality = ref('VN');
const paymentMethod = ref('KHI_NHAN_PHONG');

const submitting = ref(false);
const errorMessage = ref('');
const suggestedRooms = ref([]);

const handleRoomTypeChange = () => {
  suggestedRooms.value = [];
};

const initDefaultDates = () => {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);

  const dayAfter = new Date();
  dayAfter.setDate(dayAfter.getDate() + 3);

  checkinDate.value = tomorrow.toISOString().split('T')[0];
  checkoutDate.value = dayAfter.toISOString().split('T')[0];

  // Hourly defaults
  const now = new Date();
  now.setMinutes(0, 0, 0);
  now.setHours(now.getHours() + 1);
  const later = new Date(now.getTime() + 3 * 3600 * 1000);

  const pad = (n) => String(n).padStart(2, '0');
  const formatInput = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;

  hourlyCheckin.value = formatInput(now);
  hourlyCheckout.value = formatInput(later);
};

const handleSubmit = async () => {
  submitting.value = true;
  errorMessage.value = '';
  suggestedRooms.value = [];

  let checkinIso = '';
  let checkoutIso = '';

  if (bookingType.value === 'NGAY') {
    checkinIso = `${checkinDate.value}T14:00:00+07:00`;
    checkoutIso = `${checkoutDate.value}T12:00:00+07:00`;
  } else {
    checkinIso = `${hourlyCheckin.value}:00+07:00`;
    checkoutIso = `${hourlyCheckout.value}:00+07:00`;
  }

  const payload = {
    loaiDat: bookingType.value,
    maHang: roomType.value,
    phongId: selectedRoomId.value ? Number(selectedRoomId.value) : null,
    nhanLuc: checkinIso,
    traLuc: checkoutIso,
    soKhach: guestsCount.value,
    thanhToan: paymentMethod.value,
    dongYChinhSach: true,
    customer: {
      fullName: custName.value.trim(),
      phone: custPhone.value.trim(),
      email: custEmail.value.trim().toLowerCase(),
      nationality: custNationality.value.trim().toUpperCase() || 'VN'
    }
  };

  try {
    const res = await apiClient.post('/bookings', payload);
    const code = res.booking_code || res.bookingCode;
    router.push(`/nv/don/${code}`);
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tạo đơn đặt phòng';
    if (err.data?.suggested_rooms) {
      suggestedRooms.value = err.data.suggested_rooms;
    }
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  initDefaultDates();
  if (route.query.roomId) {
    selectedRoomId.value = Number(route.query.roomId);
  }
  if (route.query.roomType) {
    roomType.value = String(route.query.roomType).toUpperCase();
  }
});
</script>
