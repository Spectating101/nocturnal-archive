use crate::error::{ProcessingError, Result};
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{info, error, instrument};

#[derive(Debug, Serialize, Deserialize)]
pub struct QueueItem {
    pub id: String,
    pub priority: i32,
    pub retry_count: i32,
    pub payload: serde_json::Value,
}

pub struct QueueHandler {
    redis: Arc<redis::Client>,
    processing_queue: String,
    retry_queue: String,
    max_retries: i32,
}

impl QueueHandler {
    pub fn new(
        redis_client: redis::Client,
        processing_queue: String,
        retry_queue: String,
        max_retries: i32,
    ) -> Self {
        Self {
            redis: Arc::new(redis_client),
            processing_queue,
            retry_queue,
            max_retries,
        }
    }

    #[instrument(skip(self, item))]
    pub async fn enqueue(&self, item: QueueItem) -> Result<()> {
        info!("Enqueueing item: {}", item.id);
        let mut conn = self.redis.get_async_connection().await?;
        
        let serialized = serde_json::to_string(&item)?;
        conn.lpush(&self.processing_queue, serialized).await?;
        
        info!("Successfully enqueued item: {}", item.id);
        Ok(())
    }

    #[instrument(skip(self))]
    pub async fn dequeue(&self) -> Result<Option<QueueItem>> {
        let mut conn = self.redis.get_async_connection().await?;
        
        if let Some(data) = conn.rpop::<_, Option<String>>(&self.processing_queue).await? {
            info!("Dequeued item from processing queue");
            let item: QueueItem = serde_json::from_str(&data)?;
            Ok(Some(item))
        } else {
            Ok(None)
        }
    }

    #[instrument(skip(self, item))]
    pub async fn retry(&self, mut item: QueueItem) -> Result<()> {
        item.retry_count += 1;
        
        if item.retry_count >= self.max_retries {
            error!("Item {} exceeded max retries", item.id);
            self.move_to_dead_letter(&item).await?;
            return Ok(());
        }
        
        info!("Retrying item: {} (attempt {})", item.id, item.retry_count);
        let mut conn = self.redis.get_async_connection().await?;
        
        let serialized = serde_json::to_string(&item)?;
        conn.lpush(&self.retry_queue, serialized).await?;
        
        Ok(())
    }

    #[instrument(skip(self, item))]
    async fn move_to_dead_letter(&self, item: &QueueItem) -> Result<()> {
        info!("Moving item {} to dead letter queue", item.id);
        let mut conn = self.redis.get_async_connection().await?;
        
        let serialized = serde_json::to_string(&item)?;
        conn.lpush("dead_letter_queue", serialized).await?;
        
        Ok(())
    }

    #[instrument(skip(self))]
    pub async fn process_retries(&self) -> Result<()> {
        let mut conn = self.redis.get_async_connection().await?;
        
        while let Some(data) = conn.rpop::<_, Option<String>>(&self.retry_queue).await? {
            info!("Processing retry item");
            let item: QueueItem = serde_json::from_str(&data)?;
            
            // Move back to main queue with increased priority
            let mut item = item;
            item.priority += 1;
            self.enqueue(item).await?;
        }
        
        Ok(())
    }

    #[instrument(skip(self))]
    pub async fn get_queue_length(&self) -> Result<(i64, i64)> {
        let mut conn = self.redis.get_async_connection().await?;
        
        let processing: i64 = conn.llen(&self.processing_queue).await?;
        let retry: i64 = conn.llen(&self.retry_queue).await?;
        
        Ok((processing, retry))
    }
}