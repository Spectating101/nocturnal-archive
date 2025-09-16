use nocturnal_archive::{Document, DocumentMetadata, ProcessingError};
use chrono::Utc;

#[tokio::test]
async fn test_document_creation() {
    let doc = Document {
        id: "test-123".to_string(),
        content: b"Test content".to_vec(),
        metadata: DocumentMetadata {
            filename: "test.txt".to_string(),
            content_type: "text/plain".to_string(),
            size: 11,
            created_at: Utc::now(),
        },
    };

    assert_eq!(doc.id, "test-123");
    assert_eq!(doc.content, b"Test content");
}

#[tokio::test]
async fn test_document_processor() {
    let redis_url = std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string());
    
    let processor = match DocumentProcessor::new(&redis_url) {
        Ok(p) => p,
        Err(e) => panic!("Failed to create processor: {}", e),
    };

    let doc = Document {
        id: "test-123".to_string(),
        content: b"Test content for processing".to_vec(),
        metadata: DocumentMetadata {
            filename: "test.txt".to_string(),
            content_type: "text/plain".to_string(),
            size: 23,
            created_at: Utc::now(),
        },
    };

    let result = processor.process_document(doc).await;
    assert!(result.is_ok());

    let processed = result.unwrap();
    assert_eq!(processed.doc_id, "test-123");
    assert!(processed.chunks.len() > 0);
}

#[tokio::test]
async fn test_error_handling() {
    let processor = DocumentProcessor::new("redis://invalid-host:6379").unwrap();
    
    let doc = Document {
        id: "test-error".to_string(),
        content: b"Test content".to_vec(),
        metadata: DocumentMetadata {
            filename: "test.txt".to_string(),
            content_type: "text/plain".to_string(),
            size: 11,
            created_at: Utc::now(),
        },
    };

    let result = processor.process_document(doc).await;
    assert!(result.is_err());
    
    match result {
        Err(ProcessingError::Queue(_)) => (),
        _ => panic!("Expected Queue error"),
    }
}

#[tokio::test]
async fn test_pdf_processing() {
    let processor = DocumentProcessor::new("redis://127.0.0.1:6379").unwrap();
    
    // Create a minimal PDF content
    let pdf_content = include_bytes!("../test_data/sample.pdf");
    
    let doc = Document {
        id: "test-pdf".to_string(),
        content: pdf_content.to_vec(),
        metadata: DocumentMetadata {
            filename: "test.pdf".to_string(),
            content_type: "application/pdf".to_string(),
            size: pdf_content.len(),
            created_at: Utc::now(),
        },
    };

    let result = processor.process_document(doc).await;
    assert!(result.is_ok());
    
    let processed = result.unwrap();
    assert!(!processed.text_content.is_empty());
    assert!(processed.chunks.len() > 0);
}

#[tokio::test]
async fn test_large_document_handling() {
    let processor = DocumentProcessor::new("redis://127.0.0.1:6379").unwrap();
    
    // Create a large document (1MB)
    let large_content = vec![b'a'; 1_000_000];
    
    let doc = Document {
        id: "test-large".to_string(),
        content: large_content,
        metadata: DocumentMetadata {
            filename: "large.txt".to_string(),
            content_type: "text/plain".to_string(),
            size: 1_000_000,
            created_at: Utc::now(),
        },
    };

    let result = processor.process_document(doc).await;
    assert!(result.is_ok());
    
    let processed = result.unwrap();
    assert!(processed.chunks.len() > 1); // Should be split into multiple chunks
}