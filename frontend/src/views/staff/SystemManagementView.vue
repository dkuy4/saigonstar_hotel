<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div>
        <div class="flex items-center space-x-2">
          <h1 class="text-2xl font-black text-slate-800 tracking-tight">Quản lý tác vụ nền & Hệ thống</h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-600 border border-indigo-200/60">
            F13 Quản trị
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Giám sát tác vụ nền tự động (Hết hạn giữ chỗ, No-show, Đối soát phòng), quản lý tỷ giá ngoại tệ và cảnh báo sai lệch (FR-20, FR-52, NFR-03, NFR-27)
        </p>
      </div>

      <div class="flex items-center space-x-3">
        <button
          @click="openRateModal"
          class="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-bold transition flex items-center space-x-1.5"
        >
          <Coins class="w-4 h-4 text-indigo-600" />
          <span>Cập nhật tỷ giá</span>
        </button>
        <button
          @click="loadAll"
          :disabled="loading"
          class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 disabled:opacity-50 shadow-sm"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          <span>Làm mới</span>
        </button>
      </div>
    </div>

    <!-- Alert Messages -->
    <div v-if="successMsg" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-2xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0" />
        <span>{{ successMsg }}</span>
      </div>
      <button @click="successMsg = ''" class="text-emerald-500 hover:text-emerald-700">&times;</button>
    </div>

    <div v-if="errorMsg" class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <AlertCircle class="w-4 h-4 text-rose-600 shrink-0" />
        <span>{{ errorMsg }}</span>
      </div>
      <button @click="errorMsg = ''" class="text-rose-500 hover:text-rose-700">&times;</button>
    </div>

    <!-- Section 1: Background Jobs Grid -->
    <div>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-base font-bold text-slate-800">Tiến trình tác vụ nền định kỳ</h2>
          <p class="text-xs text-slate-400">Các tác vụ tự động thực thi bởi backend scheduler thay thế DBMS_SCHEDULER</p>
        </div>
        <span class="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg">
          {{ jobs.length }} tác vụ đã đăng ký
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="job in jobs"
          :key="job.id"
          class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between hover:border-slate-200 transition"
        >
          <div>
            <div class="flex items-start justify-between gap-3 mb-2">
              <div>
                <h3 class="font-bold text-slate-800 text-sm">{{ job.name }}</h3>
                <span class="font-mono text-[11px] text-slate-400 font-semibold">{{ job.id }}</span>
              </div>
              <span
                class="px-2.5 py-1 rounded-full text-[11px] font-bold border shrink-0"
                :class="getStatusBadgeClass(job.lastStatus)"
              >
                {{ formatStatus(job.lastStatus) }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mb-4 leading-relaxed">{{ job.description }}</p>

            <!-- Metrics grid -->
            <div class="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4">
              <div>
                <span class="text-slate-400 block text-[10px] uppercase font-semibold">Chu kỳ lặp</span>
                <span class="font-semibold text-slate-700">{{ formatInterval(job.intervalSeconds) }}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-[10px] uppercase font-semibold">Lần chạy gần nhất</span>
                <span class="font-semibold text-slate-700">{{ formatDateTime(job.lastRun) }}</span>
              </div>
              <div>
                <span class="text-slate-400 block text-[10px] uppercase font-semibold">Thời lượng</span>
                <span class="font-semibold text-slate-700">{{ job.lastDurationMs }} ms</span>
              </div>
              <div>
                <span class="text-slate-400 block text-[10px] uppercase font-semibold">Lần chạy kế tiếp</span>
                <span class="font-semibold text-slate-700">{{ formatDateTime(job.nextRun) }}</span>
              </div>
            </div>

            <!-- Last result or error -->
            <div v-if="job.lastResult" class="p-2.5 bg-emerald-50/70 border border-emerald-100 rounded-xl text-[11px] text-emerald-800 mb-4 flex items-start space-x-1.5">
              <CheckCircle2 class="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
              <span>{{ job.lastResult }}</span>
            </div>
            <div v-if="job.lastError" class="p-2.5 bg-rose-50 border border-rose-100 rounded-xl text-[11px] text-rose-800 mb-4 flex items-start space-x-1.5">
              <AlertCircle class="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
              <span class="font-mono break-all">{{ job.lastError }}</span>
            </div>
          </div>

          <!-- Action Button -->
          <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-[11px] text-slate-400 font-medium">
              Đã chạy: <strong>{{ job.totalRuns }}</strong> lần ({{ job.totalSuccess }} thành công)
            </span>
            <button
              @click="runJob(job.id)"
              :disabled="runningJobs[job.id]"
              class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-50 flex items-center space-x-1.5 shadow-sm"
            >
              <RefreshCw v-if="runningJobs[job.id]" class="w-3.5 h-3.5 animate-spin" />
              <Play v-else class="w-3.5 h-3.5" />
              <span>{{ runningJobs[job.id] ? 'Đang chạy...' : 'Chạy ngay' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 2: Exchange Rates & Discrepancies Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Exchange Rates Table -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center space-x-2">
              <Coins class="w-5 h-5 text-indigo-600" />
              <h2 class="text-base font-bold text-slate-800">Tỷ giá ngoại tệ hiện hành (FR-10)</h2>
            </div>
            <button
              @click="runJob('JOB_DONG_BO_TY_GIA')"
              :disabled="runningJobs['JOB_DONG_BO_TY_GIA']"
              class="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
            >
              <RefreshCw class="w-3 h-3" :class="{ 'animate-spin': runningJobs['JOB_DONG_BO_TY_GIA'] }" />
              <span>Đồng bộ ngân hàng</span>
            </button>
          </div>
          <p class="text-xs text-slate-500 mb-4">
            Bảng tỷ giá quy đổi phục vụ thanh toán quốc tế và chuyển đổi ngoại tệ trực tiếp trên website.
          </p>

          <div class="overflow-x-auto rounded-xl border border-slate-100">
            <table class="w-full text-xs text-left">
              <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b border-slate-100">
                <tr>
                  <th class="py-2.5 px-3">Mã ngoại tệ</th>
                  <th class="py-2.5 px-3 text-right">Tỷ giá (VND)</th>
                  <th class="py-2.5 px-3 text-right">Ngày cập nhật</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 font-medium">
                <tr v-for="rate in exchangeRates" :key="rate.currency" class="hover:bg-slate-50/60">
                  <td class="py-2.5 px-3 flex items-center space-x-2 font-bold text-slate-800">
                    <span class="text-base">{{ getCurrencyFlag(rate.currency) }}</span>
                    <span>{{ rate.currency }}</span>
                  </td>
                  <td class="py-2.5 px-3 text-right font-black text-indigo-600">
                    {{ formatCurrencyNumber(rate.rate_vnd || rate.rateVnd) }} đ
                  </td>
                  <td class="py-2.5 px-3 text-right text-slate-500">
                    {{ rate.updated_at || rate.updatedAt }}
                  </td>
                </tr>
                <tr v-if="exchangeRates.length === 0">
                  <td colspan="3" class="text-center py-4 text-slate-400">Chưa có dữ liệu tỷ giá</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-100 flex justify-end">
          <button
            @click="openRateModal"
            class="px-4 py-2 border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-bold text-slate-700 transition"
          >
            Chỉnh sửa tỷ giá thủ công
          </button>
        </div>
      </div>

      <!-- Room Discrepancies Table (NFR-03) -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center space-x-2">
              <ShieldAlert class="w-5 h-5 text-amber-600" />
              <h2 class="text-base font-bold text-slate-800">Đối soát phòng và lịch đặt (NFR-03)</h2>
            </div>
            <span
              class="px-2 py-0.5 rounded-full text-[11px] font-bold"
              :class="discrepancies.length > 0 ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
            >
              {{ discrepancies.length }} phòng lệch
            </span>
          </div>
          <p class="text-xs text-slate-500 mb-4">
            Phát hiện sự không nhất quán giữa trạng thái thực tế phòng (PHONG) và đơn lưu trú (CHECKED_IN).
          </p>

          <div class="overflow-x-auto rounded-xl border border-slate-100">
            <table class="w-full text-xs text-left">
              <thead class="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] border-b border-slate-100">
                <tr>
                  <th class="py-2.5 px-3">Phòng</th>
                  <th class="py-2.5 px-3">Trạng thái phòng</th>
                  <th class="py-2.5 px-3">Mô tả sai lệch</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="d in discrepancies" :key="d.roomId" class="hover:bg-amber-50/40">
                  <td class="py-2.5 px-3 font-bold text-slate-800">
                    Phòng {{ d.roomNumber }}
                  </td>
                  <td class="py-2.5 px-3">
                    <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-700">
                      {{ d.currentStatus }}
                    </span>
                  </td>
                  <td class="py-2.5 px-3 text-rose-600 font-medium text-[11px]">
                    {{ d.description }}
                  </td>
                </tr>
                <tr v-if="discrepancies.length === 0">
                  <td colspan="3" class="text-center py-6 text-emerald-600 font-medium">
                    ✓ Hoàn hảo: Tất cả các phòng khớp đúng với lịch lưu trú khách
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-100 flex justify-between items-center">
          <span class="text-[11px] text-slate-400">Ghi log LECH_TRANG_THAI vào nhật ký kiểm toán</span>
          <router-link
            to="/nv/so-do-phong"
            class="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
          >
            <span>Xem sơ đồ phòng</span>
            <span>&rarr;</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Modal Cập nhật tỷ giá thủ công (FR-10, D-37) -->
    <div v-if="showRateModal" class="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden border border-slate-100">
        <div class="px-6 py-4 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between">
          <div class="flex items-center space-x-2 text-indigo-800">
            <Coins class="w-5 h-5 text-indigo-600" />
            <h3 class="font-bold text-base">Cập nhật tỷ giá ngoại tệ thủ công</h3>
          </div>
          <button @click="showRateModal = false" class="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
        </div>

        <div class="p-6 space-y-4">
          <p class="text-xs text-slate-500">
            Nhập giá trị quy đổi sang Việt Nam Đồng (VND) cho từng loại ngoại tệ hỗ trợ.
          </p>

          <div class="space-y-3">
            <div
              v-for="item in rateEditList"
              :key="item.currency"
              class="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl border border-slate-100"
            >
              <div class="flex items-center space-x-2">
                <span class="text-lg">{{ getCurrencyFlag(item.currency) }}</span>
                <span class="font-bold text-slate-700 text-xs">{{ item.currency }}</span>
              </div>
              <div class="flex items-center space-x-2">
                <input
                  type="number"
                  v-model.number="item.rateVnd"
                  min="0.1"
                  step="0.1"
                  class="w-32 px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs text-right font-black text-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span class="text-xs text-slate-400 font-semibold">đ</span>
              </div>
            </div>
          </div>

          <div v-if="rateError" class="p-3 bg-rose-50 text-rose-600 rounded-xl text-xs border border-rose-200">
            {{ rateError }}
          </div>
        </div>

        <div class="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end space-x-2">
          <button
            type="button"
            @click="showRateModal = false"
            class="px-4 py-2 border border-slate-200 hover:bg-slate-100 rounded-xl text-xs font-semibold text-slate-600 transition"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            @click="submitManualRates"
            :disabled="savingRates"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-50 flex items-center space-x-1.5 shadow-sm"
          >
            <RefreshCw v-if="savingRates" class="w-3.5 h-3.5 animate-spin" />
            <span>{{ savingRates ? 'Đang lưu...' : 'Lưu bảng tỷ giá' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import {
  RefreshCw, Play, CheckCircle2, AlertCircle, Coins,
  ShieldAlert, Clock, Layers
} from 'lucide-vue-next';
import apiClient from '../../api/client';

const loading = ref(false);
const successMsg = ref('');
const errorMsg = ref('');

const jobs = ref([]);
const runningJobs = ref({});
const exchangeRates = ref([]);
const discrepancies = ref([]);

// Modal Edit Rates
const showRateModal = ref(false);
const savingRates = ref(false);
const rateError = ref('');
const rateEditList = ref([]);

const formatCurrencyNumber = (num) => {
  if (num === undefined || num === null) return '0';
  return Number(num).toLocaleString('vi-VN');
};

const formatInterval = (sec) => {
  if (sec === 60) return 'Mỗi 1 phút';
  if (sec === 300) return 'Mỗi 5 phút';
  if (sec >= 86400) return 'Mỗi 24 giờ';
  return `${sec} giây`;
};

const formatDateTime = (val) => {
  if (!val) return 'Chưa chạy';
  const d = new Date(val);
  return d.toLocaleString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

const getStatusBadgeClass = (status) => {
  if (status === 'SUCCESS') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (status === 'RUNNING') return 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse';
  if (status === 'ERROR') return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-slate-100 text-slate-600 border-slate-200';
};

const formatStatus = (status) => {
  if (status === 'SUCCESS') return 'Thành công';
  if (status === 'RUNNING') return 'Đang chạy';
  if (status === 'ERROR') return 'Lỗi';
  return 'Sẵn sàng';
};

const getCurrencyFlag = (curr) => {
  const flags = {
    USD: '🇺🇸',
    EUR: '🇪🇺',
    CNY: '🇨🇳',
    KRW: '🇰🇷',
    JPY: '🇯🇵'
  };
  return flags[curr] || '🌐';
};

const loadAll = async () => {
  loading.value = true;
  errorMsg.value = '';
  try {
    const [jobsRes, ratesRes, discRes] = await Promise.all([
      apiClient.get('/system/jobs'),
      apiClient.get('/exchange-rates'),
      apiClient.get('/system/discrepancies')
    ]);
    jobs.value = jobsRes || [];
    exchangeRates.value = ratesRes || [];
    discrepancies.value = discRes || [];
  } catch (err) {
    errorMsg.value = err.message || 'Lỗi khi tải thông tin hệ thống';
  } finally {
    loading.value = false;
  }
};

const runJob = async (jobId) => {
  runningJobs.value[jobId] = true;
  successMsg.value = '';
  errorMsg.value = '';
  try {
    const res = await apiClient.post(`/system/jobs/${jobId}/run`);
    successMsg.value = `Tác vụ [${jobId}] hoàn tất: ${res.result || 'Thành công'}`;
    await loadAll();
  } catch (err) {
    errorMsg.value = err.message || err.detail || `Lỗi khi chạy tác vụ ${jobId}`;
  } finally {
    runningJobs.value[jobId] = false;
  }
};

const openRateModal = () => {
  rateError.value = '';
  const currentMap = {};
  exchangeRates.value.forEach(r => {
    currentMap[r.currency] = r.rate_vnd || r.rateVnd || 0;
  });

  const currencies = ['USD', 'EUR', 'CNY', 'KRW', 'JPY'];
  rateEditList.value = currencies.map(c => ({
    currency: c,
    rateVnd: currentMap[c] || 0
  }));
  showRateModal.value = true;
};

const submitManualRates = async () => {
  savingRates.value = true;
  rateError.value = '';
  try {
    await apiClient.post('/system/exchange-rates/manual', {
      rates: rateEditList.value
    });
    successMsg.value = 'Đã cập nhật bảng tỷ giá thành công!';
    showRateModal.value = false;
    await loadAll();
  } catch (err) {
    rateError.value = err.message || err.detail || 'Lỗi khi cập nhật tỷ giá';
  } finally {
    savingRates.value = false;
  }
};

onMounted(() => {
  loadAll();
});
</script>
