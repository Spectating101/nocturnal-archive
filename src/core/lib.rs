use serde::{Deserialize, Serialize};
pub use std::error::Error;

#[derive(Debug, Serialize, Deserialize)]
pub struct Document {
    pub id: String,
    pub content: Vec<u8>,
    pub metadata: DocumentMetadata,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DocumentMetadata {
    pub filename: String,
    pub content_type: String,
    pub size: usize,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessedDocument {
    pub doc_id: String,
    pub text_content: String,
    pub chunks: Vec<TextChunk>,
    pub metadata: DocumentMetadata,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TextChunk {
    pub content: String,
    pub index: usize,
}

pub type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;