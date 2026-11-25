<template>
  <div class="space-y-6 pb-12">
    <!-- Header & Subtitle -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black text-slate-900 tracking-tight">Bản dịch chính sách & Mẫu email</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800">
            F16.5 Admin
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Quản lý nội dung chính sách hủy, no-show và các mẫu email thông báo theo 7 ngôn ngữ chuẩn (FR-33, BR-55)
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
        <router-link
          to="/nv/quan-ly/tham-so"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tham số & VAT (16.4)
        </router-link>
        <span class="px-3 py-2 bg-sky-600 text-white rounded-xl text-xs font-semibold shadow-sm">
          Bản dịch & Email (16.5)
        </span>
        <router-link
          to="/nv/quan-ly/tai-khoan"
          class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
        >
          Tài khoản nhân viên (F17)
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

    <!-- Legal & Operational Notice (BR-55) -->
    <div class="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/80 rounded-2xl p-5 shadow-sm">
      <div class="flex items-start space-x-3.5">
        <div class="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Globe class="w-5 h-5" />
        </div>
        <div class="space-y-1 text-xs text-amber-900 leading-relaxed">
          <p class="font-bold text-amber-950 text-sm">
            Nguyên tắc đa ngôn ngữ & Giá trị pháp lý (BR-55, FR-33)
          </p>
          <p>
            - <strong>Bản tiếng Việt:</strong> Là văn bản quy chuẩn có giá trị pháp lý cao nhất khi xảy ra tranh chấp hoặc khiếu nại. Hệ thống nghiêm cấm để trống nội dung tiếng Việt.
          </p>
          <p>
            - <strong>Nhãn "Chưa rà":</strong> Áp dụng mặc định cho 5 ngôn ngữ mở rộng (Trung, Hàn, Nhật, Tây Ban Nha, Pháp). Cần được đối chiếu kỹ thuật ngữ dịch vụ lưu trú trước khi gửi khách.
          </p>
          <p>
            - <strong>Mẫu email:</strong> Bắt buộc bảo lưu nguyên vẹn toàn bộ các biến thay thế trong dấu ngoặc nhọn (ví dụ: <code class="bg-white/80 px-1 py-0.5 rounded border border-amber-300 font-mono text-[11px]">&#123;ma_don&#125;</code>) để hệ thống tự động điền dữ liệu khi phát sinh sự kiện.
          </p>
        </div>
      </div>
    </div>

    <!-- Filter & Matrix Controls -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div class="flex items-center space-x-2">
        <button
          @click="activeFilter = 'ALL'"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition"
          :class="activeFilter === 'ALL' ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          Tất cả ({{ matrixList.length }})
        </button>
        <button
          @click="activeFilter = 'CHINH_SACH'"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition"
          :class="activeFilter === 'CHINH_SACH' ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          Chính sách quy định ({{ countByType('CHINH_SACH') }})
        </button>
        <button
          @click="activeFilter = 'EMAIL'"
          class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition"
          :class="activeFilter === 'EMAIL' ? 'bg-sky-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          Mẫu email thông báo ({{ countByType('EMAIL') }})
        </button>
      </div>

      <div class="flex items-center space-x-2">
        <div class="relative w-full sm:w-64">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="Tìm theo mã hoặc tên nội dung..."
            class="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-500 focus:bg-white"
          />
          <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
        </div>
        <button
          @click="fetchTranslations"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition flex items-center space-x-1"
        >
          <RotateCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
          <span>Làm mới</span>
        </button>
      </div>
    </div>

    <!-- Matrix Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[11px]">
              <th class="py-3 px-4 w-72">Mã & Nội dung chuẩn</th>
              <th v-for="lang in supportedLanguages" :key="lang.code" class="py-3 px-3 text-center min-w-[130px]">
                <div class="flex flex-col items-center space-y-0.5">
                  <span class="text-sm">{{ getFlag(lang.code) }}</span>
                  <span class="font-bold text-slate-800">{{ lang.name }}</span>
                  <span
                    v-if="!lang.isPrimary"
                    class="text-[9px] font-semibold text-amber-700 bg-amber-100/80 px-1.5 py-0.2 rounded"
                  >
                    Chưa rà
                  </span>
                  <span
                    v-else
                    class="text-[9px] font-semibold text-sky-700 bg-sky-100/80 px-1.5 py-0.2 rounded"
                  >
                    Chuẩn hóa
                  </span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 text-slate-800">
            <tr v-if="loading" class="text-center py-8">
              <td :colspan="1 + supportedLanguages.length" class="py-8 text-slate-400">
                <div class="flex items-center justify-center space-x-2">
                  <RotateCw class="w-4 h-4 animate-spin text-sky-600" />
                  <span>Đang tải danh sách bản dịch...</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="filteredMatrix.length === 0" class="text-center py-8">
              <td :colspan="1 + supportedLanguages.length" class="py-8 text-slate-400">
                Không tìm thấy nội dung phù hợp với điều kiện lọc.
              </td>
            </tr>
            <tr
              v-else
              v-for="item in filteredMatrix"
              :key="item.maNoiDung"
              class="hover:bg-slate-50/70 transition"
            >
              <!-- Info Column -->
              <td class="py-3.5 px-4 align-top border-r border-slate-100">
                <div class="space-y-1">
                  <div class="flex items-center space-x-2">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide"
                      :class="item.loai === 'CHINH_SACH' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'"
                    >
                      {{ item.loai === 'CHINH_SACH' ? 'CHÍNH SÁCH' : 'MẪU EMAIL' }}
                    </span>
                    <span class="font-mono text-[11px] font-bold text-slate-600">
                      {{ item.maNoiDung }}
                    </span>
                  </div>
                  <p class="font-bold text-slate-900 text-xs">{{ item.tieuDe }}</p>
                  <p class="text-[11px] text-slate-500 leading-snug">{{ item.moTa }}</p>

                  <div v-if="item.bienBatBuoc && item.bienBatBuoc.length > 0" class="pt-1 flex flex-wrap gap-1">
                    <span
                      v-for="b in item.bienBatBuoc"
                      :key="b"
                      class="text-[10px] font-mono bg-slate-100 text-slate-700 px-1 py-0.2 rounded border border-slate-200"
                    >
                      {{ b }}
                    </span>
                  </div>
                </div>
              </td>

              <!-- 7 Languages Cells -->
              <td
                v-for="lang in supportedLanguages"
                :key="lang.code"
                class="py-3 px-2.5 align-top text-center border-r border-slate-100 last:border-r-0 cursor-pointer hover:bg-sky-50/50 transition group"
                @click="openEditor(item, lang.code)"
              >
                <div class="h-full flex flex-col items-center justify-between space-y-2 p-1.5 rounded-xl border border-transparent group-hover:border-sky-200 group-hover:bg-white group-hover:shadow-sm transition">
                  <div v-if="item.banDich && item.banDich[lang.code]" class="space-y-1 w-full">
                    <div class="flex items-center justify-center space-x-1">
                      <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                      <span class="text-[11px] font-semibold text-emerald-800">Đã dịch</span>
                    </div>
                    <p class="text-[10px] text-slate-400 font-mono">
                      {{ (item.banDich[lang.code] || '').length }} ký tự
                    </p>
                    <p class="text-[10px] text-slate-600 line-clamp-2 text-left px-1 bg-slate-50/60 rounded p-1 font-mono">
                      {{ item.banDich[lang.code] }}
                    </p>
                  </div>
                  <div v-else class="space-y-1 w-full py-2">
                    <span class="w-2 h-2 rounded-full bg-slate-300 inline-block"></span>
                    <p class="text-[11px] text-slate-400 italic">Chưa có</p>
                  </div>

                  <button
                    type="button"
                    class="mt-1 text-[11px] font-semibold text-sky-600 group-hover:text-sky-700 group-hover:underline flex items-center space-x-1"
                  >
                    <Edit3 class="w-3 h-3" />
                    <span>Chỉnh sửa</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit Modal with Editor & Live Preview -->
    <div
      v-if="showModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
      @click.self="closeModal"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in duration-150 my-6">
        <!-- Modal Header -->
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <span class="text-2xl">{{ getFlag(currentLang) }}</span>
            <div>
              <div class="flex items-center space-x-2">
                <h3 class="text-base font-bold text-slate-900">
                  {{ currentItem?.tieuDe }}
                </h3>
                <span class="text-xs font-mono font-semibold text-slate-500 bg-slate-200 px-2 py-0.5 rounded">
                  {{ currentItem?.maNoiDung }}
                </span>
              </div>
              <p class="text-xs text-slate-500">
                Ngôn ngữ: <strong class="text-slate-800">{{ getLangName(currentLang) }} ({{ currentLang }})</strong>
                <span v-if="isUnreviewed(currentLang)" class="ml-2 text-amber-700 font-semibold bg-amber-100 px-1.5 py-0.2 rounded text-[10px]">
                  Bản dịch chưa rà
                </span>
              </p>
            </div>
          </div>
          <button
            @click="closeModal"
            class="text-slate-400 hover:text-slate-600 text-lg font-bold p-1 rounded-lg hover:bg-slate-200/50"
          >
            ✕
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          <!-- Warning for non-primary language -->
          <div
            v-if="isUnreviewed(currentLang)"
            class="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs flex items-start space-x-2"
          >
            <AlertTriangle class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p class="font-bold">Cảnh báo hiệu đính (BR-55):</p>
              <p>
                Đây là bản dịch mở rộng chưa được kiểm duyệt bởi chuyên viên bản ngữ. Khi áp dụng vào thực tế, vui lòng đối chiếu chuẩn xác với văn bản gốc tiếng Việt.
              </p>
            </div>
          </div>

          <!-- Variable Pills Helper (If email template) -->
          <div v-if="currentItem?.bienBatBuoc && currentItem.bienBatBuoc.length > 0" class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-slate-700">Các biến thay thế bắt buộc (nhấp vào biến để chèn):</span>
              <span class="text-[11px] text-slate-500">
                Đã có: {{ countPresentVars() }}/{{ currentItem.bienBatBuoc.length }}
              </span>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="v in currentItem.bienBatBuoc"
                :key="v"
                type="button"
                @click="insertVariable(v)"
                class="px-2 py-1 rounded text-xs font-mono font-semibold transition flex items-center space-x-1"
                :class="isVarPresent(v) ? 'bg-emerald-100 text-emerald-800 border border-emerald-200 hover:bg-emerald-200' : 'bg-rose-100 text-rose-800 border border-rose-200 hover:bg-rose-200'"
                :title="isVarPresent(v) ? 'Biến đã có trong văn bản' : 'Nhấp để chèn biến đang thiếu'"
              >
                <span>{{ v }}</span>
                <Check v-if="isVarPresent(v)" class="w-3 h-3 text-emerald-600" />
                <span v-else class="text-[10px] text-rose-600 font-bold">+</span>
              </button>
            </div>
          </div>

          <!-- View Mode Toggle: Edit vs Split Preview -->
          <div class="flex items-center justify-between border-b border-slate-200 pb-2">
            <div class="flex items-center space-x-2">
              <button
                type="button"
                @click="viewMode = 'SPLIT'"
                class="px-3 py-1 text-xs font-semibold rounded-lg transition"
                :class="viewMode === 'SPLIT' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              >
                Xem song song (Xem trước & Soạn)
              </button>
              <button
                type="button"
                @click="viewMode = 'EDITOR'"
                class="px-3 py-1 text-xs font-semibold rounded-lg transition"
                :class="viewMode === 'EDITOR' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              >
                Chỉ soạn thảo
              </button>
              <button
                type="button"
                @click="viewMode = 'PREVIEW'"
                class="px-3 py-1 text-xs font-semibold rounded-lg transition"
                :class="viewMode === 'PREVIEW' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              >
                Chỉ xem trước
              </button>
            </div>

            <div class="text-xs text-slate-500 font-mono">
              {{ editorText.length }} ký tự
            </div>
          </div>

          <!-- Editor / Preview Grid -->
          <div
            class="grid gap-4"
            :class="viewMode === 'SPLIT' ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'"
          >
            <!-- Editor Textarea -->
            <div v-show="viewMode !== 'PREVIEW'" class="space-y-1.5">
              <label class="block text-xs font-bold text-slate-700">
                Nội dung văn bản (Plain Text) *
              </label>
              <textarea
                ref="textareaRef"
                v-model="editorText"
                rows="14"
                placeholder="Nhập nội dung bản dịch tại đây..."
                class="w-full p-3 font-mono text-xs bg-slate-50 border border-slate-300 rounded-xl focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none leading-relaxed transition"
              ></textarea>
              <p v-if="currentLang === 'vi'" class="text-[11px] text-amber-700">
                * Bắt buộc có nội dung tiếng Việt theo quy định BR-55.
              </p>
            </div>

            <!-- Live Preview -->
            <div v-show="viewMode !== 'EDITOR'" class="space-y-1.5">
              <div class="flex items-center justify-between">
                <label class="block text-xs font-bold text-slate-700">
                  Xem trước hiển thị thực tế (Simulated Preview)
                </label>
                <span class="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                  Dữ liệu giả lập
                </span>
              </div>
              <div class="w-full h-[320px] p-4 bg-slate-100/70 border border-slate-200 rounded-xl overflow-y-auto font-sans text-xs text-slate-800 whitespace-pre-wrap leading-relaxed shadow-inner">
                {{ simulatedPreview }}
              </div>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <button
            type="button"
            @click="resetToDefault"
            class="px-3.5 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold text-xs rounded-xl transition"
          >
            Khôi phục mặc định
          </button>

          <div class="flex items-center space-x-2">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-xl transition"
            >
              Hủy
            </button>
            <button
              type="button"
              @click="saveTranslation"
              :disabled="saving || (currentLang === 'vi' && !editorText.trim())"
              class="px-5 py-2 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 text-white font-semibold text-xs rounded-xl shadow-sm transition flex items-center space-x-1.5"
            >
              <RotateCw v-if="saving" class="w-3.5 h-3.5 animate-spin" />
              <span>Xác nhận lưu</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import apiClient from '../../api/client';
import {
  Globe,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Search,
  RotateCw,
  Edit3,
  Check,
} from 'lucide-vue-next';

const supportedLanguages = [
  { code: 'vi', name: 'Tiếng Việt', isPrimary: true },
  { code: 'en', name: 'English', isPrimary: true },
  { code: 'zh-CN', name: '中文（简体）', isPrimary: false },
  { code: 'ko', name: '한국어', isPrimary: false },
  { code: 'ja', name: '日本語', isPrimary: false },
  { code: 'es', name: 'Español', isPrimary: false },
  { code: 'fr', name: 'Français', isPrimary: false },
];

const flags = {
  vi: '🇻🇳',
  en: '🇬🇧',
  'zh-CN': '🇨🇳',
  ko: '🇰🇷',
  ja: '🇯🇵',
  es: '🇪🇸',
  fr: '🇫🇷',
};

const dummyVariables = {
  '{ma_don}': 'SG20261124-001',
  '{ten_khach}': 'Nguyễn Văn A',
  '{ten_hang}': 'Superior City View',
  '{thoi_gian_nhan}': '14:00 ngày 25/11/2026',
  '{thoi_gian_tra}': '12:00 ngày 27/11/2026',
  '{tong_tien}': '2.052.000 ₫',
  '{link_tra_cuu}': 'https://saigonstar.vn/tra-cuu?code=SG20261124-001',
  '{thong_tin_cu}': 'Nhận 25/11/2026 - Standard',
  '{thong_tin_moi}': 'Nhận 26/11/2026 - Superior',
  '{chenh_lech}': '+400.000 ₫',
  '{tien_hoan}': '2.052.000 ₫',
  '{phuong_thuc}': 'Thẻ tín dụng Visa (...1234)',
  '{thoi_gian_du_kien}': '3 - 5 ngày làm việc',
  '{link_dat_lai}': 'https://saigonstar.vn/dat-phong',
  '{noi_dung_xu_ly}': 'Đơn của quý khách đã được xác nhận bù do còn phòng trống (theo quy tắc BR-19).',
};

// State
const matrixList = ref([]);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const searchKeyword = ref('');
const activeFilter = ref('ALL');

// Modal State
const showModal = ref(false);
const currentItem = ref(null);
const currentLang = ref('vi');
const editorText = ref('');
const viewMode = ref('SPLIT'); // 'EDITOR' | 'PREVIEW' | 'SPLIT'
const textareaRef = ref(null);

const getFlag = (code) => flags[code] || '🌐';

const getLangName = (code) => {
  const found = supportedLanguages.find((l) => l.code === code);
  return found ? found.name : code;
};

const isUnreviewed = (code) => {
  const found = supportedLanguages.find((l) => l.code === code);
  return found ? !found.isPrimary : false;
};

const countByType = (type) => {
  return matrixList.value.filter((item) => item.loai === type).length;
};

const filteredMatrix = computed(() => {
  return matrixList.value.filter((item) => {
    if (activeFilter.value !== 'ALL' && item.loai !== activeFilter.value) {
      return false;
    }
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.toLowerCase().trim();
      const matchMa = item.maNoiDung.toLowerCase().includes(kw);
      const matchTitle = item.tieuDe.toLowerCase().includes(kw);
      if (!matchMa && !matchTitle) return false;
    }
    return true;
  });
});

const isVarPresent = (v) => {
  return editorText.value.includes(v);
};

const countPresentVars = () => {
  if (!currentItem.value || !currentItem.value.bienBatBuoc) return 0;
  return currentItem.value.bienBatBuoc.filter((v) => editorText.value.includes(v)).length;
};

const simulatedPreview = computed(() => {
  let text = editorText.value || '';
  for (const [placeholder, sample] of Object.entries(dummyVariables)) {
    text = text.replaceAll(placeholder, sample);
  }
  return text;
});

const insertVariable = (variable) => {
  if (!textareaRef.value) {
    editorText.value += variable;
    return;
  }
  const el = textareaRef.value;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const original = editorText.value;
  editorText.value = original.substring(0, start) + variable + original.substring(end);
  // Restore focus and cursor position
  setTimeout(() => {
    el.focus();
    el.setSelectionRange(start + variable.length, start + variable.length);
  }, 0);
};

const fetchTranslations = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.get('/translations', { params: { lang: '' } });
    matrixList.value = res || [];
  } catch (err) {
    errorMessage.value =
      err.response?.data?.detail || err.message || 'Không thể tải danh sách bản dịch. Vui lòng thử lại.';
  } finally {
    loading.value = false;
  }
};

const openEditor = (item, langCode) => {
  currentItem.value = item;
  currentLang.value = langCode;
  editorText.value = (item.banDich && item.banDich[langCode]) || '';
  viewMode.value = 'SPLIT';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  currentItem.value = null;
};

const resetToDefault = () => {
  if (confirm('Khôi phục nội dung về bản mẫu hệ thống chuẩn?')) {
    // Reset to default if known
    if (currentItem.value && currentItem.value.banDich) {
      editorText.value = currentItem.value.banDich[currentLang.value] || '';
    }
  }
};

const saveTranslation = async () => {
  if (!currentItem.value) return;

  // Validate Vietnamese non-empty per BR-55
  if (currentLang.value === 'vi' && !editorText.value.trim()) {
    errorMessage.value = 'Bản dịch tiếng Việt có giá trị pháp lý khi tranh chấp (BR-55), không được để trống.';
    return;
  }

  // Validate required variables for email
  if (currentItem.value.bienBatBuoc && currentItem.value.bienBatBuoc.length > 0) {
    const missing = currentItem.value.bienBatBuoc.filter((v) => !editorText.value.includes(v));
    if (missing.length > 0) {
      errorMessage.value = `Mẫu email thiếu các biến bắt buộc: ${missing.join(', ')}`;
      return;
    }
  }

  saving.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.put(
      `/translations/${currentItem.value.maNoiDung}/${currentLang.value}`,
      { noiDung: editorText.value }
    );

    successMessage.value = `Cập nhật bản dịch ${currentItem.value.maNoiDung} [${getLangName(currentLang.value)}] thành công.`;
    if (res?.canhBao) {
      successMessage.value += ` (${res.canhBao})`;
    }

    // Update local state in matrix
    if (currentItem.value.banDich) {
      currentItem.value.banDich[currentLang.value] = editorText.value;
    }

    closeModal();
  } catch (err) {
    errorMessage.value =
      err.response?.data?.detail || err.message || 'Lỗi khi lưu bản dịch. Vui lòng kiểm tra lại.';
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  fetchTranslations();
});
</script>
