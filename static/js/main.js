// Copy referral link to clipboard
function copyReferralLink() {
    const link = document.querySelector('.alert-info code').textContent;
    navigator.clipboard.writeText(link).then(() => {
        alert('Ссылка скопирована в буфер обмена!');
    }).catch(err => {
        console.error('Ошибка копирования:', err);
    });
}

// Phone mask for Russian phone numbers
function formatPhoneNumber(value) {
    if (!value) return value;
    const phoneNumber = value.replace(/[^\d]/g, '');
    const phoneNumberLength = phoneNumber.length;

    if (phoneNumberLength < 2) return phoneNumber;

    if (phoneNumberLength < 5) {
        return `+7 (${phoneNumber.slice(1)}`;
    }

    if (phoneNumberLength < 8) {
        return `+7 (${phoneNumber.slice(1, 4)}) ${phoneNumber.slice(4)}`;
    }

    if (phoneNumberLength < 10) {
        return `+7 (${phoneNumber.slice(1, 4)}) ${phoneNumber.slice(4, 7)}-${phoneNumber.slice(7)}`;
    }

    return `+7 (${phoneNumber.slice(1, 4)}) ${phoneNumber.slice(4, 7)}-${phoneNumber.slice(7, 9)}-${phoneNumber.slice(9, 11)}`;
}

// Auto-hide alerts disabled - alerts remain visible
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide functionality removed - alerts now stay visible

    // Apply phone mask to phone input fields
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const formattedValue = formatPhoneNumber(e.target.value);
            e.target.value = formattedValue;
        });

        // Set initial +7 on focus if empty
        input.addEventListener('focus', function(e) {
            if (!e.target.value) {
                e.target.value = '+7 (';
            }
        });

        // Clear if only +7 ( remains on blur
        input.addEventListener('blur', function(e) {
            if (e.target.value === '+7 (' || e.target.value === '+7') {
                e.target.value = '';
            }
        });
    });
});
