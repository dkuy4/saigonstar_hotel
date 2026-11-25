<template>
  <div class="max-w-4xl mx-auto space-y-8">
    <!-- Header -->
    <div class="border-b border-slate-200 pb-4">
      <router-link to="/ket-qua" class="text-xs text-sky-600 hover:underline flex items-center gap-1 mb-2">
        <span>←</span>
        <span>Quay lại kết quả tìm kiếm</span>
      </router-link>
      <h2 class="text-2xl font-bold text-slate-900">Xác nhận đặt phòng</h2>
      <p class="text-xs text-slate-500 mt-0.5">Vui lòng điền thông tin người lưu trú và phương thức thanh toán</p>
    </div>

    <!-- Error Banner -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-start space-x-3">
      <AlertCircle class="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
      <div class="flex-1">
        <p class="font-semibold">{{ errorTitle }}</p>
        <p class="text-xs mt-0.5">{{ errorMessage }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left: Form Input (2 cols) -->
      <div class="lg:col-span-2 space-y-6">
        <form @submit.prevent="handleBooking" class="space-y-6">
          <!-- Customer Info Card -->
          <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <User class="w-4 h-4 text-sky-600" />
              <span>Thông tin khách lưu trú</span>
            </h3>

            <div class="space-y-4">
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">
                  Họ và tên khách hàng <span class="text-rose-500">*</span>
                </label>
                <input
                  v-model="customer.fullName"
                  type="text"
                  required
                  placeholder="Ví dụ: Nguyễn Văn A"
                  class="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
                />
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">
                    Số điện thoại liên hệ <span class="text-rose-500">*</span>
                  </label>
                  <input
                    v-model="customer.phone"
                    type="tel"
                    required
                    placeholder="0901234567"
                    class="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
                  />
                </div>

                <div>
                  <label class="block text-xs font-semibold text-slate-700 mb-1">
                    Địa chỉ Email nhận xác nhận <span class="text-rose-500">*</span>
                  </label>
                  <input
                    v-model="customer.email"
                    type="email"
                    required
                    placeholder="email@example.com"
                    class="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">
                  Quốc tịch
                </label>
                <select
                  v-model="customer.nationality"
                  class="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none bg-white"
                >
                  <option value="VN">Việt Nam (VN)</option>
                  <option value="US">Hoa Kỳ (US)</option>
                  <option value="JP">Nhật Bản (JP)</option>
                  <option value="KR">Hàn Quốc (KR)</option>
                  <option value="CN">Trung Quốc (CN)</option>
                  <option value="GB">Anh Quốc (GB)</option>
                  <option value="FR">Pháp (FR)</option>
                  <option value="OTHER">Khác</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Room Selection Card (Chọn số phòng mong muốn) -->
          <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <DoorOpen class="w-4 h-4 text-sky-600" />
                <span>Chọn số phòng mong muốn</span>
              </h3>
              <span class="text-xs text-slate-400 font-normal">Tùy chọn</span>
            </div>
            
            <p class="text-xs text-slate-500">
              Quý khách có thể chọn căn phòng ưng ý trước hoặc để khách sạn tự động lựa chọn phòng tốt nhất.
            </p>

            <!-- Loading rooms -->
            <div v-if="loadingRooms" class="py-4 text-center text-xs text-slate-400 flex items-center justify-center space-x-2">
              <div class="animate-spin rounded-full h-3.5 w-3.5 border-2 border-sky-600 border-t-transparent"></div>
              <span>Đang kiểm tra danh sách phòng còn trống...</span>
            </div>

            <!-- Room selection list -->
            <div v-else class="space-y-3">
              <!-- Default Option: Auto Assign -->
              <label
                class="flex items-center justify-between p-3.5 border rounded-xl cursor-pointer transition"
                :class="selectedRoomId === null ? 'border-sky-500 bg-sky-50/50 ring-1 ring-sky-500' : 'border-slate-200 hover:bg-slate-50'"
              >
                <div class="flex items-center space-x-3">
                  <input
                    type="radio"
                    :checked="selectedRoomId === null"
                    @change="selectedRoomId = null"
                    class="text-sky-600 focus:ring-sky-500 h-4 w-4"
                  />
                  <div>
                    <span class="text-xs font-semibold text-slate-800">Tự động sắp xếp phòng</span>
                    <p class="text-[11px] text-slate-500">Khách sạn sẽ ưu tiên chọn phòng yên tĩnh và tối ưu nhất cho quý khách</p>
                  </div>
                </div>
                <Sparkles class="w-4 h-4 text-amber-500" />
              </label>

              <!-- Custom Room Pick Option -->
              <div v-if="availableRooms.length > 0" class="pt-2">
                <p class="text-xs font-semibold text-slate-700 mb-2">
                  Hoặc chọn trực tiếp phòng trống bên dưới ({{ availableRooms.length }} phòng sẵn sàng):
                </p>
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 max-h-56 overflow-y-auto p-1">
                  <button
                    v-for="r in availableRooms"
                    :key="r.room_id"
                    type="button"
                    @click="selectedRoomId = (selectedRoomId === r.room_id ? null : r.room_id)"
                    class="p-2.5 rounded-xl border text-left transition flex flex-col justify-between"
                    :class="selectedRoomId === r.room_id ? 'border-sky-600 bg-sky-50/80 ring-2 ring-sky-500 text-sky-900 shadow-sm' : 'border-slate-200 hover:border-slate-300 bg-slate-50/60 text-slate-700'"
                  >
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-xs">Phòng {{ r.room_number }}</span>
                      <CheckCircle2 v-if="selectedRoomId === r.room_id" class="w-3.5 h-3.5 text-sky-600" />
                    </div>
                    <span class="text-[10px] text-slate-500 mt-1">Tầng {{ r.floor }}</span>
                  </button>
                </div>
              </div>

              <div v-else class="text-xs text-slate-400 italic">
                Tất cả phòng trống cùng hạng sẽ được phân bổ tự động khi quý khách hoàn tất đơn.
              </div>
            </div>
          </div>

          <!-- Payment Options Card -->
          <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <CreditCard class="w-4 h-4 text-sky-600" />
              <span>Phương thức thanh toán</span>
            </h3>

            <div class="space-y-3">
              <!-- Online Payment (HOLD) -->
              <label
                class="flex items-start p-4 border rounded-xl cursor-pointer transition"
                :class="paymentMethod === 'TRUC_TUYEN' ? 'border-sky-500 bg-sky-50/50 ring-1 ring-sky-500' : 'border-slate-200 hover:bg-slate-50'"
              >
                <input
                  v-model="paymentMethod"
                  type="radio"
                  value="TRUC_TUYEN"
                  class="mt-1 text-sky-600 focus:ring-sky-500 h-4 w-4"
                />
                <div class="ml-3">
                  <div class="font-semibold text-sm text-slate-900">Thanh toán trực tuyến (Thẻ ATM / Visa / QR Pay)</div>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Hệ thống sẽ giữ chỗ phòng trong <strong>15 phút</strong> để quý khách hoàn tất giao dịch thanh toán trực tuyến an toàn.
                  </p>
                </div>
              </label>

              <!-- Pay at Hotel (CONFIRMED) -->
              <label
                class="flex items-start p-4 border rounded-xl cursor-pointer transition"
                :class="paymentMethod === 'KHI_NHAN_PHONG' ? 'border-sky-500 bg-sky-50/50 ring-1 ring-sky-500' : 'border-slate-200 hover:bg-slate-50'"
              >
                <input
                  v-model="paymentMethod"
                  type="radio"
                  value="KHI_NHAN_PHONG"
                  class="mt-1 text-sky-600 focus:ring-sky-500 h-4 w-4"
                />
                <div class="ml-3">
                  <div class="font-semibold text-sm text-slate-900">Thanh toán khi nhận phòng tại quầy</div>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Xác nhận đơn ngay lập tức. Quý khách thanh toán bằng tiền mặt hoặc thẻ khi đến nhận phòng tại khách sạn. Mỗi khách hàng được giữ tối đa 3 đơn chưa thanh toán.
                  </p>
                </div>
              </label>
            </div>
          </div>

          <!-- Policy Agreement -->
          <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
            <div class="flex items-start">
              <input
                id="agree-checkbox"
                v-model="agreeTerms"
                type="checkbox"
                required
                class="mt-1 h-4 w-4 text-sky-600 focus:ring-sky-500 border-slate-300 rounded"
              />
              <label for="agree-checkbox" class="ml-3 text-xs text-slate-700 leading-relaxed cursor-pointer">
                Tôi xác nhận đã đọc và đồng ý với
                <button type="button" @click="showPolicyModal = true" class="text-sky-600 underline font-medium hover:text-sky-800">
                  Chính sách hủy phòng và Quy định nhận phòng
                </button>
                của khách sạn Sài Gòn Star. <span class="text-rose-500">*</span>
              </label>
            </div>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading || !isFormValid"
            class="w-full py-4 px-6 bg-sky-600 hover:bg-sky-700 text-white font-bold text-base rounded-xl shadow-lg hover:shadow-xl transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            <span>{{ loading ? 'Đang khởi tạo đơn...' : (paymentMethod === 'TRUC_TUYEN' ? 'Tiến hành giữ chỗ & Thanh toán' : 'Xác nhận đặt phòng ngay') }}</span>
            <span>→</span>
          </button>
        </form>
      </div>

      <!-- Right: Booking Summary (1 col) -->
      <div class="space-y-6">
        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm sticky top-24 space-y-5">
          <h3 class="text-base font-bold text-slate-800 pb-3 border-b border-slate-100">
            Chi tiết lưu trú
          </h3>

          <div class="space-y-3 text-xs text-slate-600">
            <div class="flex justify-between items-center">
              <span class="text-slate-500">Hạng phòng:</span>
              <span class="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{{ roomType }}</span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-slate-500">Hình thức thuê:</span>
              <span class="font-medium text-slate-800">{{ stayType === 'NGAY' ? 'Theo ngày (Đêm)' : 'Theo giờ' }}</span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-slate-500">Số lượng khách:</span>
              <span class="font-medium text-slate-800">{{ guests }} người</span>
            </div>

            <div class="flex justify-between items-center pt-2 border-t border-slate-100">
              <span class="text-slate-500">Số phòng chọn:</span>
              <span class="font-semibold text-xs text-sky-700">
                {{ selectedRoomNumber ? `Phòng ${selectedRoomNumber}` : 'Tự động sắp xếp' }}
              </span>
            </div>

            <div class="pt-2 border-t border-slate-100 space-y-2">
              <div>
                <span class="text-slate-400 block text-[10px] uppercase">Nhận phòng:</span>
                <span class="font-semibold text-slate-800">{{ formatDateTime(checkin) }}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-[10px] uppercase">Trả phòng:</span>
                <span class="font-semibold text-slate-800">{{ formatDateTime(checkout) }}</span>
              </div>
            </div>
          </div>

          <!-- Price Calculation Box -->
          <div v-if="priceInfo" class="pt-4 border-t border-slate-200 space-y-2 text-xs">
            <div class="flex justify-between text-slate-600">
              <span>Tiền phòng:</span>
              <MoneyText :value="priceInfo.room_amount" currency="VND" />
            </div>
            <div class="flex justify-between text-slate-600">
              <span>Thuế VAT ({{ (priceInfo.vat_rate * 100).toFixed(0) }}%):</span>
              <MoneyText :value="priceInfo.vat_amount" currency="VND" />
            </div>
            <div class="pt-3 border-t border-slate-100 flex justify-between items-baseline">
              <div>
                <span class="text-xs uppercase font-bold text-slate-700 block">Tổng thanh toán:</span>
                <span class="text-[10px] text-slate-400">Đã bao gồm thuế VAT 8%</span>
              </div>
              <div class="text-xl font-black text-sky-600">
                <MoneyText :value="priceInfo.total_amount" currency="VND" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Policy Modal -->
    <div v-if="showPolicyModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b pb-3">
          <h4 class="font-bold text-base text-slate-900">Chính sách hủy & vắng mặt</h4>
          <button @click="showPolicyModal = false" class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100">
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="text-xs text-slate-600 space-y-3 leading-relaxed">
          <p class="font-semibold text-slate-800">1. Chính sách hủy phòng</p>
          <ul class="list-disc pl-4 space-y-1">
            <li>Hủy trước 24 giờ so với giờ nhận phòng: Hoàn trả 100% số tiền đã thanh toán (bao gồm cả thuế VAT).</li>
            <li>Hủy trong vòng 24 giờ: Phí hủy bằng 100% tiền phòng của đêm lưu trú đầu tiên.</li>
          </ul>

          <p class="font-semibold text-slate-800">2. Quy định khi quý khách không đến nhận phòng</p>
          <ul class="list-disc pl-4 space-y-1">
            <li>Đơn chưa thanh toán: Nếu khách không nhận phòng sau 2 giờ (với đơn ngày) hoặc 30 phút (với đơn giờ), hệ thống tự động giải phóng phòng.</li>
            <li>Đơn đã thanh toán: Khách sạn giữ phòng cho quý khách đến 12:00 ngày hôm sau (đơn ngày) hoặc đến hết khung giờ thuê (đơn giờ).</li>
          </ul>

          <p class="font-semibold text-slate-800">3. Thời gian giữ phòng trực tuyến</p>
          <p>Thời hạn giữ chỗ tối đa là 15 phút. Nếu quá hạn chưa hoàn tất thanh toán, hệ thống sẽ tự động hủy đơn và mở phòng cho khách hàng khác.</p>
        </div>

        <div class="pt-3 border-t text-right">
          <button
            @click="showPolicyModal = false"
            class="px-4 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold hover:bg-sky-700 transition"
          >
            Đã hiểu và Đóng
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { AlertCircle, User, CreditCard, X, DoorOpen, Sparkles, CheckCircle2 } from 'lucide-vue-next';
import apiClient from '../api/client';
import MoneyText from '../components/MoneyText.vue';
import { useGuestAuthStore } from '../stores/guestAuth';

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const guestAuth = useGuestAuthStore();

const stayType = computed(() => route.query.type || 'NGAY');
const roomType = computed(() => route.query.room_type || 'STANDARD');
const checkin = computed(() => route.query.checkin || '');
const checkout = computed(() => route.query.checkout || '');
const guests = computed(() => Number(route.query.guests || 2));

const customer = ref({
  fullName: guestAuth.isLoggedIn ? guestAuth.guestName : '',
  phone: guestAuth.isLoggedIn ? guestAuth.guestPhone : '',
  email: guestAuth.isLoggedIn ? guestAuth.guestEmail : '',
  nationality: 'VN'
});

const paymentMethod = ref('TRUC_TUYEN');
const agreeTerms = ref(false);
const showPolicyModal = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const errorTitle = ref('');
const priceInfo = ref(null);

const availableRooms = ref([]);
const selectedRoomId = ref(null);
const loadingRooms = ref(false);

const selectedRoomNumber = computed(() => {
  if (!selectedRoomId.value) return null;
  const found = availableRooms.value.find(r => r.room_id === selectedRoomId.value);
  return found ? found.room_number : null;
});

const loadAvailableRooms = async () => {
  if (!checkin.value || !checkout.value || !roomType.value) return;
  loadingRooms.value = true;
  try {
    const res = await apiClient.get('/availability/rooms', {
      params: {
        roomType: roomType.value,
        checkin: checkin.value,
        checkout: checkout.value
      }
    });
    availableRooms.value = res.rooms || res.data?.rooms || [];
  } catch (err) {
    console.error('Không thể tải danh sách phòng khả dụng:', err);
    availableRooms.value = [];
  } finally {
    loadingRooms.value = false;
  }
};

const isFormValid = computed(() => {
  return (
    customer.value.fullName.trim().length >= 2 &&
    customer.value.phone.trim().length >= 8 &&
    customer.value.email.includes('@') &&
    agreeTerms.value
  );
});

const formatDateTime = (isoStr) => {
  if (!isoStr) return '';
  return new Date(isoStr).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Fetch real-time price validation from availability endpoint
const loadPriceInfo = async () => {
  if (!checkin.value || !checkout.value) {
    router.replace('/');
    return;
  }
  try {
    const res = await apiClient.get('/availability', {
      params: {
        type: stayType.value,
        checkin: checkin.value,
        checkout: checkout.value,
        guests: guests.value,
        room_type: roomType.value,
        lang: locale.value
      }
    });
    if (res.items && res.items.length > 0) {
      priceInfo.value = res.items[0];
    } else {
      errorMessage.value = 'Hạng phòng này hiện không còn phòng trống trong khoảng thời gian đã chọn.';
      errorTitle.value = 'Hết phòng';
    }
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tính toán biểu phí';
    errorTitle.value = 'Lỗi kết nối';
  }
};

const handleBooking = async () => {
  if (!isFormValid.value) return;

  loading.value = true;
  errorMessage.value = '';
  errorTitle.value = '';

  try {
    const payload = {
      loaiDat: stayType.value,
      maHang: roomType.value,
      phongId: selectedRoomId.value || null,
      nhanLuc: checkin.value,
      traLuc: checkout.value,
      soKhach: guests.value,
      thanhToan: paymentMethod.value,
      dongYChinhSach: agreeTerms.value,
      customer: {
        fullName: customer.value.fullName,
        phone: customer.value.phone,
        email: customer.value.email,
        nationality: customer.value.nationality
      },
      ngonNgu: locale.value
    };

    const res = await apiClient.post('/bookings', payload);
    const booking = res.data || res;

    if (booking.status === 'HOLD') {
      // Direct to Hold/Payment view
      router.push(`/giu-cho/${booking.booking_code}`);
    } else {
      // Direct to Confirmation view
      router.push(`/don/${booking.booking_code}`);
    }
  } catch (err) {
    errorTitle.value = 'Không thể tạo đơn đặt phòng';
    if (err.code === 'NO_AVAILABILITY') {
      errorMessage.value = t('errors.NO_AVAILABILITY');
    } else if (err.code === 'PENDING_LIMIT_EXCEEDED') {
      errorMessage.value = t('errors.PENDING_LIMIT_EXCEEDED');
    } else if (err.code === 'ROOM_CONFLICT') {
      errorMessage.value = t('errors.ROOM_CONFLICT');
    } else {
      errorMessage.value = err.message || t('errors.INTERNAL_SERVER_ERROR');
    }
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadPriceInfo();
  loadAvailableRooms();
});
</script>
