<template>
  <div class="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
    <div class="w-20 h-20 bg-rose-50 rounded-2xl flex items-center justify-center text-rose-500 text-3xl font-bold mb-4">
      404
    </div>
    <h2 class="text-2xl font-bold text-slate-800 tracking-tight">Trang không tồn tại</h2>
    <p class="text-sm text-slate-500 mt-2 max-w-md">
      Đường dẫn bạn yêu cầu không tìm thấy hoặc đã bị di chuyển trong hệ thống.
    </p>
    <router-link
      to="/"
      class="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-sky-600 hover:bg-sky-700 transition"
    >
      Quay về trang chủ
    </router-link>
  </div>
</template>
