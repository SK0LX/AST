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
        if (keypairBytes.length !== 64) throw new Error('Invalid key length: expected 64 bytes');
        const privateKeyBytes = keypairBytes.slice(0, 32);
        const providedPublicKeyBytes = keypairBytes.slice(32);
        const derivedKeypair = nacl.sign.keyPair.fromSeed(privateKeyBytes);
        if (!arraysEqual(derivedKeypair.publicKey, providedPublicKeyBytes)) throw new Error('Public key mismatch');
        return base58.encode(providedPublicKeyBytes);
    } catch (error) {
        console.error('Invalid private key:', error.message);
        document.getElementById('private-key-error').textContent = error.message;
        document.getElementById('private-key-error').classList.remove('hidden');
        return null;
    }
}

function updatePublicKey() {
    const privateKeyInput = document.getElementById('private-key-input').value;
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

function validateSettings(existingPublicKey) {
    let isValid = true;
    const settings = {};

    const positionSize = parseFloat(document.getElementById('position-size-input').value);
    if (isNaN(positionSize) || positionSize < 2 || positionSize > 50) {
        document.getElementById('position-size-error').classList.remove('hidden');
        isValid = false;
    } else {
        document.getElementById('position-size-error').classList.add('hidden');
        settings.positionSize = positionSize;
    }

    const slippageTolerance = parseFloat(document.getElementById('slippage-tolerance-input').value);
    if (isNaN(slippageTolerance) || slippageTolerance < 1 || slippageTolerance > 10) {
        document.getElementById('slippage-tolerance-error').classList.remove('hidden');
        isValid = false;
    } else {
        document.getElementById('slippage-tolerance-error').classList.add('hidden');
        settings.slippageTolerance = slippageTolerance;
    }

    const privateKeyInput = document.getElementById('private-key-input').value;
    if (!existingPublicKey && !privateKeyInput) {
        document.getElementById('private-key-error').textContent = 'Private key is required for first setup.';
        document.getElementById('private-key-error').classList.remove('hidden');
        isValid = false;
    } else if (privateKeyInput) {
        const keys = updatePublicKey();
        if (!keys) {
            isValid = false;
        } else {
            settings.publicKey = keys.publicKey;
            settings.privateKey = keys.privateKey;
        }
    } else if (existingPublicKey) {
        settings.publicKey = existingPublicKey; // Используем существующий ключ, если новый не введён
    }

    return isValid ? settings : null;
}

async function saveWalletSettings() {
    const existingPublicKey = document.getElementById('public-key-display').textContent.includes('...')
        ? document.getElementById('public-key-display').textContent.replace('...', '') // Примерная реконструкция, лучше хранить полный ключ
        : null;
    const settings = validateSettings(existingPublicKey);
    if (!settings) return;

    const userId = localStorage.getItem('userId');
    try {
        const response = await fetch('/wallet/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId, ...settings })
        });
        const data = await response.json();
        if (response.ok) {
            const shortPublicKey = settings.publicKey.slice(0, 4) + '...' + settings.publicKey.slice(-4);
            const shortPrivateKey = settings.privateKey ? '****' + settings.privateKey.slice(-4) : document.getElementById('private-key-display').textContent;
            document.getElementById('public-key-display').textContent = shortPublicKey;
            document.getElementById('private-key-display').textContent = shortPrivateKey;
            document.getElementById('position-size-display').textContent = `${settings.positionSize}%`;
            
            await loadDashboardData();
            setActivePage('dash');
        } else {
            console.error('Error saving wallet:', data.error);
        }
    } catch (error) {
        console.error('Error saving wallet:', error);
    }
}

async function toggleBotStatus(toggle) {
    const userId = localStorage.getItem('userId');
    const publicKeyFull = document.getElementById('public-key-input').value.includes('...') 
        ? validatePrivateKey(document.getElementById('private-key-input').value)?.publicKey 
        : document.getElementById('public-key-input').value;
    if (!publicKeyFull) return;

    const isActive = toggle.checked;
    document.getElementById('bot-toggle').disabled = true;
    setStatusById(2); // Linking

    try {
        const response = await fetch('/bot/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId, publicKey: publicKeyFull, isActive })
        });
        if (response.ok) {
            setTimeout(() => {
                setStatusById(isActive ? 1 : 3);
                document.getElementById('bot-toggle').disabled = false;
            }, 1000);
        }
    } catch (error) {
        console.error('Error toggling bot:', error);
        setStatusById(3);
        document.getElementById('bot-toggle').disabled = false;
    }
}

function setStatusById(statusId) {
    const statusDot = document.getElementById('status-dot');
    if (statusId === 1) {
        statusDot.className = 'status-dot connected flex items-center gap-2';
        statusDot.innerHTML = `<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="6"/></svg>Active`;
    } else if (statusId === 2) {
        statusDot.className = 'status-dot connecting flex items-center gap-2';
        statusDot.innerHTML = `<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="6"/></svg>Linking`;
    } else {
        statusDot.className = 'status-dot offline flex items-center gap-2';
        statusDot.innerHTML = `<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="6"/></svg>Inactive`;
    }
}

async function loadDashboardData() {
    const userId = localStorage.getItem('userId');
    try {
        const response = await fetch(`/dashboard?userId=${userId}`);
        const data = await response.json();
        if (response.ok) {
            document.getElementById('balance-display').textContent = `${parseFloat(data.balance).toFixed(3)} SOL`;
            document.getElementById('public-key-display').textContent = data.publicKey ? `${data.publicKey.slice(0, 4)}...${data.publicKey.slice(-4)}` : 'Not set';
            document.getElementById('private-key-display').textContent = data.privateKeyPreview || 'Not set';
            document.getElementById('position-size-display').textContent = `${data.positionSize}%`;
            document.getElementById('success-rate-display').textContent = `${data.successRate}%`;
            document.getElementById('trades-today-display').textContent = data.tradesToday;
            document.getElementById('trades-hourly-display').textContent = data.tradesHourly;
            document.getElementById('total-trades-display').textContent = data.totalTrades;
            document.getElementById('bot-toggle').checked = data.isTradingActive;
            setStatusById(data.isTradingActive ? 1 : 3);

            if (data.pnl && data.pnl.length) {
                chartInstance.data.labels = data.pnl.map(entry => entry.date);
                chartInstance.data.datasets[0].data = data.pnl.map(entry => entry.value);
                chartInstance.update();
            }

            document.getElementById('public-key-input').value = data.publicKey ? `${data.publicKey.slice(0, 4)}...${data.publicKey.slice(-4)}` : '';
            document.getElementById('position-size-input').value = data.positionSize;
            document.getElementById('slippage-tolerance-input').value = data.slippageTolerance;
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

document.getElementById('private-key-input').addEventListener('input', updatePublicKey);