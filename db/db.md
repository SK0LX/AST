# Sniper DB Setup

## Overview
This project sets up a database environment with PostgreSQL and Redis for tracking trades. Includes pgAdmin and Redis Commander for web-based management.

## Services
- **PostgreSQL**: Main database for user and trade stats.
- **Redis**: Temporary storage for OTP codes.
- **pgAdmin**: Web interface for PostgreSQL.
- **Redis Commander**: Web interface for Redis.

## Prerequisites
- Docker
- Docker Compose

## Running
1. Save the `docker-compose.yml` file.
2. Run:
   ```bash
   docker-compose up -d
   ```