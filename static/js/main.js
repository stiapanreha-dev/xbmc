// Copy referral link to clipboard
function copyReferralLink() {
    const link = document.querySelector('.alert-info code').textContent;
    navigator.clipboard.writeText(link).then(() => {
        alert('Ссылка скопирована в буфер обмена!');
    }).catch(err => {
        console.error('Ошибка копирования:', err);
    });
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-info)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
