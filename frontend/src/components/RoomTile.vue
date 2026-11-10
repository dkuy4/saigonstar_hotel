<template>
  <div
    @click="$emit('select', room)"
    :class="[
      'relative p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between text-left select-none',
      isSelected
        ? 'ring-2 ring-sky-500 shadow-md border-sky-400 bg-sky-50/40'
        : 'hover:shadow-md hover:border-slate-300 bg-white border-slate-200',
      statusBorderClass
    ]"
  >
    <!-- Top row: Room Number & Type & Status -->
    <div class="space-y-1.5">
      <div class="flex items-center justify-between">
        <div class="flex items-baseline space-x-1.5">
          <span class="text-lg font-black font-mono tracking-tight text-slate-900">
            {{ room.roomNumber }}
          </span>
          <span :class="roomTypeBadgeClass" class="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase">
            {{ roomTypeShort }}
          </span>
        </div>
        <StatusBadge :status="room.status" />
      </div>

      <!-- Current Booking info if any -->
      <div v-if="room.currentBooking" class="bg-slate-50 rounded-lg p-2 border border-slate-100 space-y-1 text-xs">
        <div class="flex items-center justify-between text-[11px]">
          <span class="font-mono font-bold text-sky-700">
            {{ room.currentBooking.bookingCode }}
          </span>
          <span class="text-[10px] text-slate-400 uppercase font-semibold">
            {{ room.currentBooking.bookingStatus }}
          </span>
        </div>
        <div class="text-[10px] text-slate-500 leading-tight">
          {{ formatTimeShort(room.currentBooking.from) }} - {{ formatTimeShort(room.currentBooking.to) }}
        </div>
      </div>

      <!-- Empty state text if TRONG -->
      <div v-else-if="room.status === 'TRONG'" class="py-2 text-center text-slate-400 text-xs font-medium">
        Phòng sẵn sàng
      </div>

      <!-- Cleaning or Maintenance text -->
      <div v-else-if="room.status === 'DANG_DON'" class="py-2 text-center text-purple-600 text-xs font-medium">
        Đang dọn phòng
      </div>
      <div v-else-if="room.status === 'BAO_TRI'" class="py-2 text-center text-red-600 text-xs font-medium">
        Đang bảo trì
      </div>
    </div>

    <!-- Bottom row: Next booking badge if present -->
    <div v-if="room.nextBooking" class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500">
      <span class="flex items-center space-x-1">
        <span>Kế tiếp:</span>
        <strong class="font-mono text-slate-700">{{ room.nextBooking.bookingCode }}</strong>
      </span>
      <span>{{ formatTimeShort(room.nextBooking.from) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import StatusBadge from './StatusBadge.vue';

const props = defineProps({
  room: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  }
});

defineEmits(['select']);

const roomTypeShort = computed(() => {
  switch (props.room.roomType) {
    case 'STANDARD': return 'STD';
    case 'SUPERIOR': return 'SUP';
    case 'DELUXE': return 'DLX';
    case 'SUITE': return 'SUI';
    default: return props.room.roomType;
  }
});

const roomTypeBadgeClass = computed(() => {
  switch (props.room.roomType) {
    case 'STANDARD': return 'bg-slate-100 text-slate-600';
    case 'SUPERIOR': return 'bg-sky-100 text-sky-700';
    case 'DELUXE': return 'bg-indigo-100 text-indigo-700';
    case 'SUITE': return 'bg-amber-100 text-amber-800';
    default: return 'bg-slate-100 text-slate-600';
  }
});

const statusBorderClass = computed(() => {
  switch (props.room.status) {
    case 'TRONG': return 'border-l-4 border-l-emerald-500';
    case 'DANG_O': return 'border-l-4 border-l-blue-500';
    case 'DANG_DON': return 'border-l-4 border-l-purple-500';
    case 'BAO_TRI': return 'border-l-4 border-l-red-500';
    default: return 'border-l-4 border-l-slate-400';
  }
});

const formatTimeShort = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  const day = d.getDate().toString().padStart(2, '0');
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const hours = d.getHours().toString().padStart(2, '0');
  const mins = d.getMinutes().toString().padStart(2, '0');
  return `${hours}:${mins} ${day}/${month}`;
};
</script>
