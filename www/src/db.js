require('dotenv').config();
const { Pool } = require('pg');
const { createClient } = require('redis');

// PostgreSQL
const pgPool = new Pool({
  user: process.env.PG_USER,
  host: process.env.PG_HOST,
  database: process.env.PG_DB,
  password: process.env.PG_PASSWORD,
  port: process.env.PG_PORT,
});

// Redis
const redisClient = createClient({
  url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`,
});

redisClient.connect().catch(console.error);

module.exports = { pgPool, redisClient };