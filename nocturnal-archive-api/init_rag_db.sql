-- Initialize RAG database with PGVector
-- Run with: sudo -u postgres psql -d finsight -f init_rag_db.sql

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table with vector embeddings
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    date DATE NOT NULL,
    ticker TEXT NOT NULL,
    cik TEXT NOT NULL,
    section TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384),  -- sentence-transformers/all-MiniLM-L6-v2 dimension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for ticker filtering
CREATE INDEX IF NOT EXISTS documents_ticker_idx ON documents(ticker);

-- Create index for date filtering
CREATE INDEX IF NOT EXISTS documents_date_idx ON documents(date);

-- Grant permissions to finsight_user
GRANT ALL PRIVILEGES ON TABLE documents TO finsight_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO finsight_user;

-- Insert some sample data for testing
INSERT INTO documents (id, title, url, date, ticker, cik, section, text, embedding) VALUES
(
    'DEMO:AAPL:Item7#c0',
    'Item 7 — MD&A',
    'https://sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-10k_20240928.htm',
    '2024-10-27',
    'AAPL',
    '0000320193',
    'MD&A',
    'Apple discussed gross margin pressure from FX headwinds and pricing dynamics. The company expects continued margin compression due to competitive pressures.',
    array_fill(0.1, ARRAY[384])::vector
),
(
    'DEMO:AAPL:Item1A#c0',
    'Item 1A — Risk Factors',
    'https://sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-10k_20240928.htm',
    '2024-10-27',
    'AAPL',
    '0000320193',
    'Risk Factors',
    'Foreign exchange rate fluctuations may adversely affect our results. We are exposed to foreign exchange risk related to our international operations.',
    array_fill(0.2, ARRAY[384])::vector
),
(
    'DEMO:MSFT:Item7#c0',
    'Item 7 — MD&A',
    'https://sec.gov/Archives/edgar/data/789019/000156459024012345/msft-10k_20240630.htm',
    '2024-07-30',
    'MSFT',
    '0000789019',
    'MD&A',
    'Microsoft reported strong revenue growth driven by Azure and Office 365. The company highlighted AI investments and cloud migration trends.',
    array_fill(0.3, ARRAY[384])::vector
)
ON CONFLICT (id) DO NOTHING;

-- Verify setup
SELECT 'PGVector extension installed' as status;
SELECT 'Documents table created' as status;
SELECT 'Sample data inserted' as status;
SELECT COUNT(*) as document_count FROM documents;