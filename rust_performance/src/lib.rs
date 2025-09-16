use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3_asyncio::tokio::future_into_py;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Semaphore;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use url::Url;

mod scraper;
mod processor;
mod cache;

use scraper::WebScraper;
use processor::TextProcessor;
use cache::ResponseCache;

#[derive(Debug, Serialize, Deserialize)]
pub struct ScrapedContent {
    pub url: String,
    pub title: String,
    pub content: String,
    pub metadata: HashMap<String, String>,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessedText {
    pub original: String,
    pub cleaned: String,
    pub chunks: Vec<String>,
    pub keywords: Vec<String>,
    pub summary: String,
}

#[pyclass]
pub struct HighPerformanceScraper {
    scraper: Arc<WebScraper>,
    processor: Arc<TextProcessor>,
    cache: Arc<ResponseCache>,
    semaphore: Arc<Semaphore>,
}

#[pymethods]
impl HighPerformanceScraper {
    #[new]
    fn new(max_concurrent: Option<usize>) -> PyResult<Self> {
        let max_concurrent = max_concurrent.unwrap_or(10);
        Ok(Self {
            scraper: Arc::new(WebScraper::new()),
            processor: Arc::new(TextProcessor::new()),
            cache: Arc::new(ResponseCache::new()),
            semaphore: Arc::new(Semaphore::new(max_concurrent)),
        })
    }

    #[pyo3(name = "scrape_urls")]
    fn scrape_urls_py<'py>(
        &self,
        py: Python<'py>,
        urls: Vec<String>,
    ) -> PyResult<PyObject> {
        let scraper = self.scraper.clone();
        let processor = self.processor.clone();
        let cache = self.cache.clone();
        let semaphore = self.semaphore.clone();

        future_into_py(py, async move {
            let mut results = Vec::new();
            let mut futures = Vec::new();

            for url in urls {
                let scraper = scraper.clone();
                let processor = processor.clone();
                let cache = cache.clone();
                let semaphore = semaphore.clone();

                let future = async move {
                    let _permit = semaphore.acquire().await.unwrap();
                    
                    // Check cache first
                    if let Some(cached) = cache.get(&url).await {
                        return Ok(cached);
                    }

                    // Scrape and process
                    let scraped = scraper.scrape_url(&url).await?;
                    let processed = processor.process_text(&scraped.content).await?;
                    
                    let result = ScrapedContent {
                        url: scraped.url,
                        title: scraped.title,
                        content: processed.cleaned,
                        metadata: scraped.metadata,
                        timestamp: chrono::Utc::now(),
                    };

                    // Cache the result
                    cache.set(&url, &result).await;
                    
                    Ok(result)
                };

                futures.push(future);
            }

            // Wait for all futures to complete
            let results = futures::future::join_all(futures).await;
            
            // Filter out errors and collect successful results
            let mut successful_results = Vec::new();
            for result in results {
                match result {
                    Ok(content) => successful_results.push(content),
                    Err(e) => eprintln!("Error scraping URL: {}", e),
                }
            }

            Ok(successful_results)
        })
    }

    #[pyo3(name = "process_text_batch")]
    fn process_text_batch_py<'py>(
        &self,
        py: Python<'py>,
        texts: Vec<String>,
    ) -> PyResult<PyObject> {
        let processor = self.processor.clone();

        future_into_py(py, async move {
            let mut results = Vec::new();
            
            // Process texts in parallel using rayon
            let processed: Vec<ProcessedText> = texts
                .into_par_iter()
                .map(|text| {
                    // Note: This is a simplified version. In practice, you'd want to handle async properly
                    // For now, we'll process synchronously but in parallel
                    processor.process_text_sync(&text)
                })
                .collect();

            Ok(processed)
        })
    }

    #[pyo3(name = "extract_keywords")]
    fn extract_keywords_py<'py>(
        &self,
        py: Python<'py>,
        text: String,
        max_keywords: Option<usize>,
    ) -> PyResult<PyObject> {
        let processor = self.processor.clone();
        let max_keywords = max_keywords.unwrap_or(10);

        future_into_py(py, async move {
            let keywords = processor.extract_keywords(&text, max_keywords).await?;
            Ok(keywords)
        })
    }

    #[pyo3(name = "chunk_text")]
    fn chunk_text_py<'py>(
        &self,
        py: Python<'py>,
        text: String,
        chunk_size: Option<usize>,
        overlap: Option<usize>,
    ) -> PyResult<PyObject> {
        let processor = self.processor.clone();
        let chunk_size = chunk_size.unwrap_or(1000);
        let overlap = overlap.unwrap_or(200);

        future_into_py(py, async move {
            let chunks = processor.chunk_text(&text, chunk_size, overlap).await?;
            Ok(chunks)
        })
    }
}

#[pyfunction]
fn fast_text_clean(text: &str) -> PyResult<String> {
    let processor = TextProcessor::new();
    Ok(processor.clean_text_sync(text))
}

#[pyfunction]
fn fast_url_validation(url: &str) -> PyResult<bool> {
    match Url::parse(url) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

#[pyfunction]
fn fast_text_similarity(text1: &str, text2: &str) -> PyResult<f64> {
    let processor = TextProcessor::new();
    Ok(processor.calculate_similarity_sync(text1, text2))
}

#[pymodule]
fn nocturnal_performance(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<HighPerformanceScraper>()?;
    m.add_function(wrap_pyfunction!(fast_text_clean, m)?)?;
    m.add_function(wrap_pyfunction!(fast_url_validation, m)?)?;
    m.add_function(wrap_pyfunction!(fast_text_similarity, m)?)?;
    Ok(())
}
