-- Product Separation Migration
-- Adds support for Cite-Agent vs FinSight API key differentiation

-- Add product type and tier columns to API keys
ALTER TABLE api_keys
ADD COLUMN IF NOT EXISTS key_type VARCHAR(50) DEFAULT 'cite_agent',
ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'student';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_key_type ON api_keys(key_type);
CREATE INDEX IF NOT EXISTS idx_api_keys_tier ON api_keys(tier);

-- Update existing keys to have default values
UPDATE api_keys
SET key_type = 'cite_agent', tier = 'student'
WHERE key_type IS NULL OR tier IS NULL;

-- Create API usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    api_key_id VARCHAR(255) NOT NULL REFERENCES api_keys(key_id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER,
    status_code INTEGER DEFAULT 200
);

CREATE INDEX IF NOT EXISTS idx_api_usage_api_key_id ON api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_key_date ON api_usage(api_key_id, DATE(timestamp));

-- Create view for daily FinSight usage (for Cite-Agent rate limiting)
CREATE OR REPLACE VIEW daily_finsight_usage AS
SELECT
    api_key_id,
    DATE(timestamp) as usage_date,
    COUNT(*) as call_count
FROM api_usage
WHERE endpoint LIKE '/v1/finance%'
GROUP BY api_key_id, DATE(timestamp);

-- Create view for monthly usage (for FinSight API rate limiting)
CREATE OR REPLACE VIEW monthly_usage AS
SELECT
    api_key_id,
    EXTRACT(YEAR FROM timestamp) as year,
    EXTRACT(MONTH FROM timestamp) as month,
    COUNT(*) as call_count
FROM api_usage
GROUP BY api_key_id, EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp);

-- Add constraint to validate key_type values
ALTER TABLE api_keys
ADD CONSTRAINT check_key_type CHECK (
    key_type IN ('cite_agent', 'finsight', 'admin')
);

-- Add constraint to validate tier values
ALTER TABLE api_keys
ADD CONSTRAINT check_tier CHECK (
    tier IN ('student', 'cite_pro', 'free', 'starter', 'finsight_pro', 'enterprise', 'admin')
);

COMMIT;
