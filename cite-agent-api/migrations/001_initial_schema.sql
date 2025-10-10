-- Nocturnal Archive Database Schema
-- Initial migration for user auth, sessions, queries, and downloads

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    tokens_used_today INTEGER DEFAULT 0,
    last_token_reset DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Queries table (for analytics)
CREATE TABLE IF NOT EXISTS queries (
    query_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    query_text TEXT,
    response_text TEXT,
    tokens_used INTEGER NOT NULL,
    cost DECIMAL(10, 6) NOT NULL,
    model VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id);
CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_queries_user_timestamp ON queries(user_id, timestamp);

-- Downloads table (for tracking installer downloads)
CREATE TABLE IF NOT EXISTS downloads (
    download_id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    ip INET,
    user_agent TEXT,
    referrer TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_downloads_platform ON downloads(platform);
CREATE INDEX IF NOT EXISTS idx_downloads_timestamp ON downloads(timestamp);
CREATE INDEX IF NOT EXISTS idx_downloads_platform_timestamp ON downloads(platform, timestamp);

-- API keys table (optional, for future use)
CREATE TABLE IF NOT EXISTS api_keys (
    key_id VARCHAR(255) PRIMARY KEY,
    key_hash VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- Create views for common analytics queries
CREATE OR REPLACE VIEW daily_stats AS
SELECT
    DATE(timestamp) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_queries,
    SUM(tokens_used) as total_tokens,
    SUM(cost) as total_cost,
    AVG(tokens_used) as avg_tokens_per_query
FROM queries
GROUP BY DATE(timestamp)
ORDER BY date DESC;

CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.user_id,
    u.email,
    u.created_at,
    u.last_login,
    COUNT(q.query_id) as total_queries,
    SUM(q.tokens_used) as total_tokens_used,
    SUM(q.cost) as total_cost,
    MAX(q.timestamp) as last_query_time
FROM users u
LEFT JOIN queries q ON u.user_id = q.user_id
GROUP BY u.user_id, u.email, u.created_at, u.last_login
ORDER BY total_queries DESC;

-- Function to reset daily token counters
CREATE OR REPLACE FUNCTION reset_daily_tokens()
RETURNS INTEGER AS $$
DECLARE
    rows_updated INTEGER;
BEGIN
    UPDATE users
    SET tokens_used_today = 0,
        last_token_reset = CURRENT_DATE
    WHERE last_token_reset < CURRENT_DATE;
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RETURN rows_updated;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to reset tokens daily (requires pg_cron extension)
-- If pg_cron is not available, this will be handled in application code
-- SELECT cron.schedule('reset-daily-tokens', '0 0 * * *', 'SELECT reset_daily_tokens()');

COMMIT;

