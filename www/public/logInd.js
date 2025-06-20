const emailInput = document.getElementById('email-input');
const loginButton = document.getElementById('login-button');
const themeIcon = document.getElementById('theme-icon');
const otpOverlay = document.getElementById('otp-overlay');
const otpModal = document.getElementById('otp-modal');
const otpEmail = document.getElementById('otp-email');
const otpInputs = document.querySelectorAll('.otp-input');
const otpSigninButton = document.getElementById('otp-signin-button');
const resendTimer = document.getElementById('resend-timer');
const resendLink = document.getElementById('resend-link');
const mainContent = document.querySelector('.main-content');
const termsCheckbox = document.getElementById('terms-checkbox');
const termsOverlay = document.getElementById('terms-overlay');
const termsModal = document.getElementById('terms-modal');
const emailError = document.getElementById('email-error');
const otpMessage = document.getElementById('otp-message');
const languageText = document.getElementById('language-text');
let timerSeconds = 120;
let timerInterval;

// Language translations
const translations = {
    en: {
        login: "Log in",
        description: "Enter your email below to log in to your account, or continue with a social provider.",
        or_continue_with: "Or continue with",
        email: "Email",
        login_with_email: "Log in with Email",
        agree_to: "I agree to the",
        terms_of_service: "Terms of Service",
        sign_in: "Sign in",
        otp_description: "Enter the code we just sent to ",
        resend: "Resend",
        terms_title: "Terms of Service",
        terms_content: "This software is open source and provided \"as is\". No guarantees of profit or functionality are given. You are solely responsible for all risks, taxes, and legal compliance. I do not manage your funds; I only provide a tool for swaps on Pump.fun via a trusted contract. AML risks are your responsibility. The key is stored in RAM and not saved. Profit share in SOL (if applicable) is a fee for the software, transferred manually by you. By using it, you accept all terms.",
        close: "Close"
    },
    ru: {
        login: "Войти",
        description: "Введите ваш email ниже, чтобы войти в аккаунт, или продолжите через социальные сети.",
        or_continue_with: "Или продолжить с",
        email: "Email",
        login_with_email: "Войти через Email",
        agree_to: "Я согласен с",
        terms_of_service: "Условиями использования",
        sign_in: "Войти",
        otp_description: "Введите код, который мы отправили на ",
        resend: "Отправить снова",
        terms_title: "Дисклеймер",
        terms_content: "Это программное обеспечение с открытым исходным кодом предоставляется \"как есть\". Никаких гарантий прибыли или функциональности не предоставляется. Вы несете полную ответственность за все риски, налоги и соблюдение законодательства. Я не управляю вашими средствами; я предоставляю только инструмент для обмена на Pump.fun через доверенный контракт. Риски AML — ваша ответственность. Ключ хранится в оперативной памяти и не сохраняется. Доля прибыли в SOL (если применимо) — это плата за программное обеспечение, переведенная вами вручную. Используя его, вы принимаете все условия.",
        close: "Закрыть"
    }
};

let currentLanguage = 'en';

function setTheme(theme) {
    const body = document.body;
    if (theme === 'dark') {
        body.classList.remove('light');
        body.classList.add('dark');
        themeIcon.innerHTML = `
                    <path d="M21.4 13.7C20.6 13.9 19.8 14 19 14c-5 0-9-4-9-9 0-.8.1-1.6.3-2.4-4.2 1.1-7.3 4.9-7.3 9.4 0 5.5 4.5 10 10 10 4.5 0 8.3-3 9.4-7.3z"/>
                `;
    } else {
        body.classList.remove('dark');
        body.classList.add('light');
        themeIcon.innerHTML = `
                    <circle cx="12" cy="12" r="4"/>
                    <circle cx="12" cy="4" r="1"/>
                    <circle cx="12" cy="20" r="1"/>
                    <circle cx="4" cy="12" r="1"/>
                    <circle cx="20" cy="12" r="1"/>
                    <circle cx="6.34" cy="6.34" r="1"/>
                    <circle cx="17.66" cy="17.66" r="1"/>
                    <circle cx="6.34" cy="17.66" r="1"/>
                    <circle cx="17.66" cy="6.34" r="1"/>
                `;
    }
}

function toggleTheme() {
    const body = document.body;
    const currentTheme = body.classList.contains('dark') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function switchLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'ru' : 'en';
    languageText.textContent = currentLanguage === 'en' ? 'EN' : 'RU';
    document.documentElement.lang = currentLanguage;
    updateContent();
    localStorage.setItem('language', currentLanguage);
}

function updateContent() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
            element.placeholder = translations[currentLanguage][key] || translations.en[key];
        } else {
            element.textContent = translations[currentLanguage][key] || translations.en[key];
        }
        // Handle special case for otp_description
        if (key === 'otp_description') {
            element.innerHTML = `${translations[currentLanguage][key]} <span id="otp-email" class="otp-email"></span>`;
        }
        // Handle special case for resend link
        if (key === 'resend') {
            element.innerHTML = `${translations[currentLanguage][key]} (<span id="resend-timer">1:00</span>)`;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    const savedLanguage = localStorage.getItem('language') || 'en';
    currentLanguage = savedLanguage;
    languageText.textContent = currentLanguage === 'en' ? 'EN' : 'RU';
    document.documentElement.lang = currentLanguage;
    updateContent();
});

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function updateLoginButtonState() {
    const email = emailInput.value;
    const termsAgreed = termsCheckbox.checked;
    if (validateEmail(email) && termsAgreed) {
        loginButton.disabled = false;
        loginButton.classList.add('enabled');
    } else {
        loginButton.disabled = true;
        loginButton.classList.remove('enabled');
    }
}

emailInput.addEventListener('input', updateLoginButtonState);
termsCheckbox.addEventListener('change', updateLoginButtonState);

function showMessage(element, message) {
    element.textContent = message;
    element.classList.remove('hidden');
    setTimeout(() => {
        element.classList.add('hidden');
    }, 3000);
}

async function requestOtp() {
    const email = emailInput.value;
    if (!validateEmail(email)) {
        showMessage(emailError, translations[currentLanguage].invalid_email || 'Please enter a valid email address');
        return;
    }
    if (!termsCheckbox.checked) {
        showMessage(emailError, translations[currentLanguage].agree_terms || 'Please agree to the Terms of Service');
        return;
    }

    try {
        const response = await fetch('/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        });
        const data = await response.json();
        if (response.ok) {
            otpEmail.textContent = email;
            otpOverlay.classList.remove('hidden');
            otpOverlay.classList.add('visible');
            otpModal.classList.remove('hidden');
            otpModal.classList.add('visible');
            mainContent.classList.add('blurred');
            startResendTimer();
            otpInputs[0].focus();
        } else {
            showMessage(emailError, data.error || 'Failed to send OTP');
        }
    } catch (error) {
        console.error('Error sending OTP:', error);
        showMessage(emailError, 'Error sending OTP. Please try again.');
    }
}

function hideOtpModal() {
    otpOverlay.classList.remove('visible');
    otpOverlay.classList.add('hidden');
    otpModal.classList.remove('visible');
    otpModal.classList.add('hidden');
    mainContent.classList.remove('blurred');
    otpInputs.forEach(input => {
        input.value = '';
        input.classList.remove('success', 'error');
    });
    otpSigninButton.disabled = true;
    otpSigninButton.classList.remove('enabled');
    clearInterval(timerInterval);
    timerSeconds = 120;
    resendTimer.innerHTML = '2:00';
    resendLink.classList.remove('active');
    otpMessage.classList.add('hidden');
}

function showTermsModal() {
    termsOverlay.classList.remove('hidden');
    termsOverlay.classList.add('visible');
    termsModal.classList.remove('hidden');
    termsModal.classList.add('visible');
    mainContent.classList.add('blurred');
}

function hideTermsModal() {
    termsOverlay.classList.remove('visible');
    termsOverlay.classList.add('hidden');
    termsModal.classList.remove('visible');
    termsModal.classList.add('hidden');
    mainContent.classList.remove('blurred');
}

function moveToNext(current, nextIndex) {
    const value = current.value;
    if (!/^[0-9]$/.test(value)) {
        current.value = '';
        return;
    }
    if (value.length === 1 && nextIndex < otpInputs.length) {
        otpInputs[nextIndex].focus();
    }
    const otpCode = Array.from(otpInputs).map(input => input.value).join('');
    if (otpCode.length === 6) {
        otpSigninButton.disabled = false;
        otpSigninButton.classList.add('enabled');
    } else {
        otpSigninButton.disabled = true;
        otpSigninButton.classList.remove('enabled');
    }
}

function startResendTimer() {
    // Очищаем предыдущий интервал, если он существует
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    timerInterval = setInterval(() => {

        timerSeconds--;
        const minutes = Math.floor(timerSeconds / 60);
        const seconds = timerSeconds % 60;
        resendTimer.innerHTML = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        if (timerSeconds <= 0) {
            clearInterval(timerInterval);
            resendLink.classList.add('active');
        }
    }, 1000);
}

async function resendCode() {
    if (timerSeconds <= 0 || !timerInterval) {
        const email = emailInput.value;
        try {
            const response = await fetch('/auth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });
            const data = await response.json();
            if (response.ok) {
                timerSeconds = 120;
                resendTimer.innerHTML = '2:00';
                resendLink.classList.remove('active');
                startResendTimer();
                otpInputs.forEach(input => {
                    input.value = '';
                    input.classList.remove('success', 'error');
                });
                otpSigninButton.disabled = true;
                otpSigninButton.classList.remove('enabled');
                showMessage(otpMessage, translations[currentLanguage].code_resent || 'Code resent!');
            } else {
                showMessage(otpMessage, data.error || 'Failed to resend OTP');
            }
        } catch (error) {
            console.error('Error resending OTP:', error);
            showMessage(otpMessage, translations[currentLanguage].error_resending || 'Error resending OTP. Please try again.');
        }
    }
}

async function verifyOtp() {
    const otpCode = Array.from(otpInputs).map(input => input.value).join('');
    const email = emailInput.value;
    if (otpCode.length === 6) {
        try {
            const response = await fetch('/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, otp: otpCode }),
            });
            const data = await response.json();
            if (response.ok) {
                otpInputs.forEach(input => input.classList.add('success'));
                localStorage.setItem('userId', data.userId);
                setTimeout(() => {
                    hideOtpModal();
                    window.location.href = '/main.html';
                }, 1000);
            } else {
                otpInputs.forEach(input => input.classList.add('error'));
                showMessage(otpMessage, data.error || translations[currentLanguage].invalid_otp || 'Invalid OTP');
            }
        } catch (error) {
            console.error('Error verifying OTP:', error);
            otpInputs.forEach(input => input.classList.add('error'));
            showMessage(otpMessage, translations[currentLanguage].error_verifying || 'Error verifying OTP. Please try again.');
        }
    }
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        if (!otpModal.classList.contains('hidden')) {
            hideOtpModal();
        } else if (!termsModal.classList.contains('hidden')) {
            hideTermsModal();
        }
    }
});
