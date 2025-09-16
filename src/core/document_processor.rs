use crate::{Document, ProcessedDocument, Result, TextChunk};
use pdf_extract;
use redis::AsyncCommands;
use std::sync::Arc;
use tokio;
use tracing::{info, error, instrument};

pub struct DocumentProcessor {
    redis_client: Arc<redis::Client>,
}

impl DocumentProcessor {
    pub fn new(redis_url: &str) -> Result<Self> {
        info!("Initializing DocumentProcessor with Redis URL: {}", redis_url);
        let client = redis::Client::open(redis_url)?;
        Ok(Self {
            redis_client: Arc::new(client),
        })
    }

    #[instrument(skip(self, document))]
    pub async fn process_document(&self, document: Document) -> Result<ProcessedDocument> {
        info!("Processing document: {}", document.id);
        
        // Extract text from PDF
        let text = match document.metadata.content_type.as_str() {
            "application/pdf" => {
                info!("Extracting text from PDF document");
                self.extract_pdf_text(&document.content)?
            },
            _ => {
                info!("Converting document to text");
                String::from_utf8(document.content.clone())?
            },
        };

        info!("Creating text chunks");
        let chunks = self.create_chunks(&text);
        info!("Created {} chunks", chunks.len());

        // Create processed document
        let processed = ProcessedDocument {
            doc_id: document.id.clone(),
            text_content: text,
            chunks,
            metadata: document.metadata,
        };

        info!("Queueing document for LLM processing");
        self.queue_for_processing(&processed).await?;
        info!("Document successfully queued");

        Ok(processed)
    }

    #[instrument(skip(self, content))]
    fn extract_pdf_text(&self, content: &[u8]) -> Result<String> {
        info!("Starting PDF text extraction");
        match pdf_extract::extract_text_from_mem(content) {
            Ok(text) => {
                info!("Successfully extracted text from PDF");
                Ok(text)
            },
            Err(e) => {
                error!("PDF extraction failed: {}", e);
                Err(Box::new(e))
            }
        }
    }

    fn create_chunks(&self, text: &str) -> Vec<TextChunk> {
        info!("Splitting text into chunks");
        let chunks: Vec<TextChunk> = text.split('\n')
            .enumerate()
            .map(|(i, content)| TextChunk {
                content: content.to_string(),
                index: i,
            })
            .collect();
        info!("Created {} text chunks", chunks.len());
        chunks
    }

    #[instrument(skip(self, doc))]
    async fn queue_for_processing(&self, doc: &ProcessedDocument) -> Result<()> {
        info!("Connecting to Redis");
        let mut conn = self.redis_client.get_async_connection().await?;
        
        info!("Serializing document for queue");
        let serialized = serde_json::to_string(&doc)?;
        
        info!("Adding document to processing queue");
        conn.lpush("processing_queue", serialized).await?;
        info!("Document successfully queued");
        
        Ok(())
    }
}