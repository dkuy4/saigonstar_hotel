<template>
  <div
    @click="$emit('select', room)"
    :class="[
      'group relative p-3 rounded-xl border transition-all duration-150 cursor-pointer flex flex-col justify-between text-left select-none min-h-[105px]',
      isSelected
        ? 'ring-2 ring-amberbrown-500 shadow-sm border-amberbrown-500 bg-amberbrown-500/10'
        : 'hover:border-darkbeige-700 hover:shadow-sm bg-white border-slate-200/90',
      statusBorderClass
    ]"
  >
    <!-- Top row: Room Number & Type & Status -->
    <div class="space-y-1.5">
      <div class="flex flex-wrap items-center justify-between gap-1.5">
        <div class="flex items-baseline space-x-1.5 min-w-0">
          <span class="text-base font-black font-mono tracking-tight text-slate-900 group-hover:text-amberbrown-400 transition">
            {{ room.roomNumber }}
          </span>
          <span :class="roomTypeBadgeClass" class="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase flex-shrink-0">
            {{ roomTypeShort }}
          </span>
        </div>
        <StatusBadge :status="room.status" class="whitespace-nowrap flex-shrink-0" />
      </div>

      <!-- Current Booking info if any -->
      <div v-if="room.currentBooking" class="bg-slate-50/80 rounded-lg p-2 border border-slate-100 space-y-0.5 text-xs">
        <div class="flex items-center justify-between text-[11px] gap-1">
          <span class="font-mono font-bold text-sky-700 truncate">
            {{ room.currentBooking.bookingCode }}
          </span>
          <span class="text-[9px] text-slate-500 uppercase font-semibold flex-shrink-0">
            {{ formatBookingStatus(room.currentBooking.bookingStatus) }}
          </span>
        </div>
        <div class="text-[10px] text-slate-500 leading-tight">
          {{ formatTimeShort(room.currentBooking.from) }} - {{ formatTimeShort(room.currentBooking.to) }}
        </div>
      </div>

      <!-- Empty state text if TRONG -->
      <div v-else-if="room.status === 'TRONG'" class="py-1.5 text-center text-slate-400 text-xs font-medium">
        Phòng sẵn sàng
      </div>

      <!-- Cleaning or Maintenance text -->
      <div v-else-if="room.status === 'DANG_DON'" class="py-1.5 text-center text-purple-700 text-xs font-medium">
        Đang dọn phòng
      </div>
      <div v-else-if="room.status === 'BAO_TRI'" class="py-1.5 text-center text-rose-700 text-xs font-medium">
        Đang bảo trì
      </div>
    </div>

    <!-- Bottom row: Next booking badge if present -->
    <div v-if="room.nextBooking" class="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500">
      <span class="flex items-center space-x-1 min-w-0 truncate">
        <span class="text-slate-400">Kế:</span>
        <strong class="font-mono text-slate-700 truncate">{{ room.nextBooking.bookingCode }}</strong>
      </span>
      <span class="flex-shrink-0 text-slate-400 font-medium pl-1">{{ formatTimeShort(room.nextBooking.from) }}</span>
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

const formatBookingStatus = (st) => {
  switch (st) {
    case 'HOLD': return 'Giữ chỗ';
    case 'CONFIRMED': return 'Đã xác nhận';
    case 'CHECKED_IN': return 'Đang ở';
    case 'CHECKED_OUT': return 'Đã trả';
    case 'CANCELLED': return 'Đã hủy';
    case 'EXPIRED': return 'Hết hạn';
    case 'NO_SHOW': return 'Vắng mặt';
    default: return st || '';
  }
};
</script>
