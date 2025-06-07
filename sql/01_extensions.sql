-- Extensions required for the application
-- Run this first to enable necessary PostgreSQL extensions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search in chat
CREATE EXTENSION IF NOT EXISTS "citext"; -- For case-insensitive email