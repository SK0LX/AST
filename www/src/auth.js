require('dotenv').config();
const { pgPool, redisClient } = require('./db');
const nodemailer = require('nodemailer');

// Настройка отправки email
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS,
  },
});

// Генерация OTP
function generateOTP() {
  return Math.floor(100000 + Math.random() * 900000).toString(); // 6 цифр
}

// HTML-шаблон письма в стиле твоего сайта
function generateOTPEmail(email, otp) {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your OTP Code - AST</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
          /* Базовые стили для тёмной темы */
          body {
            font-family: 'Inter', sans-serif;
            background-color: #0a0a0a;
            color: #e5e7eb;
            margin: 0;
            padding: 0;
          }
          table {
            background-color: #0a0a0a;
          }
          h2 {
            color: #e5e7eb;
          }
          p {
            color: #9ca3af;
          }
          .otp-box {
            background-color: #1a1a1a;
            border: 1px solid #2d2d2d;
            border-radius: 8px;
            padding: 16px;
          }
          .otp-code {
            font-size: 24px;
            font-weight: 600;
            color: #e5e7eb;
            letter-spacing: 8px;
          }
          .footer {
            color: #6b7280;
          }
  
          /* Поддержка светлой темы */
          @media (prefers-color-scheme: light) {
            body {
              background-color: #ffffff !important;
              color: #000000 !important;
            }
            table {
              background-color: #ffffff !important;
            }
            h2 {
              color: #000000 !important;
            }
            p {
              color: #6b7280 !important;
            }
            .otp-box {
              background-color: #f3f4f6 !important;
              border: 1px solid #e5e7eb !important;
            }
            .otp-code {
              color: #000000 !important;
            }
            .footer {
              color: #6b7280 !important;
            }
          }
        </style>
      </head>
      <body>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td align="center" style="padding: 20px 0;">
              <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%;">
                <!-- Header -->
                <tr>
                  <td align="center" style="padding: 20px 0;">
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td align="center">
                          <svg style="height: 32px; width: 32px; color: #ffffff;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <circle cx="12" cy="12" r="6"/>
                            <circle cx="12" cy="12" r="2"/>
                            <path d="M12 2v4"/>
                            <path d="M12 18v4"/>
                            <path d="M2 12h4"/>
                            <path d="M18 12h4"/>
                          </svg>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <!-- Title -->
                <tr>
                  <td align="center" style="padding: 10px 0;">
                    <h2 style="font-size: 24px; font-weight: 600; margin: 0;">Your OTP Code</h2>
                  </td>
                </tr>
                <!-- Description -->
                <tr>
                  <td align="center" style="padding: 10px 20px;">
                    <p style="font-size: 14px; margin: 0;">
                      Hello! You requested a one-time password to sign in to your AST account.
                    </p>
                  </td>
                </tr>
                <!-- OTP Box -->
                <tr>
                  <td align="center" style="padding: 20px 0;">
                    <table cellpadding="0" cellspacing="0" border="0" class="otp-box">
                      <tr>
                        <td align="center">
                          <span class="otp-code">${otp}</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <!-- Description -->
                <tr>
                  <td align="center" style="padding: 10px 20px;">
                    <p style="font-size: 14px; margin: 0;">
                      This code will expire in 5 minutes. If you didn’t request this, please ignore this email.
                    </p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td align="center" style="padding: 20px 0;">
                    <p class="footer" style="font-size: 12px; margin: 0;">
                      © This is a test open-source project by AST, 2025
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
      </html>
    `;
}
// Регистрация или получение OTP
async function registerOrLogin(email) {
  const client = await pgPool.connect();
  try {
    let res = await client.query('SELECT id FROM users WHERE email = $1', [email]);
    let userId;

    if (res.rowCount === 0) {
      res = await client.query(
        'INSERT INTO users (id, email) VALUES (uuid_generate_v4(), $1) RETURNING id',
        [email]
      );
      userId = res.rows[0].id;
    } else {
      userId = res.rows[0].id;
    }

    const otp = generateOTP();
    await redisClient.set(`otp:${email}`, otp, { EX: 300 }); // 5 минут

    await transporter.sendMail({
      from: `"AST" <${process.env.EMAIL_USER}>`,
      to: email,
      subject: 'Your OTP Code - AST',
      html: generateOTPEmail(email, otp),
    });

    return { message: 'OTP sent', userId };
  } catch (err) {
    console.error('Error during registration:', err);
    throw new Error('Error during registration');
  } finally {
    client.release();
  }
}

// Проверка OTP
async function verifyOTP(email, otp) {
  const storedOTP = await redisClient.get(`otp:${email}`);
  if (!storedOTP || storedOTP !== otp) {
    throw new Error('Invalid or expired OTP');
  }

  await redisClient.del(`otp:${email}`);
  const res = await pgPool.query('SELECT id FROM users WHERE email = $1', [email]);
  const userId = res.rows[0].id;

  // Создаём сессию в Redis
  try {
    await redisClient.set(`session:${userId}`, email, { EX: 3600 }); // Сессия на 1 час
    console.log(`Session created for userId: ${userId}, email: ${email}`); // Отладка
    const sessionValue = await redisClient.get(`session:${userId}`);
    console.log(`Session value in Redis: ${sessionValue}`); // Должно вывести email
  } catch (err) {
    console.error('Error saving session to Redis:', err);
    throw new Error('Failed to save session');
  }

  return { message: 'Login successful', userId };
}

module.exports = { registerOrLogin, verifyOTP };