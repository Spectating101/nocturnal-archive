# FinSight RAG System Makefile

.PHONY: help setup-db start-db stop-db init-db index-apple test-rag clean-db

help: ## Show this help message
	@echo "FinSight RAG System Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup-db: ## Start PostgreSQL with PGVector and initialize database
	@echo "🚀 Starting PostgreSQL with PGVector..."
	docker compose up -d pg
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "🔧 Initializing database..."
	@docker exec -i $$(docker compose ps -q pg) psql -U postgres -d finsight < init_rag_db.sql
	@echo "✅ Database setup complete!"

start-db: ## Start PostgreSQL container
	@echo "🚀 Starting PostgreSQL..."
	docker compose up -d pg

stop-db: ## Stop PostgreSQL container
	@echo "🛑 Stopping PostgreSQL..."
	docker compose down

init-db: ## Initialize database schema (requires running container)
	@echo "🔧 Initializing database schema..."
	@docker exec -i $$(docker compose ps -q pg) psql -U postgres -d finsight < init_rag_db.sql
	@echo "✅ Database initialized!"

index-apple: ## Index Apple filings into RAG database
	@echo "📊 Indexing Apple filings..."
	@source venv/bin/activate && python -m src.jobs.index_filings AAPL 1
	@echo "✅ Apple filings indexed!"

test-rag: ## Test RAG system with sample query
	@echo "🧪 Testing RAG system..."
	@source venv/bin/activate && python -c "from src.rag.index import get_doc_stats; stats = get_doc_stats(); print(f'📈 Database stats: {stats[\"total_documents\"]} documents'); print('✅ RAG system ready!' if stats['total_documents'] > 0 else '⚠️ No documents found')"

test-qa: ## Test Q&A endpoint (requires running server)
	@echo "🧪 Testing Q&A endpoint..."
	@curl -s -X POST "http://localhost:8000/v1/qa/filings" \
		-H "Content-Type: application/json" \
		-H "X-API-Key: demo-key-123" \
		-d '{"query":"What did Apple say about margins?", "tickers":["AAPL"], "k":3}' | jq

clean-db: ## Clear all documents from RAG database
	@echo "🧹 Clearing RAG database..."
	@source venv/bin/activate && python -c "from src.rag.index import clear_docs; deleted = clear_docs(); print(f'🗑️ Deleted {deleted} documents')"

status: ## Show system status
	@echo "📊 FinSight RAG System Status:"
	@echo ""
	@echo "🗄️ Database:"
	@docker compose ps pg
	@echo ""
	@echo "📈 RAG Stats:"
	@source venv/bin/activate && python -c "from src.rag.index import get_doc_stats; stats = get_doc_stats(); print(f'  Documents: {stats[\"total_documents\"]}'); print(f'  Tickers: {len(stats[\"ticker_counts\"])}')"

demo: setup-db index-apple ## Complete demo setup (database + Apple data)
	@echo ""
	@echo "🎉 Demo setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Start the server: uvicorn src.main:app --host 0.0.0.0 --port 8000"
	@echo "2. Test Q&A: make test-qa"
	@echo "3. Optimize indexes: make optimize-indexes"

optimize-indexes: ## Optimize vector indexes after bulk inserts
	@echo "🔧 Optimizing vector indexes..."
	@docker exec -i $$(docker compose ps -q pg) psql -U postgres -d finsight -c "SELECT optimize_rag_indexes();"
	@echo "✅ Indexes optimized!"

test-production: ## Test production-ready features
	@echo "🧪 Testing production features..."
	@source venv/bin/activate && python -c "
from src.rag.qa import answer
from src.rag.index import get_doc_stats
print('Testing MMR reranking and extractive answers...')
stats = get_doc_stats()
print(f'Database: {stats[\"total_documents\"]} documents')
print('✅ Production features ready!')
"