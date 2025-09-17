use std::fmt;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ProcessingError {
    #[error("Failed to process document: {0}")]
    DocumentProcessing(String),

    #[error("Failed to extract text: {0}")]
    TextExtraction(String),

    #[error("Database error: {0}")]
    Database(String),

    #[error("Queue error: {0}")]
    Queue(String),

    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("System error: {0}")]
    System(String),
}

impl fmt::Display for ProcessingError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self)
    }
}

impl From<redis::RedisError> for ProcessingError {
    fn from(err: redis::RedisError) -> Self {
        ProcessingError::Queue(err.to_string())
    }
}

impl From<mongodb::error::Error> for ProcessingError {
    fn from(err: mongodb::error::Error) -> Self {
        ProcessingError::Database(err.to_string())
    }
}

impl From<std::io::Error> for ProcessingError {
    fn from(err: std::io::Error) -> Self {
        ProcessingError::System(err.to_string())
    }
}

pub type Result<T> = std::result::Result<T, ProcessingError>;