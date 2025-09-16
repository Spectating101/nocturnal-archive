use crate::error::{ProcessingError, Result};
use serde::{Deserialize, Serialize};
use tokio;
use std::sync::Arc;
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use tracing::{info, error, instrument};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct ResearchSession {
    pub id: String,
    pub topic: String,
    pub status: ResearchStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub papers_found: i32,
    pub papers_processed: i32,
    pub completion_percentage: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum ResearchStatus {
    Initializing,
    SearchingPapers,
    ProcessingDocuments,
    BuildingKnowledge,
    Completed,
    Error,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ResearchProgress {
    pub papers_total: i32,
    pub papers_processed: i32,
    pub papers_failed: i32,
    pub current_phase: String,
    pub last_processed: Option<String>,
}

pub struct ResearchManager {
    redis_client: Arc<redis::Client>,
    active_sessions: HashMap<String, ResearchSession>,
}

impl ResearchManager {
    pub fn new(redis_url: &str) -> Result<Self> {
        info!("Initializing ResearchManager");
        let client = redis::Client::open(redis_url)?;
        Ok(Self {
            redis_client: Arc::new(client),
            active_sessions: HashMap::new(),
        })
    }

    #[instrument(skip(self, topic))]
    pub async fn start_research(&mut self, topic: String) -> Result<String> {
        info!("Starting new research session for topic: {}", topic);
        
        let session_id = Uuid::new_v4().to_string();
        let session = ResearchSession {
            id: session_id.clone(),
            topic,
            status: ResearchStatus::Initializing,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            papers_found: 0,
            papers_processed: 0,
            completion_percentage: 0.0,
        };
        
        self.active_sessions.insert(session_id.clone(), session);
        self.queue_research_task(&session_id).await?;
        
        info!("Research session started: {}", session_id);
        Ok(session_id)
    }

    #[instrument(skip(self))]
    pub async fn get_research_status(&self, session_id: &str) -> Result<ResearchProgress> {
        info!("Checking status for session: {}", session_id);
        
        let mut conn = self.redis_client.get_async_connection().await?;
        let progress: String = conn.get(format!("research:{}:progress", session_id)).await?;
        
        serde_json::from_str(&progress)
            .map_err(|e| ProcessingError::System(format!("Failed to parse progress: {}", e)))
    }

    #[instrument(skip(self, session_id))]
    async fn queue_research_task(&self, session_id: &str) -> Result<()> {
        info!("Queueing research task for session: {}", session_id);
        
        let mut conn = self.redis_client.get_async_connection().await?;
        
        // Add to processing queue
        conn.lpush(
            "research_queue",
            serde_json::to_string(&self.active_sessions.get(session_id).unwrap())?
        ).await?;
        
        Ok(())
    }

    #[instrument(skip(self))]
    pub async fn process_research_queue(&self) -> Result<()> {
        info!("Starting research queue processing");
        
        let mut conn = self.redis_client.get_async_connection().await?;
        
        while let Some(session_data) = conn.rpop::<_, Option<String>>("research_queue").await? {
            let session: ResearchSession = serde_json::from_str(&session_data)?;
            
            match self.process_research_session(&session).await {
                Ok(_) => {
                    info!("Successfully processed research session: {}", session.id);
                    self.update_session_status(&session.id, ResearchStatus::Completed).await?;
                },
                Err(e) => {
                    error!("Failed to process research session {}: {}", session.id, e);
                    self.update_session_status(&session.id, ResearchStatus::Error).await?;
                }
            }
        }
        
        Ok(())
    }

    #[instrument(skip(self, session))]
    async fn process_research_session(&self, session: &ResearchSession) -> Result<()> {
        info!("Processing research session: {}", session.id);
        
        // Update status to searching
        self.update_session_status(&session.id, ResearchStatus::SearchingPapers).await?;
        
        // Process phases
        self.search_papers(session).await?;
        self.process_documents(session).await?;
        self.build_knowledge_base(session).await?;
        
        Ok(())
    }

    async fn search_papers(&self, session: &ResearchSession) -> Result<()> {
        info!("Searching papers for session: {}", session.id);
        // This will be implemented to interface with paper service
        Ok(())
    }

    async fn process_documents(&self, session: &ResearchSession) -> Result<()> {
        info!("Processing documents for session: {}", session.id);
        // This will be implemented to handle document processing
        Ok(())
    }

    async fn build_knowledge_base(&self, session: &ResearchSession) -> Result<()> {
        info!("Building knowledge base for session: {}", session.id);
        // This will be implemented to create research synthesis
        Ok(())
    }

    #[instrument(skip(self))]
    async fn update_session_status(&self, session_id: &str, status: ResearchStatus) -> Result<()> {
        info!("Updating session {} status to {:?}", session_id, status);
        
        let mut conn = self.redis_client.get_async_connection().await?;
        
        // Update status in Redis
        conn.set(
            format!("research:{}:status", session_id),
            serde_json::to_string(&status)?
        ).await?;
        
        Ok(())
    }

    #[instrument(skip(self))]
    pub async fn cleanup_old_sessions(&self, age_hours: i64) -> Result<i32> {
        info!("Cleaning up old research sessions");
        
        let mut conn = self.redis_client.get_async_connection().await?;
        let mut cleaned = 0;
        
        // Implement cleanup logic
        
        Ok(cleaned)
    }
}