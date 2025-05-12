const express = require('express');
const path = require('path');
const { registerOrLogin, verifyOTP } = require('./auth');
const { pgPool } = require('./db');
const Redis = require('ioredis');
const WebSocket = require('ws');
const { Connection, PublicKey } = require('@solana/web3.js');

const app = express();
const redis = new Redis({
    host: process.env.REDIS_HOST || 'redis',
    port: process.env.REDIS_PORT || 6379,
});

const solanaConnection = new Connection('https://api.mainnet-beta.solana.com', 'confirmed');
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => console.log('Connected to trade_manager WebSocket server'));
ws.on('error', (err) => console.error('WebSocket error:', err));

app.use(express.static(path.join(__dirname, '../public')));
app.use(express.json());

// Проверка авторизации (с Redis)
app.get('/check-auth', async (req, res) => {
    const userId = req.query.userId;
    if (!userId) return res.status(401).json({ error: 'No user ID provided' });
    const sessionExists = await redis.exists(`session:${userId}`);
    res.json({ authenticated: !!sessionExists });
});

// Выход (с Redis)
app.post('/logout', async (req, res) => {
    const { userId } = req.body;
    if (!userId) return res.status(400).json({ error: 'No user ID provided' });
    await redis.del(`session:${userId}`);
    res.json({ success: true });
});

// Авторизация (с Redis через auth.js)
app.post('/auth', async (req, res) => {
    const { email } = req.body;
    if (!email) return res.status(400).json({ error: 'Email is required' });
    try {
        const result = await registerOrLogin(email);
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/verify', async (req, res) => {
    const { email, otp } = req.body;
    if (!email || !otp) return res.status(400).json({ error: 'Email and OTP are required' });
    try {
        const result = await verifyOTP(email, otp);
        res.json(result);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// Добавление/обновление кошелька (через WS)
app.post('/wallet/add', async (req, res) => {
    const { userId, publicKey, privateKey, positionSize, slippageTolerance } = req.body;
    if (!userId) return res.status(400).json({ error: 'Missing userId' });

    const client = await pgPool.connect();
    try {
        await client.query('BEGIN');

        const existingWalletRes = await client.query('SELECT public_key, is_trading_active FROM wallets WHERE user_id = $1', [userId]);
        const existingWallet = existingWalletRes.rows[0];

        if (!existingWallet && (!publicKey || !privateKey)) {
            await client.query('ROLLBACK');
            return res.status(400).json({ error: 'Private key and public key are required for first wallet setup' });
        }

        if (publicKey && privateKey) {
            if (existingWallet && existingWallet.public_key !== publicKey) {
                if (existingWallet.is_trading_active) {
                    await client.query('UPDATE wallets SET is_trading_active = false WHERE user_id = $1 AND public_key = $2', 
                        [userId, existingWallet.public_key]);
                    ws.send(JSON.stringify({ action: 'bot:stop', publicKey: existingWallet.public_key }));
                }
                await client.query('DELETE FROM wallets WHERE user_id = $1 AND public_key = $2', 
                    [userId, existingWallet.public_key]);
            }

            const privateKeyPreview = `****${privateKey.slice(-4)}`;
            await client.query(`
                INSERT INTO wallets (user_id, public_key, private_key_preview, position_size, slippage_tolerance, is_trading_active)
                VALUES ($1, $2, $3, $4, $5, false)
                ON CONFLICT (public_key) DO UPDATE
                SET private_key_preview = $3, position_size = $4, slippage_tolerance = $5, is_trading_active = false
            `, [userId, publicKey, privateKeyPreview, positionSize, slippageTolerance]);

            ws.send(JSON.stringify({ action: 'wallet:added', userId, publicKey, privateKey }));
        } else if (existingWallet) {
            await client.query(`
                UPDATE wallets 
                SET position_size = $1, slippage_tolerance = $2
                WHERE user_id = $3 AND public_key = $4
            `, [positionSize, slippageTolerance, userId, existingWallet.public_key]);
        }

        await client.query('COMMIT');
        res.json({ success: true });
    } catch (err) {
        await client.query('ROLLBACK');
        console.error('Error saving wallet:', err);
        res.status(500).json({ error: 'Server error' });
    } finally {
        client.release();
    }
});

// Переключение бота (через WS)
app.post('/bot/toggle', async (req, res) => {
    const { userId, publicKey, isActive } = req.body;
    if (!userId || !publicKey) return res.status(400).json({ error: 'Missing required fields' });

    const client = await pgPool.connect();
    try {
        await client.query('UPDATE wallets SET is_trading_active = $1 WHERE user_id = $2 AND public_key = $3', 
            [isActive, userId, publicKey]);
        ws.send(JSON.stringify({ action: isActive ? 'bot:start' : 'bot:stop', publicKey }));
        res.json({ success: true });
    } catch (err) {
        console.error('Error toggling bot:', err);
        res.status(500).json({ error: 'Server error' });
    } finally {
        client.release();
    }
});

// Загрузка данных дашборда (статус из БД)
app.get('/dashboard', async (req, res) => {
    const userId = req.query.userId;
    if (!userId) return res.status(400).json({ error: 'No user ID provided' });

    const client = await pgPool.connect();
    try {
        const walletRes = await client.query('SELECT * FROM wallets WHERE user_id = $1 LIMIT 1', [userId]);
        const wallet = walletRes.rows[0] || {};

        const statsRes = await client.query(`
            SELECT 
                COALESCE(SUM(CASE WHEN is_success THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100, 0) as success_rate,
                COALESCE(COUNT(CASE WHEN date = CURRENT_DATE THEN 1 END), 0) as trades_today,
                COALESCE(COUNT(CASE WHEN trade_date > NOW() - INTERVAL '1 hour' THEN 1 END), 0) as trades_hourly,
                COALESCE(COUNT(*), 0) as total_trades,
                json_agg(json_build_object('date', date, 'value', pnl)) as pnl
            FROM trades_stats 
            WHERE public_key = $1
        `, [wallet.public_key || '']); // Используем public_key из wallet
        const stats = statsRes.rows[0] || {};

        let balance = 0;
        let status = wallet.public_key ? 'linking' : 'inactive'; // По умолчанию linking, если кошелёк есть
        if (wallet.public_key) {
            try {
                const publicKey = new PublicKey(wallet.public_key);
                const balanceLamports = await solanaConnection.getBalance(publicKey);
                balance = balanceLamports / 1e9;

                // Статус берется напрямую из БД
                status = wallet.is_trading_active ? 'active' : 'inactive';
            } catch (err) {
                console.error('Error fetching Solana balance:', err);
                balance = 0;
            }
        }

        res.json({
            balance: balance.toFixed(3),
            publicKey: wallet.public_key || '',
            privateKeyPreview: wallet.private_key_preview || '',
            positionSize: wallet.position_size || 25,
            slippageTolerance: wallet.slippage_tolerance || 2,
            status,
            successRate: stats.success_rate || 0,
            tradesToday: stats.trades_today || 0,
            tradesHourly: stats.trades_hourly || 0,
            totalTrades: stats.total_trades || 0,
            pnl: stats.pnl || []
        });
    } catch (err) {
        console.error('Error loading dashboard:', err);
        res.status(500).json({ error: 'Server error' });
    } finally {
        client.release();
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public', 'login.html'));
});

const PORT = process.env.SERVER_PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});