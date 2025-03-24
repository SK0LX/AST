const express = require('express');
const path = require('path');
const { registerOrLogin, verifyOTP } = require('./auth');
const Redis = require('ioredis');

const app = express();
const redis = new Redis({
  host: process.env.REDIS_HOST || 'redis',
  port: process.env.REDIS_PORT || 6379,
});

app.use(express.static(path.join(__dirname, '../public')));
app.use(express.json());

// Маршрут для проверки авторизации
app.get('/check-auth', async (req, res) => {
  const userId = req.query.userId;
  if (!userId) {
    return res.status(401).json({ error: 'No user ID provided' });
  }
  try {
    const sessionExists = await redis.exists(`session:${userId}`);
    if (sessionExists) {
      res.json({ authenticated: true });
    } else {
      res.status(401).json({ authenticated: false, error: 'Session expired or invalid' });
    }
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

// Маршрут для выхода из системы
app.post('/logout', async (req, res) => {
  const { userId } = req.body;
  if (!userId) {
    return res.status(400).json({ error: 'No user ID provided' });
  }
  try {
    await redis.del(`session:${userId}`);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/auth', async (req, res) => {
  const { email } = req.body;
  if (!email) {
    return res.status(400).json({ error: 'Email is required' });
  }
  try {
    const result = await registerOrLogin(email);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/verify', async (req, res) => {
  const { email, otp } = req.body;
  if (!email || !otp) {
    return res.status(400).json({ error: 'Email and OTP are required' });
  }
  try {
    const result = await verifyOTP(email, otp);
    res.json(result);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../public', 'login.html'));
});

const PORT = process.env.SERVER_PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});