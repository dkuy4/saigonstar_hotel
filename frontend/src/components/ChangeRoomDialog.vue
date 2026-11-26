<template>
  <!-- Backdrop -->
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
    @click.self="close"
  >
    <!-- Dialog card -->
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
        <div>
          <h2 class="text-base font-black text-slate-900">🔄 Đổi phòng do sự cố</h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Phòng cũ → Bảo trì - Giá đơn giữ nguyên (BR-36)
          </p>
        </div>
        <button
          @click="close"
          class="text-slate-400 hover:text-slate-700 text-xl leading-none transition"
          aria-label="Đóng"
        >×</button>
      </div>

      <!-- Body (scrollable) -->
      <div class="overflow-y-auto flex-1 px-6 py-5 space-y-5">

        <!-- Current room info -->
        <div v-if="currentRoomNumber" class="text-xs bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center space-x-2">
          <span class="text-amber-500 text-base">⚠️</span>
          <div>
            <span class="font-semibold text-amber-800">Phòng hiện tại:</span>
            <span class="font-mono text-amber-900 ml-1">{{ currentRoomNumber }}</span>
            <span class="text-amber-700 ml-1">– sẽ được chuyển sang Bảo trì ngay.</span>
          </div>
        </div>

        <!-- Error banner -->
        <div
          v-if="error"
          class="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-start space-x-2"
        >
          <span class="text-rose-500 text-base mt-0.5">⚠️</span>
          <span>{{ error }}</span>
        </div>

        <!-- Suggested rooms -->
        <div>
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
            Phòng đề xuất
            <span v-if="loadingSuggestions" class="ml-1 text-slate-400">(Đang tải...)</span>
            <span v-else-if="suggestions.length === 0 && !loadingSuggestions" class="ml-1 text-rose-400">(Không có phòng trống cùng hạng)</span>
          </div>

          <!-- Loading skeleton -->
          <div v-if="loadingSuggestions" class="space-y-2">
            <div v-for="i in 3" :key="i"
                 class="h-10 bg-slate-100 animate-pulse rounded-xl" />
          </div>

          <!-- Room list -->
          <div v-else class="space-y-2">
            <button
              v-for="room in suggestions"
              :key="room.room_id"
              @click="selectRoom(room)"
              :class="[
                'w-full text-left px-4 py-3 rounded-xl border text-xs font-medium transition',
                selectedRoomId === room.room_id
                  ? 'border-sky-500 bg-sky-50 text-sky-900 ring-1 ring-sky-400'
                  : 'border-slate-200 bg-white hover:border-sky-300 hover:bg-sky-50 text-slate-700'
              ]"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <span class="text-base">🛏️</span>
                  <div>
                    <span class="font-mono font-bold text-sm">{{ room.room_number }}</span>
                    <span class="text-slate-500 ml-2">Tầng {{ room.floor }}</span>
                  </div>
                </div>
                <span
                  v-if="selectedRoomId === room.room_id"
                  class="text-sky-600 font-bold text-xs"
                >✓ Đã chọn</span>
              </div>
            </button>

            <!-- No suggestions placeholder -->
            <div
              v-if="suggestions.length === 0"
              class="text-center py-6 text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl"
            >
              Không có phòng cùng hạng còn trống. Vui lòng nhập mã phòng thủ công bên dưới.
            </div>
          </div>

          <!-- Manual room ID input (fallback) -->
          <div class="mt-3">
            <label class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Hoặc nhập ID phòng thủ công
            </label>
            <input
              v-model.number="manualRoomId"
              type="number"
              min="1"
              placeholder="VD: 12"
              @input="selectedRoomId = manualRoomId || null"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
          </div>
        </div>

        <!-- Reason input – REQUIRED -->
        <div>
          <label class="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
            Lý do sự cố
            <span class="text-rose-500 ml-0.5">*</span>
          </label>
          <textarea
            v-model="reason"
            rows="3"
            maxlength="500"
            placeholder="Mô tả sự cố: vòi nước bị rò rỉ, điều hòa hỏng, v.v. (bắt buộc)"
            class="w-full px-3 py-2 border rounded-xl text-xs focus:outline-none focus:ring-2 transition resize-none"
            :class="reasonTouched && !reason.trim()
              ? 'border-rose-400 focus:ring-rose-300 bg-rose-50'
              : 'border-slate-200 focus:ring-sky-400 bg-white'"
            @blur="reasonTouched = true"
          />
          <div class="flex justify-between mt-1">
            <span
              v-if="reasonTouched && !reason.trim()"
              class="text-rose-500 text-[11px] font-semibold"
            >Lý do sự cố là bắt buộc (ghi vào nhật ký).</span>
            <span class="text-slate-400 text-[11px] ml-auto">{{ reason.length }}/500</span>
          </div>
        </div>

        <!-- Info notice -->
        <div class="text-[11px] text-slate-500 bg-slate-50 rounded-xl px-4 py-3 border border-slate-200 leading-relaxed">
          <strong class="text-slate-700">Lưu ý:</strong>
          Sau khi xác nhận, phòng cũ sẽ chuyển sang trạng thái
          <span class="font-semibold text-amber-700">Bảo trì</span> ngay lập tức.
          Khách sẽ được chuyển sang phòng mới và
          <span class="font-semibold text-emerald-700">giá đơn được giữ nguyên</span> (BR-36).
          Lý do sự cố được ghi vào nhật ký hệ thống (AC-13).
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-slate-200 flex items-center justify-end space-x-3">
        <button
          @click="close"
          :disabled="submitting"
          class="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
        >Hủy bỏ</button>

        <button
          @click="submit"
          :disabled="!canSubmit || submitting"
          class="px-5 py-2 text-xs font-bold text-white rounded-xl transition flex items-center space-x-1.5"
          :class="canSubmit && !submitting
            ? 'bg-amber-600 hover:bg-amber-500 shadow-sm'
            : 'bg-slate-300 cursor-not-allowed'"
        >
          <span v-if="submitting" class="animate-spin">⏳</span>
          <span>{{ submitting ? 'Đang xử lý...' : 'Xác nhận đổi phòng' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import apiClient from '../api/client';

// Props & emits
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  bookingId: { type: Number, required: true },
  currentRoomNumber: { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue', 'success']);

// State
const suggestions = ref([]);
const loadingSuggestions = ref(false);
const selectedRoomId = ref(null);
const manualRoomId = ref(null);
const reason = ref('');
const reasonTouched = ref(false);
const error = ref('');
const submitting = ref(false);

// Computed
const canSubmit = computed(() =>
  (selectedRoomId.value || manualRoomId.value) &&
  reason.value.trim().length >= 3
);

// Watchers
watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      await loadSuggestions();
    } else {
      reset();
    }
  }
);

// Methods
function close() {
  emit('update:modelValue', false);
}

function reset() {
  suggestions.value = [];
  selectedRoomId.value = null;
  manualRoomId.value = null;
  reason.value = '';
  reasonTouched.value = false;
  error.value = '';
  submitting.value = false;
  loadingSuggestions.value = false;
}

function selectRoom(room) {
  selectedRoomId.value = room.room_id;
  manualRoomId.value = null;
}

async function loadSuggestions() {
  loadingSuggestions.value = true;
  error.value = '';
  try {
    const res = await apiClient.get(`/bookings/${props.bookingId}/suggested-rooms`);
    suggestions.value = Array.isArray(res) ? res : [];
    // Pre-select first suggestion
    if (suggestions.value.length > 0) {
      selectedRoomId.value = suggestions.value[0].room_id;
    }
  } catch (err) {
    suggestions.value = [];
    // Non-fatal: user can still use manual input
    error.value = err.message || 'Không thể tải danh sách phòng gợi ý.';
  } finally {
    loadingSuggestions.value = false;
  }
}

async function submit() {
  reasonTouched.value = true;
  if (!canSubmit.value) return;

  const roomId = selectedRoomId.value || manualRoomId.value;
  if (!roomId) {
    error.value = 'Vui lòng chọn hoặc nhập ID phòng mới.';
    return;
  }
  if (reason.value.trim().length < 3) {
    error.value = 'Lý do sự cố phải có ít nhất 3 ký tự.';
    return;
  }

  submitting.value = true;
  error.value = '';
  try {
    const res = await apiClient.post(`/bookings/${props.bookingId}/change-room`, {
      newRoomId: roomId,
      reason: reason.value.trim(),
    });
    emit('success', res);
    close();
  } catch (err) {
    // err.code is the backend error code (ASCII, no Vietnamese)
    // err.message is the i18n-translated user-friendly message from client.js
    error.value = err.message || 'Đổi phòng thất bại. Vui lòng thử lại.';
    // If the API returns alternative suggestions in the error data, refresh list
    if (err.data?.suggested_rooms?.length) {
      suggestions.value = err.data.suggested_rooms;
      selectedRoomId.value = null;
    }
  } finally {
    submitting.value = false;
  }
}
</script>
