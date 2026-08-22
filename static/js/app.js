// ملف JavaScript المخصص لمنصة سوق الخدمات
// Custom JavaScript for Service Marketplace

document.addEventListener('DOMContentLoaded', function () {

    // إخفاء الرسائل تلقائياً بعد 5 ثواني
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // تأكيد حذف العناصر
    // Confirm before deleting items
    const deleteButtons = document.querySelectorAll('.btn-delete, .delete-confirm');
    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function (e) {
            if (!confirm('هل أنت متأكد من الحذف؟')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // تفعيل tooltips
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // تفعيل popovers
    // Enable Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // إضافة تأثير loading للنماذج
    // Add loading effect to forms
    const forms = document.querySelectorAll('form.loading-form');
    forms.forEach(function (form) {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm ms-2"></span> جاري الإرسال...';
            }
        });
    });

    // تحسين البحث التلقائي (سيستخدم لاحقاً)
    // Auto-search functionality (will be used later)
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            // يمكن إضافة AJAX search هنا لاحقاً
        });
    }

    // التمرير السلس للروابط الداخلية
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#' && document.querySelector(targetId)) {
                e.preventDefault();
                document.querySelector(targetId).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
        const reveal = new IntersectionObserver((entries, observer) => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); } }), { threshold: 0.08 });
        document.querySelectorAll('.service-card, .feature-box, .card').forEach((item, index) => { item.classList.add('reveal-item'); item.style.transitionDelay = `${Math.min(index % 6, 5) * 45}ms`; reveal.observe(item); });
    }
});

// دالة مساعدة لعرض رسالة Toast
// Helper function to show toast messages
function showToast(message, type = 'info') {
    // سيتم تطويرها في المراحل القادمة
    console.log(`Toast [${type}]: ${message}`);
}

// دالة للتحقق من صحة البريد الإلكتروني
// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// دالة للتحقق من رقم الجوال السعودي
// Saudi phone number validation
function isValidSaudiPhone(phone) {
    const phoneRegex = /^(05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$/;
    return phoneRegex.test(phone);
}
