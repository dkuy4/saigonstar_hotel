<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Subtitle -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Quản lý bảng giá phòng</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            F16.3 Admin
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Thiết lập đơn giá ngày, đơn giá giờ, thuế VAT và tự động ghi nhật ký kiểm toán (FR-28, AC-04)
        </p>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex flex-wrap items-center gap-2">
        <router-link
          to="/nv/quan-ly/phong"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Danh mục phòng (16.1)
        </router-link>
        <router-link
          to="/nv/quan-ly/hang-phong"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Hạng phòng & Đa ngôn ngữ (16.2)
        </router-link>
        <span class="px-3 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold shadow-sm">
          Bảng giá (16.3)
        </span>
        <router-link
          to="/nv/quan-ly/tham-so"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tham số & VAT (16.4)
        </router-link>
        <router-link
          to="/nv/quan-ly/ban-dich"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bản dịch & Email (16.5)
        </router-link>
        <router-link
          to="/nv/quan-ly/tai-khoan"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tài khoản (F17)
        </router-link>
      </div>
    </div>

    <!-- Notifications -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
      <div class="flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
        <span>{{ errorMessage }}</span>
      </div>
      <button @click="errorMessage = ''" class="font-bold text-rose-600 hover:text-rose-800">✕</button>
    </div>

    <div v-if="successMessage" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
      <div class="flex items-center space-x-2">
        <CheckCircle2 class="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>{{ successMessage }}</span>
      </div>
      <button @click="successMessage = ''" class="font-bold text-emerald-600 hover:text-emerald-800">✕</button>
    </div>

    <!-- Active Price Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider">Bảng giá phòng đang áp dụng</h2>
          <p class="text-[11px] text-slate-500">Mức giá đã bao gồm thuế VAT hiện hành, áp dụng khi đặt trực tuyến và tại quầy</p>
        </div>
        <div class="flex items-center space-x-3">
          <button
            @click="fetchPrices"
            :disabled="loading"
            class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition flex items-center space-x-1"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      <!-- Table Content -->
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <th class="py-3 px-4">Hạng phòng</th>
              <th class="py-3 px-4">Hình thức thuê</th>
              <th class="py-3 px-4 text-right">Giá chưa VAT</th>
              <th class="py-3 px-4 text-center">Thuế VAT</th>
              <th class="py-3 px-4 text-right">Tổng giá gồm VAT</th>
              <th class="py-3 px-4">Hiệu lực từ</th>
              <th class="py-3 px-4">Hiệu lực đến</th>
              <th class="py-3 px-4 text-center">Trạng thái</th>
              <th class="py-3 px-4 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading && !priceList.length">
              <td colspan="9" class="py-8 text-center text-slate-400">Đang tải dữ liệu bảng giá...</td>
            </tr>
            <tr
              v-for="p in activePrices"
              :key="p.bangGiaId"
              class="hover:bg-slate-50/70 transition"
            >
              <!-- Room Type & Code -->
              <td class="py-3 px-4">
                <div class="font-bold text-slate-900">{{ p.tenHang }}</div>
                <div class="text-[10px] font-mono text-sky-600 uppercase font-semibold">Mã: {{ p.maHang }}</div>
              </td>

              <!-- Price Type -->
              <td class="py-3 px-4">
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded-full font-semibold text-[10px]"
                  :class="p.loaiGia === 'GIO' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'"
                >
                  <Clock v-if="p.loaiGia === 'GIO'" class="w-3 h-3 mr-1" />
                  <Calendar v-else class="w-3 h-3 mr-1" />
                  {{ p.loaiGia === 'GIO' ? 'Theo giờ' : 'Theo ngày' }}
                </span>
              </td>

              <!-- Base Price -->
              <td class="py-3 px-4 text-right font-mono font-medium text-slate-700">
                {{ formatCurrency(p.donGia) }}
              </td>

              <!-- VAT Rate -->
              <td class="py-3 px-4 text-center">
                <span class="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-bold">
                  {{ (p.thueSuat * 100).toFixed(0) }}%
                </span>
              </td>

              <!-- Gross Price With VAT -->
              <td class="py-3 px-4 text-right font-mono font-bold text-slate-900 text-sm">
                {{ formatCurrency(p.donGiaVat) }}
              </td>

              <!-- Effective From -->
              <td class="py-3 px-4 text-slate-600 font-mono">
                {{ p.hieuLucTu }}
              </td>

              <!-- Effective To -->
              <td class="py-3 px-4 text-slate-500 font-mono">
                <span v-if="p.hieuLucDen">{{ p.hieuLucDen }}</span>
                <span v-else class="text-emerald-600 font-medium">Vô thời hạn</span>
              </td>

              <!-- Status -->
              <td class="py-3 px-4 text-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
                  Đang áp dụng
                </span>
              </td>

              <!-- Actions -->
              <td class="py-3 px-4 text-right space-x-2">
                <button
                  @click="openChangeModal(p)"
                  class="px-2.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold transition shadow-sm"
                >
                  Đổi giá
                </button>
                <button
                  @click="openHistoryDrawer(p.maHang)"
                  class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
                >
                  Lịch sử
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Notice Card on Business Rules -->
    <div class="bg-amber-50/80 border border-amber-200 rounded-2xl p-5 text-xs text-amber-900 space-y-2">
      <div class="flex items-center space-x-2 font-bold text-amber-950">
        <Info class="w-4 h-4 text-amber-700 flex-shrink-0" />
        <span>Quy tắc ràng buộc bảng giá (BR-02, BR-04, FR-28)</span>
      </div>
      <ul class="list-disc list-inside space-y-1 text-amber-800 pl-1">
        <li>Chỉ hạng phòng <strong>Standard</strong> mới hỗ trợ thuê theo giờ (hạng Superior, Deluxe, Suite chỉ thuê theo ngày).</li>
        <li><strong>Quy tắc ngưỡng 5 giờ:</strong> 5 lần giá giờ không được vượt quá 1 giá ngày của cùng thời điểm hiệu lực.</li>
        <li>Ngày hiệu lực mới phải từ ngày hôm nay trở đi. Toàn bộ lịch sử thay đổi giá và lý do điều chỉnh được ghi vào nhật ký kiểm toán hệ thống.</li>
        <li>Các đơn đặt phòng đã tạo trước thời điểm đổi giá vẫn giữ nguyên mức giá cũ đã chốt (BR-42).</li>
      </ul>
    </div>

    <!-- Change Price Modal -->
    <div
      v-if="showChangeModal"
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-5 my-8">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-900">Điều chỉnh bảng giá</h3>
            <p class="text-xs text-slate-500">Áp dụng cho hạng {{ form.maHang }} ({{ form.loaiGia === 'GIO' ? 'Theo giờ' : 'Theo ngày' }})</p>
          </div>
          <button @click="showChangeModal = false" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
        </div>

        <form @submit.prevent="handleSubmitPriceChange" class="space-y-4 text-xs">
          <!-- Room Type (Read-only or Select) -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Hạng phòng</label>
              <input
                :value="form.tenHang || form.maHang"
                disabled
                class="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl font-medium text-slate-600 cursor-not-allowed"
              />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Loại giá</label>
              <input
                :value="form.loaiGia === 'GIO' ? 'Thuê theo giờ' : 'Thuê theo ngày'"
                disabled
                class="w-full px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl font-medium text-slate-600 cursor-not-allowed"
              />
            </div>
          </div>

          <!-- New Price & VAT preview -->
          <div>
            <div class="flex justify-between items-center mb-1">
              <label class="font-semibold text-slate-700">Đơn giá mới (chưa VAT) *</label>
              <span class="text-[10px] text-slate-400">Bội số của 1.000 đ</span>
            </div>
            <div class="relative">
              <input
                v-model.number="form.donGia"
                @input="handlePriceInput"
                type="number"
                step="1000"
                min="1000"
                required
                placeholder="Nhập giá mới (VND)"
                class="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-xl font-mono text-sm font-bold text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none pr-12"
              />
              <span class="absolute right-3 top-3 font-semibold text-slate-400">VND</span>
            </div>

            <!-- VAT Estimation -->
            <div class="mt-2 p-2.5 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between text-slate-600">
              <span>Ước tính gồm VAT (8%):</span>
              <strong class="font-mono text-slate-900 text-xs">
                {{ formatCurrency(Math.round(form.donGia * 1.08)) }}
              </strong>
            </div>
          </div>

          <!-- Effective Date -->
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Ngày bắt đầu hiệu lực *</label>
            <input
              v-model="form.hieuLucTu"
              @change="handlePriceInput"
              type="date"
              :min="todayStr"
              required
              class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            />
            <p class="text-[10px] text-slate-400 mt-1">Mức giá cũ sẽ tự động kết thúc vào ngày liền kề trước ngày này</p>
          </div>

          <!-- Live Rule Validation Feedback -->
          <div
            v-if="form.maHang === 'STANDARD'"
            class="p-3.5 rounded-xl border text-xs space-y-1 transition"
            :class="ruleCheck.valid ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'"
          >
            <div class="flex items-center space-x-1.5 font-bold">
              <CheckCircle2 v-if="ruleCheck.valid" class="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <AlertCircle v-else class="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>Kiểm tra quy tắc giá giờ (BR-04, AC-04):</span>
            </div>
            <p class="text-[11px] leading-relaxed">
              {{ ruleCheck.message || 'Đang kiểm tra tính hợp lệ...' }}
            </p>
          </div>

          <!-- Reason (Audit Requirement) -->
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Lý do điều chỉnh (lưu vào nhật ký kiểm toán) *</label>
            <textarea
              v-model="form.lyDo"
              rows="2"
              required
              placeholder="VD: Điều chỉnh giá theo quyết định phê duyệt QĐ-2026/04..."
              class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            ></textarea>
          </div>

          <!-- Modal Action Buttons -->
          <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              @click="showChangeModal = false"
              class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="saving || (form.maHang === 'STANDARD' && !ruleCheck.valid)"
              class="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-xl shadow transition disabled:opacity-50 flex items-center space-x-1.5"
            >
              <div v-if="saving" class="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
              <span>{{ saving ? 'Đang lưu...' : 'Xác nhận đổi giá' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- History Drawer / Modal -->
    <div
      v-if="showHistoryModal"
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl max-w-3xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 my-8">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-900">Lịch sử giá - Hạng {{ historyRoomCode }}</h3>
            <p class="text-xs text-slate-500">Toàn bộ các chu kỳ giá và lịch sử điều chỉnh theo thời gian</p>
          </div>
          <button @click="showHistoryModal = false" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
        </div>

        <div class="overflow-x-auto max-h-96">
          <table class="w-full text-left text-xs divide-y divide-slate-100">
            <thead class="bg-slate-50 text-[11px] text-slate-600 uppercase font-semibold">
              <tr>
                <th class="py-2.5 px-3">Loại giá</th>
                <th class="py-2.5 px-3 text-right">Đơn giá</th>
                <th class="py-2.5 px-3 text-center">VAT</th>
                <th class="py-2.5 px-3 text-right">Giá gồm VAT</th>
                <th class="py-2.5 px-3">Hiệu lực từ</th>
                <th class="py-2.5 px-3">Hiệu lực đến</th>
                <th class="py-2.5 px-3 text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="h in historyList" :key="h.bangGiaId" class="hover:bg-slate-50/60 font-mono">
                <td class="py-2.5 px-3 font-sans font-medium text-slate-800">
                  {{ h.loaiGia === 'GIO' ? 'Theo giờ' : 'Theo ngày' }}
                </td>
                <td class="py-2.5 px-3 text-right text-slate-700">
                  {{ formatCurrency(h.donGia) }}
                </td>
                <td class="py-2.5 px-3 text-center text-slate-500">
                  {{ (h.thueSuat * 100).toFixed(0) }}%
                </td>
                <td class="py-2.5 px-3 text-right font-bold text-slate-900">
                  {{ formatCurrency(h.donGiaVat) }}
                </td>
                <td class="py-2.5 px-3 text-slate-600">{{ h.hieuLucTu }}</td>
                <td class="py-2.5 px-3 text-slate-500">{{ h.hieuLucDen || 'Hiện hành' }}</td>
                <td class="py-2.5 px-3 text-center font-sans">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                    :class="h.isActive ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'"
                  >
                    {{ h.isActive ? 'Đang áp dụng' : 'Hết hiệu lực' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex justify-end pt-3 border-t border-slate-100">
          <button
            @click="showHistoryModal = false"
            class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import {
  Calendar,
  Clock,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Info
} from 'lucide-vue-next';
import apiClient from '../../api/client';

const priceList = ref([]);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

// Date calculations
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

// Filter active prices for the main table
const activePrices = computed(() => {
  return priceList.value.filter(p => p.isActive);
});

// Format Currency
const formatCurrency = (val) => {
  if (val === null || val === undefined) return '-';
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
};

// Form state for Modal
const showChangeModal = ref(false);
const form = reactive({
  maHang: 'STANDARD',
  tenHang: 'Phòng Tiêu Chuẩn (Standard)',
  loaiGia: 'NGAY',
  donGia: 550000,
  hieuLucTu: todayStr,
  lyDo: ''
});

// Rule check state
const ruleCheck = reactive({
  valid: true,
  message: ''
});

// History Modal State
const showHistoryModal = ref(false);
const historyRoomCode = ref('');
const historyList = ref([]);

const fetchPrices = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.get('/prices');
    priceList.value = res || [];
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tải danh sách bảng giá';
  } finally {
    loading.value = false;
  }
};

const openChangeModal = (p) => {
  form.maHang = p.maHang;
  form.tenHang = p.tenHang;
  form.loaiGia = p.loaiGia;
  form.donGia = p.donGia;
  form.hieuLucTu = todayStr;
  form.lyDo = '';
  showChangeModal.value = true;
  handlePriceInput();
};

const handlePriceInput = async () => {
  if (form.maHang !== 'STANDARD') {
    ruleCheck.valid = true;
    ruleCheck.message = 'Hạng phòng chỉ thuê theo ngày, không chịu ràng buộc tỷ lệ giá giờ.';
    return;
  }

  try {
    const res = await apiClient.post('/prices/validate-rule', {
      maHang: form.maHang,
      loaiGia: form.loaiGia,
      donGia: form.donGia,
      hieuLucTu: form.hieuLucTu
    });
    ruleCheck.valid = res.valid;
    ruleCheck.message = res.message;
  } catch (err) {
    ruleCheck.valid = false;
    ruleCheck.message = err.message || 'Không thể kiểm tra quy tắc giá';
  }
};

const handleSubmitPriceChange = async () => {
  saving.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    await apiClient.post('/prices', {
      maHang: form.maHang,
      loaiGia: form.loaiGia,
      donGia: form.donGia,
      hieuLucTu: form.hieuLucTu,
      lyDo: form.lyDo
    });

    successMessage.value = `Điều chỉnh giá cho hạng ${form.maHang} (${form.loaiGia === 'GIO' ? 'Theo giờ' : 'Theo ngày'}) thành công!`;
    showChangeModal.value = false;
    await fetchPrices();
  } catch (err) {
    errorMessage.value = err.message || 'Điều chỉnh giá thất bại';
  } finally {
    saving.value = false;
  }
};

const openHistoryDrawer = async (maHang) => {
  historyRoomCode.value = maHang;
  historyList.value = priceList.value.filter(p => p.maHang === maHang);
  showHistoryModal.value = true;
};

onMounted(fetchPrices);
</script>
