const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const base58 = {
    decode: string => {
        const bytes = [0];
        for (let i = 0; i < string.length; i++) {
            const value = BASE58_ALPHABET.indexOf(string[i]);
            if (value < 0) throw new Error('Invalid base58 character');
            for (let j = 0; j < bytes.length; j++) bytes[j] *= 58;
            bytes[0] += value;
            let carry = 0;
            for (let j = 0; j < bytes.length; j++) {
                carry = (bytes[j] / 256) | 0;
                bytes[j] %= 256;
                if (carry && j + 1 === bytes.length) bytes.push(0);
                if (j + 1 < bytes.length) bytes[j + 1] += carry;
            }
        }
        while (string[0] === '1' && bytes[bytes.length - 1] === 0) bytes.pop();
        return Uint8Array.from(bytes.reverse());
    },
    encode: bytes => {
        const digits = [0];
        for (let i = 0; i < bytes.length; i++) {
            for (let j = 0; j < digits.length; j++) digits[j] *= 256;
            digits[0] += bytes[i];
            let carry = 0;
            for (let j = 0; j < digits.length; j++) {
                carry = (digits[j] / 58) | 0;
                digits[j] %= 58;
                if (carry && j + 1 === digits.length) digits.push(0);
                if (j + 1 < digits.length) digits[j + 1] += carry;
            }
        }
        let string = '';
        while (digits[digits.length - 1] === 0) digits.pop();
        for (let i = digits.length - 1; i >= 0; i--) string += BASE58_ALPHABET[digits[i]];
        for (let i = 0; i < bytes.length && bytes[i] === 0; i++) string = '1' + string;
        return string;
    }
};

function arraysEqual(a, b) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
}

function validatePrivateKey(privateKeyBase58) {
    try {
        const keypairBytes = base58.decode(privateKeyBase58);
        if (keypairBytes.length !== 64) throw new Error(translations[currentLanguage].invalid_key_length || 'Invalid key length: expected 64 bytes');
        const privateKeyBytes = keypairBytes.slice(0, 32);
        const providedPublicKeyBytes = keypairBytes.slice(32);
        const derivedKeypair = nacl.sign.keyPair.fromSeed(privateKeyBytes);
        if (!arraysEqual(derivedKeypair.publicKey, providedPublicKeyBytes)) throw new Error(translations[currentLanguage].public_key_mismatch || 'Public key mismatch');
        return base58.encode(providedPublicKeyBytes);
    } catch (error) {
        console.error('Invalid private key:', error.message);
        document.getElementById('private-key-error').textContent = error.message;
        document.getElementById('private-key-error').classList.remove('hidden');
        return null;
    }
}

function updatePublicKey() {
    const privateKeyInput = document.getElementById('private-key-input').value.trim();
    const publicKeyInput = document.getElementById('public-key-input');
    const publicKey = validatePrivateKey(privateKeyInput);
    if (publicKey) {
        const shortPublicKey = publicKey.slice(0, 4) + '...' + publicKey.slice(-4);
        publicKeyInput.value = shortPublicKey;
        document.getElementById('private-key-error').classList.add('hidden');
        return { publicKey, privateKey: privateKeyInput };
    }
    return null;
}

let currentPublicKey = null;

const translations = {
    en: {
        dashboard: "Dashboard",
        wallets: "Wallets",
        docs: "Docs",
        logout: "Logout",
        donate_wallet: "Donate Wallet",
        asset_vault: "Asset Vault",
        inactive: "Inactive",
        active: "Active",
        linking: "Linking",
        asset_vault_description: "Manage your Solana wallet for token sniping.",
        balance: "Balance",
        wallet_address: "Wallet Address",
        private_key: "Private Key",
        position_size: "Position Size",
        edit_settings: "Edit Settings",
        trade_statistics: "Trade Statistics",
        trade_statistics_description: "Overview of your sniping activity.",
        trades_today: "Trades Today",
        trades_hourly: "Trades Hourly",
        total_trades: "Total Trades",
        pnl_performance: "PNL Performance",
        pnl_performance_description: "Your profit/loss in SOL over the last 14 days.",
        profit: "Profit",
        loss: "Loss",
        wallet_settings: "Wallet Settings",
        wallet_settings_description: "Manage your Solana wallets and sniping preferences.",
        enter_private_key: "Enter your Solana private key",
        invalid_private_key: "Invalid Solana private key.",
        primary_wallet_address: "Primary Wallet Address",
        position_size_error: "Position Size must be between 2% and 50%.",
        slippage_tolerance: "Slippage Tolerance (%)",
        slippage_tolerance_error: "Slippage Tolerance must be between 1% and 10%.",
        save_changes: "Save Changes",
        overview: "Overview",
        overview_description: "The Automatic Sniper Tool (AST) is designed to empower users to snipe newly launched tokens on the Solana blockchain with precision and speed. By leveraging an on-chain scanner and a machine learning (ML) model, AST identifies and filters tokens with positive expected value, enabling users to capitalize on early opportunities.",
        core_objective: "Core Objective",
        core_objective_description: "AST automates the process of sniping new tokens on Solana by scanning the blockchain in real-time and using an ML model to predict token potential, ensuring users can act swiftly and efficiently.",
        architecture: "Architecture",
        blockchain_scanner: "<strong>Blockchain Scanner:</strong> A server-side script continuously scans the Solana blockchain via API requests to nodes, detecting new token launches.",
        ml_model: "<strong>ML Model:</strong> An integrated machine learning model filters tokens based on their potential for positive mathematical expectation, prioritizing high-value opportunities.",
        user_interfaces: "<strong>User Interfaces:</strong> Access AST through a web application, an Android app, or a Telegram Mini App, providing flexibility and convenience.",
        user_access_workflow: "User Access & Workflow",
        authorization: "<strong>Authorization:</strong> Users log in to access a dashboard displaying trade logs, wallet balances, and sniping activity.",
        private_key_handling: "<strong>Private Key Handling:</strong> Your private key is transmitted via a secure protocol, stored only in RAM during operation, and never persisted on disk.",
        fund_management: "<strong>Fund Management:</strong> AST does not custody your funds. Instead, you delegate token management rights to the tool while your assets remain in your wallet.",
        security_transparency: "Security & Transparency",
        open_source: "<strong>Open Source:</strong> AST's codebase is fully open source, allowing users to audit and verify its security.",
        delegated_control: "<strong>Delegated Control:</strong> Fund management occurs through delegation, ensuring your assets never leave your wallet.",
        secure_key_handling: "<strong>Secure Key Handling:</strong> Private keys are stored in RAM during use and are not saved, minimizing exposure risks.",
        business_model: "Business Model",
        business_model_description: "For the MVP, AST operates on a profit-sharing model or voluntary donations. A small commission may be applied on profits, ensuring sustainability while keeping the tool accessible.",
        competitive_advantage: "Competitive Advantage",
        competitive_advantage_description: "AST offers lightning-fast token filtering, processing each Solana block in just <span class=\"highlight\">0.4 seconds</span>. This speed ensures you’re among the first buyers, maximizing your chances of securing high-potential tokens before others.",
        support: "Support",
        support_description: "Need assistance? Reach out to our team at <a href=\"mailto:support@ast.io\" class=\"underline highlight\">support@ast.io</a>. We’re here to help you make the most of AST.",
        disclaimer_terms: "Disclaimer & Terms of Use",
        disclaimer_content: "This software is open source and provided \"as is\". No guarantees of profit or functionality are given. You are solely responsible for all risks, taxes, and legal compliance. I do not manage your funds; I only provide a tool for swaps on Pump.fun via a trusted contract. AML risks are your responsibility. The key is stored in RAM and not saved. Profit share in SOL (if applicable) is a fee for the software, transferred manually by you. By using it, you accept all terms.",
        invalid_key_length: "Invalid key length: expected 64 bytes",
        public_key_mismatch: "Public key mismatch",
        private_key_required: "Private key is required for first setup."
    },
    ru: {
        dashboard: "Панель",
        wallets: "Кошельки",
        docs: "Доки",
        logout: "Выйти",
        donate_wallet: "Донаты",
        asset_vault: "Хранилище активов",
        inactive: "Неактивно",
        active: "Активно",
        linking: "Подключение",
        asset_vault_description: "Управление кошельком Solana.",
        balance: "Баланс",
        wallet_address: "Адрес кошелька",
        private_key: "Приватный ключ",
        position_size: "Размер позиции",
        edit_settings: "Редактировать настройки",
        trade_statistics: "Статистика торгов",
        trade_statistics_description: "Обзор вашей активности по снайпингу.",
        trades_today: "Сделки сегодня",
        trades_hourly: "Сделки за час",
        total_trades: "Всего сделок",
        pnl_performance: "Производительность PNL",
        pnl_performance_description: "Ваши прибыли/убытки в SOL за последние 14 дней.",
        profit: "Прибыль",
        loss: "Убыток",
        wallet_settings: "Настройки кошелька",
        wallet_settings_description: "Управляйте своими кошельками Solana и предпочтениями для снайпинга.",
        enter_private_key: "Введите ваш приватный ключ Solana",
        invalid_private_key: "Недействительный приватный ключ Solana.",
        primary_wallet_address: "Основной адрес кошелька",
        position_size_error: "Размер позиции должен быть от 2% до 50%.",
        slippage_tolerance: "Допуск проскальзывания (%)",
        slippage_tolerance_error: "Допуск проскальзывания должен быть от 1% до 10%.",
        save_changes: "Сохранить изменения",
        overview: "Обзор",
        overview_description: "Инструмент автоматического снайпинга (AST) разработан для того, чтобы пользователи могли с высокой точностью и скоростью снайпить недавно запущенные токены на блокчейне Solana. Используя сканер на блокчейне и модель машинного обучения (ML), AST идентифицирует и фильтрует токены с положительным ожидаемым значением, позволяя пользователям использовать ранние возможности.",
        core_objective: "Основная цель",
        core_objective_description: "AST автоматизирует процесс снайпинга новых токенов на Solana, сканируя блокчейн в реальном времени и используя модель ML для прогнозирования потенциала токенов, обеспечивая быстрые и эффективные действия пользователей.",
        architecture: "Архитектура",
        blockchain_scanner: "<strong>Сканер блокчейна:</strong> Серверный скрипт непрерывно сканирует блокчейн Solana через API-запросы к узлам, обнаруживая новые запуски токенов.",
        ml_model: "<strong>Модель ML:</strong> Интегрированная модель машинного обучения фильтрует токены на основе их потенциала для положительного математического ожидания, приоритизируя возможности с высокой ценностью.",
        user_interfaces: "<strong>Пользовательские интерфейсы:</strong> Доступ к AST через веб-приложение, приложение для Android или мини-приложение Telegram, обеспечивая гибкость и удобство.",
        user_access_workflow: "Доступ и рабочий процесс пользователя",
        authorization: "<strong>Авторизация:</strong> Пользователи входят в систему, чтобы получить доступ к панели управления, отображающей журналы торгов, балансы кошельков и активность по снайпингу.",
        private_key_handling: "<strong>Обработка приватного ключа:</strong> Ваш приватный ключ передается через безопасный протокол, хранится только в оперативной памяти во время работы и никогда не сохраняется на диске.",
        fund_management: "<strong>Управление средствами:</strong> AST не хранит ваши средства. Вместо этого вы делегируете права управления токенами инструменту, в то время как ваши активы остаются в вашем кошельке.",
        security_transparency: "Безопасность и прозрачность",
        open_source: "<strong>Открытый исходный код:</strong> Кодовая база AST полностью открыта, что позволяет пользователям проверять и подтверждать её безопасность.",
        delegated_control: "<strong>Делегированное управление:</strong> Управление средствами осуществляется через делегирование, гарантируя, что ваши активы никогда не покидают ваш кошелёк.",
        secure_key_handling: "<strong>Безопасная обработка ключей:</strong> Приватные ключи хранятся в оперативной памяти во время использования и не сохраняются, минимизируя риски раскрытия.",
        business_model: "Бизнес-модель",
        business_model_description: "Для MVP AST работает по модели разделения прибыли или добровольных пожертвований. Небольшая комиссия может взиматься с прибыли, обеспечивая устойчивость и сохраняя доступность инструмента.",
        competitive_advantage: "Конкурентное преимущество",
        competitive_advantage_description: "AST предлагает молниеносную фильтрацию токенов, обрабатывая каждый блок Solana всего за <span class=\"highlight\">0,4 секунды</span>. Эта скорость гарантирует, что вы будете среди первых покупателей, максимизируя ваши шансы на получение высокопотенциальных токенов раньше других.",
        support: "Поддержка",
        support_description: "Нужна помощь? Свяжитесь с нашей командой по адресу <a href=\"mailto:support@ast.io\" class=\"underline highlight\">support@ast.io</a>. Мы здесь, чтобы помочь вам максимально эффективно использовать AST.",
        disclaimer_terms: "Отказ от ответственности и условия использования",
        disclaimer_content: "Это программное обеспечение с открытым исходным кодом предоставляется \"как есть\". Никаких гарантий прибыли или функциональности не предоставляется. Вы несете полную ответственность за все риски, налоги и соблюдение законодательства. Я не управляю вашими средствами; я предоставляю только инструмент для обмена на Pump.fun через доверенный контракт. Риски AML — ваша ответственность. Ключ хранится в оперативной памяти и не сохраняется. Доля прибыли в SOL (если применимо) — это плата за программное обеспечение, переведенная вами вручную. Используя его, вы принимаете все условия.",
        invalid_key_length: "Недействительная длина ключа: ожидается 64 байта",
        public_key_mismatch: "Несоответствие публичного ключа",
        private_key_required: "Приватный ключ требуется для первой настройки."
    }
};

let currentLanguage = 'en';

function switchLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'ru' : 'en';
    document.getElementById('language-text').textContent = currentLanguage === 'en' ? 'EN' : 'RU';
    document.documentElement.lang = currentLanguage;
    updateContent();
    localStorage.setItem('language', currentLanguage);
}

function updateContent() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = translations[currentLanguage][key] || translations.en[key];
        if (translation.includes('<') && translation.includes('>')) {
            element.innerHTML = translation;
        } else {
            element.textContent = translation;
        }
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.placeholder = translations[currentLanguage][key] || translations.en[key];
    });
    const activePage = localStorage.getItem('activePage') || 'dash';
    document.getElementById('page-title').textContent = translations[currentLanguage][activePage] || translations.en[activePage];
    const statusDot = document.getElementById('status-dot');
    const status = statusDot.classList.contains('active') ? 'active' : statusDot.classList.contains('linking') ? 'linking' : 'inactive';
    statusDot.innerHTML = `
                <svg class="icon-small" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="6"/>
                </svg>
                ${translations[currentLanguage][status] || translations.en[status]}
            `;
}

function validateInputs() {
    const privateKeyInput = document.getElementById('private-key-input').value.trim();
    const positionSize = parseFloat(document.getElementById('position-size-input').value);
    const slippageTolerance = parseFloat(document.getElementById('slippage-tolerance-input').value);
    const saveButton = document.getElementById('save-settings-button');

    let isValid = true;
    if (privateKeyInput) {
        const keys = updatePublicKey();
        if (!keys) {
            isValid = false;
        } else {
            document.getElementById('private-key-error').classList.add('hidden');
        }
    } else {
        if (!currentPublicKey) {
            document.getElementById('private-key-error').textContent = translations[currentLanguage].private_key_required || 'Private key is required for first setup.';
            document.getElementById('private-key-error').classList.remove('hidden');
            isValid = false;
        } else {
            document.getElementById('private-key-error').classList.add('hidden');
        }
    }

    if (document.getElementById('position-size-input').value === '' || isNaN(positionSize) || positionSize < 2 || positionSize > 50) {
        document.getElementById('position-size-error').textContent = translations[currentLanguage].position_size_error || 'Position Size must be between 2% and 50%.';
        document.getElementById('position-size-error').classList.remove('hidden');
        isValid = false;
    } else {
        document.getElementById('position-size-error').classList.add('hidden');
    }

    if (document.getElementById('slippage-tolerance-input').value === '' || isNaN(slippageTolerance) || slippageTolerance < 1 || slippageTolerance > 10) {
        document.getElementById('slippage-tolerance-error').textContent = translations[currentLanguage].slippage_tolerance_error || 'Slippage Tolerance must be between 1% and 10%.';
        document.getElementById('slippage-tolerance-error').classList.remove('hidden');
        isValid = false;
    } else {
        document.getElementById('slippage-tolerance-error').classList.add('hidden');
    }

    saveButton.disabled = !isValid;
}

async function checkAuth() {
    const userId = localStorage.getItem('userId');
    if (!userId) {
        window.location.href = '/login.html';
        return false;
    }
    try {
        const response = await fetch(`/check-auth?userId=${userId}`, {
            method: 'GET',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Auth check failed');
        const data = await response.json();
        if (!data.authenticated) {
            localStorage.removeItem('userId');
            window.location.href = '/login.html';
            return false;
        }
        return true;
    } catch (error) {
        console.error('Error checking auth:', error);
        localStorage.removeItem('userId');
        window.location.href = '/login.html';
        return false;
    }
}

async function logout() {
    const userId = localStorage.getItem('userId');
    if (userId) {
        try {
            await fetch('/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId }),
            });
        } catch (error) {
            console.error('Error during logout:', error);
        }
    }
    localStorage.removeItem('userId');
    window.location.href = '/login.html';
}

function setTheme(theme) {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    if (theme === 'dark') {
        body.classList.remove('light');
        body.classList.add('dark');
        themeIcon.innerHTML = `<path d="M21.4 13.7C20.6 13.9 19.8 14 19 14c-5 0-9-4-9-9 0-.8.1-1.6.3-2.4-4.2 1.1-7.3 4.9-7.3 9.4 0 5.5 4.5 10 10 10 4.5 0 8.3-3 9.4-7.3z"/>`;
    } else {
        body.classList.remove('dark');
        body.classList.add('light');
        themeIcon.innerHTML = `<circle cx="12" cy="12" r="4"/><circle cx="12" cy="4" r="1"/><circle cx="12" cy="20" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="20" cy="12" r="1"/><circle cx="6.34" cy="6.34" r="1"/><circle cx="17.66" cy="17.66" r="1"/><circle cx="6.34" cy="17.66" r="1"/><circle cx="17.66" cy="6.34" r="1"/>`;
    }
    if (chartInstance) {
        updateChartColors(theme);
    }
}

function toggleTheme() {
    const body = document.body;
    const newTheme = body.classList.contains('dark') ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function setActivePage(page) {
    document.querySelectorAll('.page-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`${page}-content`).classList.remove('hidden');
    document.getElementById('page-title').textContent = translations[currentLanguage][page] || translations.en[page];
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.getAttribute('data-page') === page);
    });
    localStorage.setItem('activePage', page);
    if (page === 'wallets') {
        validateInputs();
    }
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        setActivePage(link.getAttribute('data-page'));
    });
});

let chartInstance;

function formatDate(date) {
    return date.toLocaleString(currentLanguage === 'en' ? 'en-US' : 'ru-RU', { month: 'short', day: 'numeric' });
}

function getLast14Days() {
    const dates = [];
    const today = new Date();
    for (let i = 13; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        dates.push(formatDate(date));
    }
    return dates;
}

function formatToSignificant(value) {
    if (value === 0) return '0 SOL';
    const absValue = Math.abs(value);
    if (absValue >= 1) return `${value.toFixed(3)} SOL`;
    const digits = -Math.floor(Math.log10(absValue)) + 1;
    return `${value.toFixed(Math.min(digits, 9))} SOL`;
}

function createChart(theme) {
    const ctx = document.getElementById('uptimeChart').getContext('2d');
    const isLightTheme = theme === 'light';
    const gridColor = isLightTheme ? '#e5e7eb' : '#2d2d2d';
    const tickColor = isLightTheme ? '#6b7280' : '#9ca3af';

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: getLast14Days(),
            datasets: [{
                label: translations[currentLanguage].pnl_performance || 'PNL',
                data: Array(14).fill(0),
                rawData: Array(14).fill(0),
                backgroundColor: data => data.raw >= 0 ? 'rgba(46, 125, 50, 0.9)' : 'rgba(211, 47, 47, 0.9)',
                borderWidth: 0,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const rawValue = context.dataset.rawData[context.dataIndex];
                            return `${translations[currentLanguage].pnl_performance || 'PNL'}: ${formatToSignificant(rawValue)}`;
                        }
                    },
                    padding: 10,
                    bodyFont: { size: 14 },
                    displayColors: false,
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: tickColor } },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: tickColor,
                        callback: value => formatToSignificant(value),
                        stepSize: null
                    },
                    grid: { color: gridColor }
                }
            }
        }
    });
}

function updateChartColors(theme) {
    const isLightTheme = theme === 'light';
    const gridColor = isLightTheme ? '#e5e7eb' : '#2d2d2d';
    const tickColor = isLightTheme ? '#6b7280' : '#9ca3af';

    chartInstance.options.scales.x.ticks.color = tickColor;
    chartInstance.options.scales.y.ticks.color = tickColor;
    chartInstance.options.scales.y.grid.color = gridColor;
    chartInstance.data.labels = getLast14Days();
    chartInstance.data.datasets[0].label = translations[currentLanguage].pnl_performance || 'PNL';
    chartInstance.update();
}

function copyDonateAddress(event) {
    event.stopPropagation();
    const walletAddress = 'q4tqEU7BJ7GNkazQAKci7X1DBPj8jRzWyFpn6TzZBpe';
    navigator.clipboard.writeText(walletAddress).then(() => {
        const popup = document.querySelector('.donate-popup');
        const walletSpan = popup.querySelector('.wallet-address');
        const originalText = walletSpan.textContent;
        walletSpan.textContent = translations[currentLanguage].copied || 'Copied!';
        walletSpan.style.color = '#FFA500';
        setTimeout(() => {
            walletSpan.textContent = originalText;
            walletSpan.style.color = '#32CD32';
        }, 1000);
    });
}

function updateStatus(status) {
    const statusDot = document.getElementById('status-dot');
    statusDot.className = `status-dot ${status}`;
    statusDot.innerHTML = `
                <svg class="icon-small" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="6"/>
                </svg>
                ${translations[currentLanguage][status] || translations.en[status]}
            `;
    document.getElementById('bot-toggle').checked = status === 'active';
}

async function loadDashboardData() {
    const userId = localStorage.getItem('userId');
    if (!userId) return;

    try {
        const response = await fetch(`/dashboard?userId=${userId}`, { method: 'GET', credentials: 'include' });
        if (!response.ok) throw new Error('Failed to load dashboard data');
        const data = await response.json();

        document.getElementById('balance-display').textContent = `${parseFloat(data.balance || 0).toFixed(3)} SOL`;
        currentPublicKey = data.publicKey || null;
        document.getElementById('public-key-display').textContent = data.publicKey ? `${data.publicKey.slice(0, 4)}...${data.publicKey.slice(-4)}` : translations[currentLanguage].not_set || 'Not set';
        document.getElementById('private-key-display').textContent = data.privateKeyPreview || translations[currentLanguage].not_set || 'Not set';
        document.getElementById('position-size-display').textContent = `${data.positionSize || 25}%`;
        document.getElementById('success-rate-display').textContent = `${Math.round(data.successRate || 0)} %`;
        document.getElementById('trades-today-display').textContent = data.tradesToday || 0;
        document.getElementById('trades-hourly-display').textContent = data.tradesHourly || 0;
        document.getElementById('total-trades-display').textContent = data.totalTrades || 0;

        updateStatus(data.status || 'inactive');

        document.getElementById('public-key-input').value = data.publicKey ? `${data.publicKey.slice(0, 4)}...${data.publicKey.slice(-4)}` : '';
        document.getElementById('position-size-input').value = data.positionSize || 25;
        document.getElementById('slippage-tolerance-input').value = data.slippageTolerance || 2;

        validateInputs();

        const pnlDataRaw = data.pnl || [];
        const pnlByDate = {};
        pnlDataRaw.forEach(item => {
            const date = new Date(item.date).toISOString().split('T')[0];
            if (!pnlByDate[date]) {
                pnlByDate[date] = 0;
            }
            pnlByDate[date] += item.value;
        });

        const labels = getLast14Days();
        const today = new Date();
        const chartData = Array(14).fill(0).map((_, i) => {
            const date = new Date(today);
            date.setDate(today.getDate() - (13 - i));
            const dateStr = date.toISOString().split('T')[0];
            const value = pnlByDate[dateStr] || 0;
            return { value: Math.abs(value), raw: value };
        });

        chartInstance.data.labels = labels;
        chartInstance.data.datasets[0].data = chartData.map(item => item.value);
        chartInstance.data.datasets[0].rawData = chartData.map(item => item.raw);
        chartInstance.data.datasets[0].backgroundColor = chartData.map(item =>
            item.raw >= 0 ? 'rgba(46, 125, 50, 0.9)' : 'rgba(211, 47, 47, 0.9)'
        );

        const values = chartData.map(item => item.value);
        const maxValue = Math.max(...values, 0);
        if (maxValue > 0) {
            const magnitude = Math.pow(10, Math.floor(Math.log10(maxValue)));
            const scaleMax = Math.ceil(maxValue / magnitude * 1.2) * magnitude;
            chartInstance.options.scales.y.max = scaleMax;
            chartInstance.options.scales.y.ticks.stepSize = scaleMax / 5;
        } else {
            chartInstance.options.scales.y.max = 0.0001;
            chartInstance.options.scales.y.ticks.stepSize = 0.00002;
        }

        chartInstance.update();
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function toggleBotStatus(checkbox) {
    const userId = localStorage.getItem('userId');
    if (!userId || !currentPublicKey) {
        checkbox.checked = false;
        updateStatus('inactive');
        return;
    }

    const isActive = checkbox.checked;
    updateStatus('linking');

    try {
        const response = await fetch('/bot/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId, publicKey: currentPublicKey, isActive }),
        });
        if (!response.ok) throw new Error('Failed to toggle bot');
        await loadDashboardData();
    } catch (error) {
        console.error('Error toggling bot:', error);
        checkbox.checked = !isActive;
        await loadDashboardData();
    }
}

async function saveWalletSettings() {
    const userId = localStorage.getItem('userId');
    if (!userId) return;

    const privateKeyInput = document.getElementById('private-key-input').value.trim();
    const positionSize = parseFloat(document.getElementById('position-size-input').value);
    const slippageTolerance = parseFloat(document.getElementById('slippage-tolerance-input').value);

    let settings = {};

    if (privateKeyInput) {
        const keys = updatePublicKey();
        if (!keys) return;
        settings.publicKey = keys.publicKey;
        settings.privateKey = keys.privateKey;
    } else if (currentPublicKey) {
        settings.publicKey = currentPublicKey;
    }

    settings.positionSize = positionSize;
    settings.slippageTolerance = slippageTolerance;

    try {
        const response = await fetch('/wallet/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId, ...settings }),
        });
        if (!response.ok) throw new Error('Failed to save wallet settings');
        await loadDashboardData();
        setActivePage('dash');
    } catch (error) {
        console.error('Error saving wallet settings:', error);
    }
}

async function initializePage() {
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) return;

    document.getElementById('main-content').classList.remove('content-hidden');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    createChart(savedTheme);
    setTheme(savedTheme);
    const savedPage = localStorage.getItem('activePage') || 'dash';
    setActivePage(savedPage);

    await loadDashboardData();

    document.getElementById('private-key-input').addEventListener('input', validateInputs);
    document.getElementById('position-size-input').addEventListener('input', validateInputs);
    document.getElementById('slippage-tolerance-input').addEventListener('input', validateInputs);
}

initializePage();
