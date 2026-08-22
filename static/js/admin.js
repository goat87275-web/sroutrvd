document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.main-sidebar');
  const toggle = document.querySelector('[data-widget="pushmenu"]');
  if (!sidebar || !toggle) return;
  toggle.setAttribute('aria-label', 'طي أو توسيع القائمة الجانبية');
  toggle.addEventListener('click', () => setTimeout(() => document.body.classList.toggle('admin-sidebar-collapsed', document.body.classList.contains('sidebar-collapse')), 20));
  document.querySelectorAll('.nav-sidebar .nav-link').forEach(link => { const label = link.textContent.trim(); if (!link.getAttribute('aria-label')) link.setAttribute('aria-label', label); link.setAttribute('title', label); });
});
