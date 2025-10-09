-- Accuracy Tracking Schema
-- Tracks citation quality and response accuracy metrics

-- Response quality table
CREATE TABLE IF NOT EXISTS response_quality (
    response_id VARCHAR(255) PRIMARY KEY,
    query_id VARCHAR(255) REFERENCES queries(query_id) ON DELETE CASCADE,
    
    -- Citation metrics
    has_citations BOOLEAN NOT NULL,
    total_citations INTEGER DEFAULT 0,
    verified_citations INTEGER DEFAULT 0,
    broken_citations INTEGER DEFAULT 0,
    citation_quality_score FLOAT,  -- 0-1
    
    -- Response metrics
    word_count INTEGER,
    confidence_score FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_quality_query_id (query_id),
    INDEX idx_quality_timestamp (created_at),
    INDEX idx_quality_score (citation_quality_score)
);

-- Citation details table (for debugging)
CREATE TABLE IF NOT EXISTS citation_details (
    id SERIAL PRIMARY KEY,
    response_id VARCHAR(255) REFERENCES response_quality(response_id) ON DELETE CASCADE,
    
    citation_type VARCHAR(50),  -- 'url', 'doi', 'arxiv', 'author_year'
    citation_text TEXT,
    verification_status VARCHAR(50),  -- 'verified', 'broken', 'timeout', 'error'
    http_status_code INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_citation_response (response_id),
    INDEX idx_citation_status (verification_status)
);

-- Accuracy metrics view (for analytics dashboard)
CREATE OR REPLACE VIEW accuracy_metrics AS
SELECT
    DATE(created_at) as date,
    
    -- Citation metrics
    AVG(CASE WHEN has_citations THEN 1.0 ELSE 0.0 END) as citation_rate,
    AVG(total_citations) as avg_citations_per_response,
    AVG(citation_quality_score) as avg_quality_score,
    
    -- Unsupported Claim Rate (UCR)
    -- = responses without citations / total responses
    SUM(CASE WHEN NOT has_citations THEN 1 ELSE 0 END)::float / COUNT(*) as unsupported_claim_rate,
    
    -- False Citation Rate (FCR)  
    -- = broken citations / total citations
    SUM(broken_citations)::float / NULLIF(SUM(total_citations), 0) as false_citation_rate,
    
    -- Counts
    COUNT(*) as total_responses,
    SUM(CASE WHEN has_citations THEN 1 ELSE 0 END) as responses_with_citations,
    SUM(total_citations) as total_citations_count,
    SUM(verified_citations) as verified_citations_count,
    SUM(broken_citations) as broken_citations_count
    
FROM response_quality
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Weekly accuracy summary
CREATE OR REPLACE VIEW accuracy_weekly AS
SELECT
    DATE_TRUNC('week', created_at) as week_start,
    
    AVG(citation_quality_score) as avg_quality_score,
    SUM(CASE WHEN NOT has_citations THEN 1 ELSE 0 END)::float / COUNT(*) as unsupported_claim_rate,
    SUM(broken_citations)::float / NULLIF(SUM(total_citations), 0) as false_citation_rate,
    
    COUNT(*) as total_responses,
    AVG(total_citations) as avg_citations
    
FROM response_quality
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week_start DESC;

-- User accuracy leaderboard (for A/B testing)
CREATE OR REPLACE VIEW user_accuracy AS
SELECT
    q.user_id,
    u.email,
    
    COUNT(DISTINCT rq.response_id) as total_responses,
    AVG(rq.citation_quality_score) as avg_quality_score,
    SUM(CASE WHEN rq.has_citations THEN 1 ELSE 0 END)::float / COUNT(*) as citation_rate,
    AVG(rq.total_citations) as avg_citations,
    
    -- Quality tier
    CASE
        WHEN AVG(rq.citation_quality_score) >= 0.9 THEN 'excellent'
        WHEN AVG(rq.citation_quality_score) >= 0.7 THEN 'good'
        WHEN AVG(rq.citation_quality_score) >= 0.5 THEN 'fair'
        ELSE 'poor'
    END as quality_tier
    
FROM queries q
LEFT JOIN response_quality rq ON q.query_id = rq.query_id
LEFT JOIN users u ON q.user_id = u.user_id
WHERE rq.response_id IS NOT NULL
GROUP BY q.user_id, u.email
ORDER BY avg_quality_score DESC;

-- Function to calculate overall accuracy stats
CREATE OR REPLACE FUNCTION get_accuracy_stats(
    days_back INTEGER DEFAULT 7
)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'unsupported_claim_rate', 
        COALESCE(
            SUM(CASE WHEN NOT has_citations THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0),
            0
        ),
        
        'false_citation_rate',
        COALESCE(
            SUM(broken_citations)::float / NULLIF(SUM(total_citations), 0),
            0
        ),
        
        'avg_quality_score',
        COALESCE(AVG(citation_quality_score), 0),
        
        'citation_rate',
        COALESCE(
            SUM(CASE WHEN has_citations THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0),
            0
        ),
        
        'total_responses', COUNT(*),
        'total_citations', COALESCE(SUM(total_citations), 0),
        'verified_citations', COALESCE(SUM(verified_citations), 0),
        'broken_citations', COALESCE(SUM(broken_citations), 0),
        
        'period_days', days_back,
        'calculated_at', NOW()
    )
    INTO result
    FROM response_quality
    WHERE created_at > NOW() - (days_back || ' days')::INTERVAL;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMIT;

