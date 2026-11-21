<template>
  <div class="max-w-5xl mx-auto space-y-6 pb-16">
    <!-- Header & Breadcrumbs -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
      <div class="space-y-1">
        <div class="flex items-center space-x-2 text-xs text-slate-500">
          <router-link to="/nv/don" class="hover:text-sky-600 transition">Quản lý đơn</router-link>
          <span>/</span>
          <span class="text-slate-800 font-semibold font-mono">{{ bookingCode || idParam }}</span>
        </div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-black font-mono text-slate-900 tracking-tight">
            {{ booking?.booking_code || 'Chi tiết đơn' }}
          </h1>
          <StatusBadge v-if="booking" :status="booking.status" />
          <span
            v-if="booking"
            class="px-2.5 py-0.5 rounded-full text-xs font-semibold"
            :class="booking.channel === 'QUAY' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-amber-50 text-amber-700 border border-amber-200'"
          >
            {{ booking.channel === 'QUAY' ? 'Tại quầy' : 'Trực tuyến' }}
          </span>
          <span
            v-if="booking"
            class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200"
          >
            {{ booking.booking_type === 'NGAY' ? 'Theo ngày' : 'Theo giờ' }}
          </span>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <button
          @click="fetchBooking"
          :disabled="loading"
          class="px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 shadow-sm"
        >
          <span :class="{ 'animate-spin': loading }">🔄</span>
          <span>Làm mới</span>
        </button>
        <router-link
          to="/nv/don"
          class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition shadow-sm"
        >
          ← Danh sách đơn
        </router-link>
      </div>
    </div>

    <!-- Alert Messages -->
    <div v-if="errorMessage" class="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-lg">⚠️</span>
        <span>{{ errorMessage }}</span>
      </div>
      <button @click="errorMessage = ''" class="font-bold text-rose-600 hover:text-rose-800">×</button>
    </div>

    <div v-if="successMessage" class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-lg">✅</span>
        <span>{{ successMessage }}</span>
      </div>
      <button @click="successMessage = ''" class="font-bold text-emerald-600 hover:text-emerald-800">×</button>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading && !booking" class="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-sky-600 border-t-transparent mx-auto mb-3"></div>
      <p class="text-xs">Đang tải thông tin đơn đặt phòng...</p>
    </div>

    <div v-else-if="booking" class="space-y-6">
      <!-- Actions Toolbar -->
      <div class="bg-slate-900 text-white rounded-2xl p-4 sm:p-5 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Thao tác khả dụng</div>
          <div class="text-xs text-slate-300">
            Trạng thái hiện tại: <span class="font-semibold text-white">{{ booking.status }}</span>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <!-- Check-in Action -->
          <button
            v-if="booking.actions?.can_check_in"
            @click="openCheckInModal"
            class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>🏨</span>
            <span>Check-in (Nhận phòng)</span>
          </button>

          <!-- Reschedule Action -->
          <button
            v-if="booking.actions?.can_reschedule"
            @click="openRescheduleModal"
            class="px-3.5 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>📅</span>
            <span>Đổi lịch</span>
          </button>

          <!-- Extend Action -->
          <button
            v-if="booking.actions?.can_extend"
            @click="openExtendModal"
            class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>⏱️</span>
            <span>Gia hạn lưu trú</span>
          </button>

          <!-- Change Room Action -->
          <button
            v-if="booking.actions?.can_change_room"
            @click="openChangeRoomModal"
            class="px-3.5 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-semibold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>🔄</span>
            <span>Đổi phòng sự cố</span>
          </button>

          <!-- Desk Payment Action -->
          <button
            v-if="booking.actions?.can_pay"
            @click="openPaymentModal"
            class="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-semibold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>💵</span>
            <span>Thu tiền quầy</span>
          </button>

          <!-- Check-out Action -->
          <button
            v-if="booking.actions?.can_check_out"
            @click="openCheckOutModal"
            class="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>🚪</span>
            <span>Check-out & Hóa đơn</span>
          </button>

          <!-- Cancel Action -->
          <button
            v-if="booking.actions?.can_cancel"
            @click="openCancelModal"
            class="px-3.5 py-2 bg-slate-800 hover:bg-rose-900 text-rose-300 border border-rose-700/50 rounded-xl text-xs font-semibold transition shadow-sm flex items-center space-x-1.5"
          >
            <span>✖</span>
            <span>Hủy đơn</span>
          </button>
        </div>
      </div>

      <!-- 3 Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Guest Details -->
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 pb-2 flex items-center justify-between">
            <span>Thông tin khách hàng</span>
            <span>👤</span>
          </div>
          <div class="space-y-1.5 text-xs">
            <div class="text-sm font-bold text-slate-900">{{ booking.customer?.full_name || booking.customer?.fullName }}</div>
            <div class="flex items-center space-x-2 text-slate-600">
              <span class="font-medium text-slate-400">SĐT:</span>
              <a :href="`tel:${booking.customer?.phone}`" class="text-sky-600 hover:underline font-mono">{{ booking.customer?.phone }}</a>
            </div>
            <div class="flex items-center space-x-2 text-slate-600">
              <span class="font-medium text-slate-400">Email:</span>
              <a :href="`mailto:${booking.customer?.email}`" class="text-sky-600 hover:underline font-mono">{{ booking.customer?.email }}</a>
            </div>
            <div v-if="booking.customer?.identification_id || booking.customer?.identificationId" class="flex items-center space-x-2 text-slate-600">
              <span class="font-medium text-slate-400">Giấy tờ:</span>
              <span class="font-mono">{{ booking.customer?.identification_id || booking.customer?.identificationId }}</span>
            </div>
            <div v-if="booking.customer?.nationality" class="flex items-center space-x-2 text-slate-600">
              <span class="font-medium text-slate-400">Quốc tịch:</span>
              <span>{{ booking.customer.nationality }}</span>
            </div>
          </div>
        </div>

        <!-- Stay Details -->
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 pb-2 flex items-center justify-between">
            <span>Thời gian lưu trú</span>
            <span>🕒</span>
          </div>
          <div class="space-y-2 text-xs">
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-semibold">Nhận phòng dự kiến</span>
              <span class="font-semibold text-slate-800">{{ formatDateTime(booking.checkin) }}</span>
            </div>
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-semibold">Trả phòng dự kiến</span>
              <span class="font-semibold text-slate-800">{{ formatDateTime(booking.checkout) }}</span>
            </div>
            <div v-if="booking.actual_checkin" class="pt-1 border-t border-slate-100 text-emerald-700">
              <span class="block text-[10px] uppercase font-semibold">Đã nhận phòng lúc</span>
              <span class="font-semibold">{{ formatDateTime(booking.actual_checkin) }}</span>
            </div>
            <div v-if="booking.actual_checkout" class="text-rose-700">
              <span class="block text-[10px] uppercase font-semibold">Đã trả phòng lúc</span>
              <span class="font-semibold">{{ formatDateTime(booking.actual_checkout) }}</span>
            </div>
            <div class="text-slate-500 pt-1 border-t border-slate-100">
              Số khách: <strong class="text-slate-800">{{ booking.guests }} người</strong>
            </div>
          </div>
        </div>

        <!-- Financial Overview -->
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 pb-2 flex items-center justify-between">
            <span>Tài chính & Thanh toán</span>
            <span>💰</span>
          </div>
          <div class="space-y-1.5 text-xs">
            <div class="flex justify-between text-slate-600">
              <span>Tiền phòng:</span>
              <span class="font-medium font-mono">{{ formatCurrency(booking.room_amount) }}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>VAT ({{ Math.round(booking.vat_rate * 100) }}%):</span>
              <span class="font-medium font-mono">{{ formatCurrency(booking.vat_amount) }}</span>
            </div>
            <div class="flex justify-between text-sm font-bold text-slate-900 pt-1.5 border-t border-slate-100">
              <span>Tổng tiền đơn:</span>
              <span class="font-mono text-sky-700">{{ formatCurrency(booking.total_amount) }}</span>
            </div>
            <div class="flex justify-between text-emerald-700 font-semibold pt-1">
              <span>Đã thanh toán:</span>
              <span class="font-mono">{{ formatCurrency(booking.paid_amount) }}</span>
            </div>
            <div
              class="flex justify-between font-bold pt-1 border-t border-slate-100"
              :class="booking.remaining_amount > 0 ? 'text-amber-700' : 'text-slate-700'"
            >
              <span>Còn lại phải thu:</span>
              <span class="font-mono">{{ formatCurrency(booking.remaining_amount) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Stay Segments (Đoạn lưu trú) -->
      <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div class="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
            <span>🏨</span>
            <span>Chi tiết các đoạn lưu trú (Phòng được gán)</span>
          </h3>
          <span class="text-xs text-slate-500 font-mono">{{ booking.segments?.length || 0 }} đoạn</span>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-600">
            <thead class="bg-slate-100/75 text-slate-700 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th class="p-3">Phòng</th>
                <th class="p-3">Tầng</th>
                <th class="p-3">Hạng phòng</th>
                <th class="p-3">Từ ngày / giờ</th>
                <th class="p-3">Đến ngày / giờ</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="seg in booking.segments" :key="seg.segment_id" class="hover:bg-slate-50/75">
                <td class="p-3 font-mono font-bold text-slate-900">
                  <span v-if="seg.room_number" class="px-2 py-1 bg-sky-50 text-sky-700 border border-sky-200 rounded">
                    Phòng {{ seg.room_number }}
                  </span>
                  <span v-else class="text-slate-400 italic">Chưa xếp phòng</span>
                </td>
                <td class="p-3 font-mono text-slate-700">Tầng {{ seg.floor }}</td>
                <td class="p-3 font-semibold text-slate-800">{{ seg.room_type }}</td>
                <td class="p-3 font-mono">{{ formatDateTime(seg.checkin) }}</td>
                <td class="p-3 font-mono">{{ formatDateTime(seg.checkout) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Payment Transactions & Refunds (2 columns) -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Payment Transactions -->
        <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div class="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <span>💳</span>
              <span>Lịch sử thanh toán</span>
            </h3>
            <span class="text-xs text-slate-500 font-mono">{{ booking.transactions?.length || 0 }} giao dịch</span>
          </div>

          <div v-if="!booking.transactions?.length" class="p-6 text-center text-xs text-slate-400 italic">
            Chưa có giao dịch thanh toán nào
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-100/75 text-slate-700 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th class="p-3">Mã GD</th>
                  <th class="p-3">Phương thức</th>
                  <th class="p-3 text-right">Số tiền</th>
                  <th class="p-3 text-center">Trạng thái</th>
                  <th class="p-3">Thời gian</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="tx in booking.transactions" :key="tx.transaction_id" class="hover:bg-slate-50/75">
                  <td class="p-3 font-mono font-medium text-slate-900">{{ tx.reference_code || ('GD#' + tx.transaction_id) }}</td>
                  <td class="p-3 font-medium">{{ tx.method }} ({{ tx.channel }})</td>
                  <td class="p-3 text-right font-mono font-bold text-emerald-700">{{ formatCurrency(tx.amount) }}</td>
                  <td class="p-3 text-center">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                      :class="tx.status === 'THANH_CONG' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'"
                    >
                      {{ tx.status }}
                    </span>
                  </td>
                  <td class="p-3 font-mono text-[11px] text-slate-500">{{ formatDateTime(tx.transaction_date) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Refunds -->
        <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div class="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <span>💸</span>
              <span>Lịch sử hoàn tiền</span>
            </h3>
            <span class="text-xs text-slate-500 font-mono">{{ booking.refunds?.length || 0 }} khoản hoàn</span>
          </div>

          <div v-if="!booking.refunds?.length" class="p-6 text-center text-xs text-slate-400 italic">
            Không có khoản hoàn tiền nào
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-100/75 text-slate-700 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th class="p-3">Mã hoàn</th>
                  <th class="p-3 text-right">Số tiền</th>
                  <th class="p-3">Lý do</th>
                  <th class="p-3 text-center">Trạng thái</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="rf in booking.refunds" :key="rf.refund_id" class="hover:bg-slate-50/75">
                  <td class="p-3 font-mono font-medium text-slate-900">#{{ rf.refund_id }}</td>
                  <td class="p-3 text-right font-mono font-bold text-rose-700">{{ formatCurrency(rf.amount) }}</td>
                  <td class="p-3 text-slate-600 truncate max-w-[150px]">{{ rf.reason }}</td>
                  <td class="p-3 text-center">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                      :class="rf.status === 'DA_HOAN' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
                    >
                      {{ rf.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Invoice Summary if generated -->
      <div v-if="booking.invoice" class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
        <div class="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 pb-2 flex items-center justify-between">
          <span class="flex items-center space-x-1.5">
            <span>🧾</span>
            <span>Hóa đơn lưu trú đã cấp</span>
          </span>
          <span class="font-mono text-slate-900 font-bold">Số HĐ: {{ booking.invoice.invoice_number }}</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Ngày lập</span>
            <span class="font-medium text-slate-800 font-mono">{{ formatDateTime(booking.invoice.issued_at) }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Người lập</span>
            <span class="font-medium text-slate-800">{{ booking.invoice.created_by || '-' }}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase font-semibold">Tổng thanh toán</span>
            <span class="font-bold text-sky-700 font-mono">{{ formatCurrency(booking.invoice.total_amount) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Cancel -->
    <div v-if="showCancelModal" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
        <h3 class="text-base font-bold text-slate-900">Xác nhận hủy đơn đặt phòng</h3>
        <p class="text-xs text-slate-600">
          Hủy đơn mã <strong class="font-mono text-slate-900">{{ booking?.booking_code }}</strong>.
          Thao tác này sẽ giải phóng toàn bộ phòng đang được giữ.
        </p>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Lý do hủy (bắt buộc)</label>
          <textarea
            v-model="cancelReason"
            rows="3"
            required
            placeholder="Khách đổi kế hoạch, không liên lạc được..."
            class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-rose-500 outline-none"
          ></textarea>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2">
          <button
            @click="showCancelModal = false"
            class="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
          >
            Đóng
          </button>
          <button
            @click="handleCancel"
            :disabled="submittingAction || !cancelReason.trim()"
            class="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-50"
          >
            {{ submittingAction ? 'Đang hủy...' : 'Xác nhận hủy' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Check-in (F08) -->
    <div v-if="showCheckInModal" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center space-x-2">
            <span class="text-xl">🏨</span>
            <h3 class="text-base font-bold text-slate-900">Check-in nhận phòng: {{ booking?.booking_code }}</h3>
          </div>
          <button @click="showCheckInModal = false" class="text-slate-400 hover:text-slate-600 font-bold">✕</button>
        </div>

        <!-- Room info note -->
        <div class="p-3 bg-sky-50 border border-sky-200 rounded-xl text-xs text-sky-800 space-y-1">
          <div class="flex justify-between font-semibold">
            <span>Phòng được xếp:</span>
            <span class="font-mono">{{ booking?.segments?.[0]?.room_number ? 'Phòng ' + booking.segments[0].room_number : 'Theo phân bổ' }}</span>
          </div>
          <div class="flex justify-between text-sky-700">
            <span>Giờ nhận dự kiến:</span>
            <span>{{ formatDateTime(booking?.checkin) }}</span>
          </div>
        </div>

        <!-- Modal Error Message -->
        <div v-if="checkInError" class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 space-y-1">
          <div class="font-bold flex items-center space-x-1">
            <span>⚠️</span>
            <span>Không thể nhận phòng</span>
          </div>
          <div>{{ checkInError }}</div>
        </div>

        <form @submit.prevent="handleCheckIn" class="space-y-3.5">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Loại giấy tờ *</label>
              <select
                v-model="checkInForm.idType"
                required
                class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="CCCD">CCCD / Căn cước công dân</option>
                <option value="HO_CHIEU">Hộ chiếu / Passport</option>
                <option value="BANG_LAI">Bằng lái xe / GPLX</option>
                <option value="KHAC">Giấy tờ khác</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">Quốc tịch *</label>
              <input
                v-model="checkInForm.nationality"
                type="text"
                required
                placeholder="VN"
                class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 outline-none uppercase font-mono"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Số giấy tờ (CCCD/Passport) *</label>
            <input
              v-model="checkInForm.idNumber"
              type="text"
              required
              placeholder="Nhập số CCCD (được mã hóa NFR-13)"
              class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-mono focus:ring-2 focus:ring-emerald-500 outline-none"
            />
            <span class="text-[10px] text-slate-400 mt-0.5 block">
              🔒 Số giấy tờ được mã hóa AES theo tiêu chuẩn bảo mật dữ liệu khách hàng (NFR-13).
            </span>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Ảnh chụp giấy tờ (Tùy chọn)</label>
            <input
              type="file"
              accept="image/*,application/pdf"
              @change="handleFileUpload"
              class="w-full text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
            />
            <div v-if="uploadingPhoto" class="text-[11px] text-sky-600 mt-1 flex items-center space-x-1">
              <span class="animate-spin">⏳</span>
              <span>Đang tải tệp lên máy chủ...</span>
            </div>
            <div v-else-if="checkInForm.photoUrl" class="text-[11px] text-emerald-600 mt-1 flex items-center space-x-1">
              <span>✓</span>
              <span>Đã lưu ảnh giấy tờ</span>
            </div>
          </div>

          <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              @click="showCheckInModal = false"
              class="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="submittingAction || uploadingPhoto"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-50 flex items-center space-x-1.5"
            >
              <span v-if="submittingAction" class="animate-spin">⏳</span>
              <span>{{ submittingAction ? 'Đang xử lý...' : 'Xác nhận nhận phòng' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Extend Stay (F09) -->
    <div v-if="showExtendModal" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center space-x-2">
            <span class="text-xl">⏱️</span>
            <h3 class="text-base font-bold text-slate-900">Gia hạn lưu trú: {{ booking?.booking_code }}</h3>
          </div>
          <button @click="showExtendModal = false" class="text-slate-400 hover:text-slate-600 font-bold">✕</button>
        </div>

        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 space-y-1">
          <div class="flex justify-between">
            <span>Loại hình đặt:</span>
            <strong class="text-slate-900">{{ booking?.booking_type === 'NGAY' ? 'Theo ngày (Đêm)' : 'Theo giờ' }}</strong>
          </div>
          <div class="flex justify-between">
            <span>Giờ trả phòng hiện tại:</span>
            <strong class="font-mono text-slate-900">{{ formatDateTime(booking?.checkout) }}</strong>
          </div>
          <div v-if="booking?.segments?.length" class="flex justify-between">
            <span>Phòng hiện tại:</span>
            <strong class="font-mono text-sky-700">Phòng {{ booking.segments[booking.segments.length - 1].room_number }}</strong>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1.5">
            {{ booking?.booking_type === 'NGAY' ? 'Số đêm muốn gia hạn thêm *' : 'Số giờ muốn gia hạn thêm *' }}
          </label>
          <div class="flex items-center space-x-2">
            <button
              type="button"
              @click="changeExtendUnits(-1)"
              :disabled="extendUnits <= 1 || loadingExtendPreview"
              class="w-9 h-9 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 font-bold text-slate-700 disabled:opacity-40"
            >
              -
            </button>
            <input
              v-model.number="extendUnits"
              type="number"
              min="1"
              max="30"
              @change="fetchExtendPreview"
              class="w-24 text-center px-3 py-2 border border-slate-300 rounded-xl text-sm font-mono font-bold focus:ring-2 focus:ring-indigo-500 outline-none"
            />
            <button
              type="button"
              @click="changeExtendUnits(1)"
              :disabled="loadingExtendPreview"
              class="w-9 h-9 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 font-bold text-slate-700 disabled:opacity-40"
            >
              +
            </button>
            <span class="text-xs text-slate-500 font-medium">
              {{ booking?.booking_type === 'NGAY' ? 'đêm' : 'giờ' }}
            </span>
          </div>
        </div>

        <!-- Preview Cost Box -->
        <div v-if="loadingExtendPreview" class="p-4 bg-indigo-50/50 border border-indigo-100 rounded-xl text-center text-xs text-indigo-600">
          ⏳ Đang tính tiền thêm và kiểm tra lịch phòng...
        </div>

        <div v-else-if="extendPreview" class="p-4 bg-indigo-50 border border-indigo-200 rounded-xl text-xs space-y-2">
          <div class="flex justify-between text-indigo-900">
            <span>Trả phòng mới dự kiến:</span>
            <strong class="font-mono">{{ formatDateTime(extendPreview.new_checkout) }}</strong>
          </div>
          <div v-if="extendPreview.switched_to_daily_rate" class="p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-[11px] font-medium">
            ℹ️ Tổng thời gian vượt ngưỡng 5 giờ — hệ thống tính lại theo 1 giá ngày (BR-33).
          </div>
          <div class="border-t border-indigo-200/70 pt-2 space-y-1">
            <div class="flex justify-between text-indigo-800">
              <span>Tiền phòng thêm:</span>
              <span class="font-mono font-semibold">{{ formatCurrency(extendPreview.added_room_amount) }}</span>
            </div>
            <div class="flex justify-between text-indigo-800">
              <span>VAT thêm:</span>
              <span class="font-mono font-semibold">{{ formatCurrency(extendPreview.added_vat_amount) }}</span>
            </div>
            <div class="flex justify-between text-sm font-bold text-indigo-950 pt-1 border-t border-indigo-200/70">
              <span>Số tiền cộng thêm vào đơn:</span>
              <span class="font-mono text-indigo-700">+{{ formatCurrency(extendPreview.added_amount) }}</span>
            </div>
            <div class="flex justify-between text-[11px] text-indigo-700">
              <span>Tổng tiền đơn sau gia hạn:</span>
              <span class="font-mono font-semibold">{{ formatCurrency(extendPreview.new_total_amount) }}</span>
            </div>
          </div>
        </div>

        <!-- Conflict / Error + Suggested Rooms (AC-12) -->
        <div v-if="extendError || extendPreview?.has_conflict" class="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 space-y-2">
          <div class="font-bold flex items-center space-x-1.5">
            <span>⚠️</span>
            <span>Không thể gia hạn trên phòng hiện tại (EXTEND_CONFLICT)</span>
          </div>
          <div>
            {{ extendError || 'Phòng hiện tại đã có lượt đặt kế tiếp (bao gồm khoảng đệm 30 phút dọn phòng - AC-12).' }}
          </div>

          <div v-if="extendSuggestedRooms.length" class="pt-2 border-t border-rose-200 space-y-1.5">
            <div class="font-semibold text-rose-900">
              Danh sách phòng cùng hạng còn trống trong khoảng gia hạn (đề xuất chuyển phòng):
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="r in extendSuggestedRooms"
                :key="r.room_id"
                class="px-2.5 py-1 bg-white border border-rose-300 rounded-lg font-mono font-bold text-rose-900 text-[11px]"
              >
                Phòng {{ r.room_number }} (Tầng {{ r.floor }})
              </span>
            </div>
            <div class="pt-1">
              <router-link to="/nv/so-do-phong" class="text-[11px] font-semibold text-sky-700 hover:underline">
                → Mở sơ đồ phòng để bố trí lại
              </router-link>
            </div>
          </div>
          <div v-else class="text-[11px] italic text-rose-700">
            Hiện không còn phòng cùng hạng nào trống trong khung giờ gia hạn này.
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
          <button
            type="button"
            @click="showExtendModal = false"
            class="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
          >
            Đóng
          </button>
          <button
            type="button"
            @click="handleExtend"
            :disabled="submittingAction || loadingExtendPreview || !extendPreview || extendPreview.has_conflict"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-50 flex items-center space-x-1.5"
          >
            <span v-if="submittingAction" class="animate-spin">⏳</span>
            <span>{{ submittingAction ? 'Đang gia hạn...' : 'Xác nhận gia hạn' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Change Room Incident Modal (F10) -->
    <ChangeRoomDialog
      v-if="booking"
      v-model="showChangeRoomModal"
      :booking-id="booking.id"
      :current-room-number="currentRoomNumber"
      @success="handleChangeRoomSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import apiClient from '../../api/client';
import StatusBadge from '../../components/StatusBadge.vue';
import ChangeRoomDialog from '../../components/ChangeRoomDialog.vue';

const route = useRoute();
const idParam = ref(route.params.id);
const bookingCode = ref('');
const booking = ref(null);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

// Modals
const showCancelModal = ref(false);
const cancelReason = ref('');
const submittingAction = ref(false);

const fetchBooking = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await apiClient.get(`/bookings/${idParam.value}`);
    booking.value = res;
    bookingCode.value = res.booking_code;
  } catch (err) {
    errorMessage.value = err.message || 'Không thể tải chi tiết đơn';
  } finally {
    loading.value = false;
  }
};

const openCancelModal = () => {
  cancelReason.value = '';
  showCancelModal.value = true;
};

const handleCancel = async () => {
  if (!cancelReason.value.trim()) return;
  submittingAction.value = true;
  try {
    await apiClient.post(`/bookings/${booking.value.id}/cancel`, {
      reason: cancelReason.value
    });
    successMessage.value = 'Hủy đơn thành công!';
    showCancelModal.value = false;
    await fetchBooking();
  } catch (err) {
    errorMessage.value = err.message || 'Lỗi khi hủy đơn';
  } finally {
    submittingAction.value = false;
  }
};

// Check-in Modal (F08)
const showCheckInModal = ref(false);
const checkInError = ref('');
const checkInForm = ref({
  idType: 'CCCD',
  idNumber: '',
  nationality: 'VN',
  photoUrl: ''
});
const uploadingPhoto = ref(false);

const openCheckInModal = () => {
  checkInError.value = '';
  checkInForm.value = {
    idType: 'CCCD',
    idNumber: '',
    nationality: booking.value?.customer?.nationality || 'VN',
    photoUrl: ''
  };
  showCheckInModal.value = true;
};

const handleFileUpload = async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  uploadingPhoto.value = true;
  checkInError.value = '';
  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post(`/bookings/${booking.value.id}/upload-document`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    checkInForm.value.photoUrl = res.photo_url;
  } catch (err) {
    checkInError.value = err.message || 'Lỗi khi tải ảnh giấy tờ';
  } finally {
    uploadingPhoto.value = false;
  }
};

const handleCheckIn = async () => {
  if (!checkInForm.value.idNumber.trim()) return;
  submittingAction.value = true;
  checkInError.value = '';
  try {
    const res = await apiClient.post(`/bookings/${booking.value.id}/check-in`, {
      loaiGiayTo: checkInForm.value.idType,
      soGiayTo: checkInForm.value.idNumber.trim(),
      quocTich: checkInForm.value.nationality.trim(),
      anhUrl: checkInForm.value.photoUrl || null
    });
    successMessage.value = res.message || 'Nhận phòng thành công!';
    showCheckInModal.value = false;
    await fetchBooking();
  } catch (err) {
    const errCode = err.code;
    const errDetail = err.detail;
    if (errCode === 'CHECKIN_TOO_EARLY') {
      checkInError.value = `Chưa tới giờ nhận phòng quy định (Quy tắc BR-32). Giờ nhận dự kiến: ${formatDateTime(booking.value.checkin)}`;
    } else if (errCode === 'ROOM_NOT_READY') {
      checkInError.value = `Phòng chưa sẵn sàng để nhận khách (hiện tại: ${errDetail || 'ĐANG_DON'}). Vui lòng thông báo buồng phòng hoàn tất dọn dẹp (Quy tắc BR-31).`;
    } else {
      checkInError.value = err.message || 'Lỗi khi nhận phòng';
    }
  } finally {
    submittingAction.value = false;
  }
};

const openRescheduleModal = () => {
  alert('Mở hộp thoại đổi lịch (F05/F07)');
};

// Extend Modal (F09)
const showExtendModal = ref(false);
const extendUnits = ref(1);
const extendPreview = ref(null);
const loadingExtendPreview = ref(false);
const extendError = ref('');
const extendSuggestedRooms = ref([]);

const openExtendModal = async () => {
  extendUnits.value = 1;
  extendPreview.value = null;
  extendError.value = '';
  extendSuggestedRooms.value = [];
  showExtendModal.value = true;
  await fetchExtendPreview();
};

const changeExtendUnits = async (delta) => {
  const next = (extendUnits.value || 1) + delta;
  if (next < 1) return;
  extendUnits.value = next;
  await fetchExtendPreview();
};

const fetchExtendPreview = async () => {
  if (!extendUnits.value || extendUnits.value < 1) return;
  loadingExtendPreview.value = true;
  extendError.value = '';
  extendSuggestedRooms.value = [];
  try {
    const res = await apiClient.get(`/bookings/${booking.value.id}/extend-preview`, {
      params: { units: extendUnits.value }
    });
    extendPreview.value = res;
    if (res.has_conflict && res.suggested_rooms) {
      extendSuggestedRooms.value = res.suggested_rooms;
    }
  } catch (err) {
    extendPreview.value = null;
    extendError.value = err.message || 'Không thể tính trước chi phí gia hạn';
  } finally {
    loadingExtendPreview.value = false;
  }
};

const handleExtend = async () => {
  if (!extendUnits.value || extendUnits.value < 1) return;
  submittingAction.value = true;
  extendError.value = '';
  try {
    const res = await apiClient.post(`/bookings/${booking.value.id}/extend`, {
      soDonVi: extendUnits.value
    });
    successMessage.value = `${res.message} (+${formatCurrency(res.added_amount)})`;
    showExtendModal.value = false;
    await fetchBooking();
  } catch (err) {
    extendError.value = err.message || 'Lỗi khi gia hạn lưu trú';
    if (err.code === 'EXTEND_CONFLICT' && err.data?.suggested_rooms) {
      extendSuggestedRooms.value = err.data.suggested_rooms;
    }
  } finally {
    submittingAction.value = false;
  }
};

// Change Room Modal (F10)
const showChangeRoomModal = ref(false);

const currentRoomNumber = computed(() => {
  if (!booking.value?.segments?.length) return '';
  const lastSeg = booking.value.segments[booking.value.segments.length - 1];
  return lastSeg.room_number || lastSeg.roomNumber || '';
});

const openChangeRoomModal = () => {
  showChangeRoomModal.value = true;
};

const handleChangeRoomSuccess = async (res) => {
  const roomNum = res.new_room_number || res.newRoomNumber;
  successMessage.value = `Đổi phòng do sự cố thành công! Đã chuyển khách sang phòng ${roomNum}, phòng cũ chuyển sang trạng thái bảo trì.`;
  await fetchBooking();
};

const openCheckOutModal = () => {
  alert('Mở màn hình Check-out và Hóa đơn (F11)');
};

const openPaymentModal = () => {
  alert('Mở hộp thoại thu tiền quầy (F12)');
};

const formatCurrency = (val) => {
  if (val === undefined || val === null) return '0 ₫';
  return Number(val).toLocaleString('vi-VN') + ' ₫';
};

const formatDateTime = (val) => {
  if (!val) return '-';
  const d = new Date(val);
  return d.toLocaleString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

onMounted(() => {
  fetchBooking();
});
</script>
