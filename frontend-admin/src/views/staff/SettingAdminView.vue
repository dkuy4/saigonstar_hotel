<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Subtitle -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Tham số cấu hình & Thuế suất VAT</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            F16.4 Admin
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Cấu hình quy chuẩn nghiệp vụ, hạn giữ chỗ, hạn hủy, thời gian dọn phòng và thuế suất VAT (FR-29, AC-22)
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
          Hạng phòng (16.2)
        </router-link>
        <router-link
          to="/nv/quan-ly/bang-gia"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Bảng giá (16.3)
        </router-link>
        <span class="px-3 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold shadow-sm">
          Tham số & VAT (16.4)
        </span>
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

    <!-- Alert Notifications -->
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

    <!-- Section 1: VAT Rate Timeline Card (Khối riêng VAT theo OQ-25, AC-22) -->
    <div v-if="vatSetting" class="bg-gradient-to-br from-white to-sky-50/50 rounded-2xl border border-sky-200 shadow-sm p-6 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-sky-100 pb-3">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold shadow-sm">
            %
          </div>
          <div>
            <h2 class="text-base font-bold text-slate-900">Thuế suất Giá trị gia tăng (VAT) Dịch vụ lưu trú</h2>
            <p class="text-xs text-slate-500">Mức thuế suất áp dụng tính hóa đơn tiền phòng và các dịch vụ đi kèm</p>
          </div>
        </div>

        <button
          @click="openEditModal(vatSetting)"
          class="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm transition self-start sm:self-auto"
        >
          Điều chỉnh mức thuế VAT
        </button>
      </div>

      <!-- VAT Timeline Graphic -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Current Rate Period -->
        <div class="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
          <div class="flex items-center justify-between">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1"></span>
              Giai đoạn hiện hành
            </span>
            <span class="text-xs font-mono font-medium text-slate-500">Đến 31/12/2026</span>
          </div>
          <div class="flex items-baseline space-x-2">
            <span class="text-3xl font-black text-slate-900 font-mono">8%</span>
            <span class="text-xs text-slate-500 font-medium">(Mức giảm theo Nghị quyết 204/2025/QH15)</span>
          </div>
          <p class="text-[11px] text-slate-500">
            Áp dụng cho mọi đơn đặt phòng và hóa đơn thanh toán trong năm 2026.
          </p>
        </div>

        <!-- Next Period from 2027 -->
        <div class="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
          <div class="flex items-center justify-between">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1"></span>
              Giai đoạn tiếp theo
            </span>
            <span class="text-xs font-mono font-medium text-slate-500">Từ 01/01/2027</span>
          </div>
          <div class="flex items-baseline space-x-2">
            <span class="text-3xl font-black text-slate-900 font-mono">10%</span>
            <span class="text-xs text-slate-500 font-medium">(Thuế suất chuẩn theo Luật thuế GTGT)</span>
          </div>
          <p class="text-[11px] text-slate-500">
            Tự động áp dụng từ ngày 01/01/2027 trừ khi có nghị quyết mới gia hạn mức 8%.
          </p>
        </div>
      </div>

      <!-- Legal Warning -->
      <div class="p-3 bg-amber-50/80 border border-amber-200 text-amber-900 rounded-xl text-xs flex items-center space-x-2">
        <Info class="w-4 h-4 text-amber-600 flex-shrink-0" />
        <span><strong>Lưu ý nghiệp vụ (OQ-25):</strong> Cần kế toán trưởng đối chiếu văn bản pháp luật trước khi thay đổi mức thuế suất. Đơn đặt phòng tạo trước thời điểm đổi thuế vẫn giữ nguyên mức thuế suất cũ đã chốt (AC-22).</span>
      </div>
    </div>

    <!-- Section 2: General System Parameters Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <!-- Toolbar -->
      <div class="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider">Danh mục tham số cấu hình vận hành</h2>
          <p class="text-[11px] text-slate-500">Điều chỉnh các hằng số nghiệp vụ đặt phòng, hủy phòng, no-show và bảo mật</p>
        </div>

        <div class="flex items-center space-x-3">
          <div class="relative w-48 sm:w-64">
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Tìm mã hoặc tên tham số..."
              class="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            />
          </div>

          <button
            @click="fetchSettings"
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
              <th class="py-3 px-4">Tên tham số & Mã</th>
              <th class="py-3 px-4">Mô tả nghiệp vụ</th>
              <th class="py-3 px-4 text-center">Giá trị hiện hành</th>
              <th class="py-3 px-4 text-center">Hiệu lực từ</th>
              <th class="py-3 px-4 text-center">Hiệu lực đến</th>
              <th class="py-3 px-4 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="loading && !settingsList.length">
              <td colspan="6" class="py-8 text-center text-slate-400">Đang tải dữ liệu tham số...</td>
            </tr>
            <tr
              v-for="s in filteredSettings"
              :key="s.ma"
              class="hover:bg-slate-50/70 transition"
            >
              <!-- Name & Code -->
              <td class="py-3 px-4">
                <div class="font-bold text-slate-900">{{ s.ten }}</div>
                <div class="text-[10px] font-mono text-sky-600 uppercase font-semibold">{{ s.ma }}</div>
              </td>

              <!-- Description -->
              <td class="py-3 px-4 text-slate-600 max-w-xs">
                <p>{{ s.moTa }}</p>
                <span v-if="s.canhBao" class="text-[10px] text-amber-700 font-medium block mt-0.5">
                  Chú ý: {{ s.canhBao }}
                </span>
              </td>

              <!-- Value -->
              <td class="py-3 px-4 text-center">
                <span class="inline-flex items-center px-3 py-1 rounded-xl bg-slate-100 text-slate-900 font-mono font-bold text-xs border border-slate-200">
                  <span v-if="s.kieu === 'TY_LE'">{{ (s.giaTriHienHanh * 100).toFixed(0) }}%</span>
                  <span v-else>{{ s.giaTriHienHanh }}</span>
                  <span v-if="s.donVi && s.kieu !== 'TY_LE'" class="ml-1 text-[10px] text-slate-500 font-normal">{{ s.donVi }}</span>
                </span>
              </td>

              <!-- Effective From -->
              <td class="py-3 px-4 text-center text-slate-600 font-mono">
                {{ s.hieuLucTu }}
              </td>

              <!-- Effective To -->
              <td class="py-3 px-4 text-center text-slate-500 font-mono">
                <span v-if="s.hieuLucDen">{{ s.hieuLucDen }}</span>
                <span v-else class="text-emerald-600 font-medium">Hiện hành</span>
              </td>

              <!-- Actions -->
              <td class="py-3 px-4 text-right space-x-2">
                <button
                  @click="openEditModal(s)"
                  class="px-2.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold transition shadow-sm"
                >
                  Đổi
                </button>
                <button
                  @click="openHistoryModal(s)"
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

    <!-- Edit Setting Modal -->
    <div
      v-if="showEditModal"
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 my-8">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-900">Điều chỉnh tham số hệ thống</h3>
            <p class="text-xs text-slate-500">{{ currentEditSetting?.ten }} ({{ currentEditSetting?.ma }})</p>
          </div>
          <button @click="showEditModal = false" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
        </div>

        <form @submit.prevent="handleSubmitUpdate" class="space-y-4 text-xs">
          <!-- Warning banner if setting affects future calculations -->
          <div v-if="currentEditSetting?.canhBao" class="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl space-y-1">
            <div class="flex items-center space-x-1.5 font-bold">
              <AlertCircle class="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>Cảnh báo ảnh hưởng nghiệp vụ:</span>
            </div>
            <p class="text-[11px] leading-relaxed">{{ currentEditSetting.canhBao }}</p>
          </div>

          <!-- Value Input Field -->
          <div>
            <div class="flex justify-between items-center mb-1">
              <label class="font-semibold text-slate-700">Giá trị mới *</label>
              <span v-if="currentEditSetting?.minVal !== null && currentEditSetting?.maxVal !== null" class="text-[10px] text-slate-400">
                Khoảng hợp lệ: {{ currentEditSetting.minVal }} - {{ currentEditSetting.maxVal }} {{ currentEditSetting.donVi }}
              </span>
            </div>

            <!-- Format: Ratio / Percentage -->
            <div v-if="currentEditSetting?.kieu === 'TY_LE'" class="relative">
              <input
                v-model.number="form.giaTriPercent"
                type="number"
                step="0.1"
                min="0"
                max="100"
                required
                class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-mono text-sm font-bold text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none pr-8"
              />
              <span class="absolute right-3 top-2.5 font-bold text-slate-400">%</span>
            </div>

            <!-- Format: Time HH:MM -->
            <div v-else-if="currentEditSetting?.kieu === 'GIO'">
              <input
                v-model="form.giaTri"
                type="text"
                placeholder="14:00"
                pattern="^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
                required
                class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-mono text-sm font-bold text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
              />
              <p class="text-[10px] text-slate-400 mt-1">Định dạng 24 giờ HH:MM (VD: 14:00, 12:00)</p>
            </div>

            <!-- Format: Integer Number -->
            <div v-else class="relative">
              <input
                v-model.number="form.giaTri"
                type="number"
                step="1"
                :min="currentEditSetting?.minVal"
                :max="currentEditSetting?.maxVal"
                required
                class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-mono text-sm font-bold text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none pr-14"
              />
              <span v-if="currentEditSetting?.donVi" class="absolute right-3 top-2.5 text-xs text-slate-400 font-semibold">
                {{ currentEditSetting.donVi }}
              </span>
            </div>
          </div>

          <!-- Effective Date -->
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Ngày bắt đầu hiệu lực *</label>
            <input
              v-model="form.hieuLucTu"
              type="date"
              :min="todayStr"
              required
              class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-medium text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            />
            <p class="text-[10px] text-slate-400 mt-1">Giá trị hiện tại sẽ tự động kết thúc vào ngày liền kề trước ngày này</p>
          </div>

          <!-- Reason (Audit requirement) -->
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Lý do điều chỉnh (ghi vào nhật ký kiểm toán) *</label>
            <textarea
              v-model="form.lyDo"
              rows="2"
              required
              placeholder="VD: Cập nhật hạn giữ chỗ thanh toán theo quyết định phê duyệt..."
              class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-slate-900 focus:ring-2 focus:ring-sky-500 outline-none"
            ></textarea>
          </div>

          <!-- Action Buttons -->
          <div class="flex justify-end space-x-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              @click="showEditModal = false"
              class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-xl shadow transition disabled:opacity-50 flex items-center space-x-1.5"
            >
              <div v-if="saving" class="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
              <span>{{ saving ? 'Đang lưu...' : 'Xác nhận lưu' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- History Modal -->
    <div
      v-if="showHistoryModal"
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 space-y-4 my-8">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-900">Lịch sử điều chỉnh tham số</h3>
            <p class="text-xs text-slate-500">{{ currentHistorySetting?.ten }} ({{ currentHistorySetting?.ma }})</p>
          </div>
          <button @click="showHistoryModal = false" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
        </div>

        <div class="overflow-x-auto max-h-96">
          <table class="w-full text-left text-xs divide-y divide-slate-100">
            <thead class="bg-slate-50 text-[11px] text-slate-600 uppercase font-semibold">
              <tr>
                <th class="py-2.5 px-3">Giá trị</th>
                <th class="py-2.5 px-3">Hiệu lực từ</th>
                <th class="py-2.5 px-3">Hiệu lực đến</th>
                <th class="py-2.5 px-3 text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="(h, idx) in currentHistorySetting?.history" :key="idx" class="hover:bg-slate-50/60 font-mono">
                <td class="py-2.5 px-3 font-bold text-slate-900">
                  <span v-if="currentHistorySetting?.kieu === 'TY_LE'">{{ (h.giaTri * 100).toFixed(0) }}%</span>
                  <span v-else>{{ h.giaTri }} {{ currentHistorySetting?.donVi }}</span>
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
  RefreshCw,
  Search,
  AlertCircle,
  CheckCircle2,
  Info
} from 'lucide-vue-next';
import apiClient from '../../api/client';

const settingsList = ref([]);
const loading = ref(false);
const saving = ref(false);
const searchQuery = ref('');
const errorMessage = ref('');
const successMessage = ref('');

// Date calculation
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

// VAT specific setting item
const vatSetting = computed(() => {
  return settingsList.value.find(s => s.ma === 'THUE_SUAT_VAT');
});

// Filter settings excluding VAT (shown in separate top block) and matching search
const filteredSettings = computed(() => {
  return settingsList.value.filter(s => {
    if (s.ma === 'THUE_SUAT_VAT') return false;
    if (!searchQuery.value) return true;
    const q = searchQuery.value.toLowerCase();
    return s.ma.toLowerCase().includes(q) || s.ten.toLowerCase().includes(q) || s.moTa.toLowerCase().includes(q);
  });
});

// Modal state
const showEditModal = ref(false);
const currentEditSetting = ref(null);
const form = reactive({
  giaTri: '',
  giaTriPercent: 10,
  hieuLucTu: todayStr,
  lyDo: ''
});

// History modal
const showHistoryModal = ref(false);
const currentHistorySetting = ref(null);

const fetchSettings = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.get('/settings');
    settingsList.value = res || [];
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tải danh sách tham số cấu hình';
  } finally {
    loading.value = false;
  }
};

const openEditModal = (s) => {
  currentEditSetting.value = s;
  form.hieuLucTu = todayStr;
  form.lyDo = '';

  if (s.kieu === 'TY_LE') {
    form.giaTriPercent = Math.round(Number(s.giaTriHienHanh) * 100);
  } else {
    form.giaTri = s.giaTriHienHanh;
  }
  showEditModal.value = true;
};

const openHistoryModal = (s) => {
  currentHistorySetting.value = s;
  showHistoryModal.value = true;
};

const handleSubmitUpdate = async () => {
  saving.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  let finalVal = form.giaTri;
  if (currentEditSetting.value.kieu === 'TY_LE') {
    finalVal = form.giaTriPercent / 100.0;
  }

  try {
    const res = await apiClient.put(`/settings/${currentEditSetting.value.ma}`, {
      giaTri: finalVal,
      hieuLucTu: form.hieuLucTu,
      lyDo: form.lyDo
    });

    successMessage.value = res.canhBao
      ? `${res.message}. Chú ý: ${res.canhBao}`
      : res.message || 'Cập nhật tham số thành công!';

    showEditModal.value = false;
    await fetchSettings();
  } catch (err) {
    errorMessage.value = err.message || 'Cập nhật tham số thất bại';
  } finally {
    saving.value = false;
  }
};

onMounted(fetchSettings);
</script>
