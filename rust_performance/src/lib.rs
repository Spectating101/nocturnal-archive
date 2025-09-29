use pyo3::prelude::*;
use pyo3_asyncio::tokio::future_into_py;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapedContent {
    pub url: String,
    pub title: String,
    pub content: String,
    pub metadata: HashMap<String, String>,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessedText {
    pub original: String,
    pub cleaned: String,
    pub chunks: Vec<String>,
    pub keywords: Vec<String>,
    pub summary: String,
}

#[pyclass]
pub struct HighPerformanceScraper {
    max_concurrent: usize,
}

#[pymethods]
impl HighPerformanceScraper {
    #[new]
    fn new(max_concurrent: usize) -> Self {
        Self { max_concurrent }
    }

    fn scrape_urls(&self, py: Python, urls: Vec<String>) -> PyResult<PyObject> {
        future_into_py(py, async move {
            let mut results = Vec::new();
            
            for url in urls {
                match self.scrape_single_url(&url).await {
                    Ok(content) => results.push(content),
                    Err(e) => eprintln!("Failed to scrape {}: {}", url, e),
                }
            }
            
            Ok(results)
        })
    }

    fn process_text_batch(&self, py: Python, texts: Vec<String>) -> PyResult<PyObject> {
        future_into_py(py, async move {
            let mut results = Vec::new();
            
            for text in texts {
                let processed = self.process_single_text(&text).await;
                results.push(processed);
            }
            
            Ok(results)
        })
    }

    fn extract_keywords(&self, py: Python, text: String, max_keywords: usize) -> PyResult<PyObject> {
        future_into_py(py, async move {
            let keywords = self.extract_keywords_impl(&text, max_keywords).await;
            Ok(keywords)
        })
    }

    fn chunk_text(&self, py: Python, text: String, chunk_size: usize, overlap: usize) -> PyResult<PyObject> {
        future_into_py(py, async move {
            let chunks = self.chunk_text_impl(&text, chunk_size, overlap).await;
            Ok(chunks)
        })
    }
}

impl HighPerformanceScraper {
    async fn scrape_single_url(&self, url: &str) -> Result<ScrapedContent, Box<dyn std::error::Error>> {
        let client = reqwest::Client::new();
        let response = client.get(url).send().await?;
        let html = response.text().await?;
        
        // Simple HTML parsing - extract title and content
        let title = self.extract_title(&html);
        let content = self.extract_content(&html);
        
        let mut metadata = HashMap::new();
        metadata.insert("content_type".to_string(), "text/html".to_string());
        metadata.insert("url".to_string(), url.to_string());
        
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        Ok(ScrapedContent {
            url: url.to_string(),
            title,
            content,
            metadata,
            timestamp: timestamp.to_string(),
        })
    }

    fn extract_title(&self, html: &str) -> String {
        if let Some(start) = html.find("<title>") {
            if let Some(end) = html[start + 7..].find("</title>") {
                return html[start + 7..start + 7 + end].to_string();
            }
        }
        "No title".to_string()
    }

    fn extract_content(&self, html: &str) -> String {
        // Simple content extraction - remove HTML tags
        let mut content = html.to_string();
        
        // Remove script and style tags
        content = regex::Regex::new(r"<script[^>]*>.*?</script>").unwrap().replace_all(&content, "").to_string();
        content = regex::Regex::new(r"<style[^>]*>.*?</style>").unwrap().replace_all(&content, "").to_string();
        
        // Remove HTML tags
        content = regex::Regex::new(r"<[^>]+>").unwrap().replace_all(&content, " ").to_string();
        
        // Clean up whitespace
        content = regex::Regex::new(r"\s+").unwrap().replace_all(&content, " ").to_string();
        
        content.trim().to_string()
    }

    async fn process_single_text(&self, text: &str) -> ProcessedText {
        let cleaned = self.clean_text(text);
        let chunks = self.chunk_text_impl(&cleaned, 1000, 200).await;
        let keywords = self.extract_keywords_impl(&cleaned, 10).await;
        let summary = self.generate_summary(&cleaned);
        
        ProcessedText {
            original: text.to_string(),
            cleaned,
            chunks,
            keywords,
            summary,
        }
    }

    fn clean_text(&self, text: &str) -> String {
        let mut cleaned = text.to_string();
        
        // Remove extra whitespace
        cleaned = regex::Regex::new(r"\s+").unwrap().replace_all(&cleaned, " ").to_string();
        
        // Remove special characters but keep basic punctuation
        cleaned = regex::Regex::new(r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]").unwrap().replace_all(&cleaned, "").to_string();
        
        // Normalize quotes and dashes
        cleaned = cleaned
            .replace(""", "\"")
            .replace(""", "\"")
            .replace("'", "'")
            .replace("'", "'")
            .replace("–", "-")
            .replace("—", "-");
        
        cleaned.trim().to_string()
    }

    async fn chunk_text_impl(&self, text: &str, chunk_size: usize, overlap: usize) -> Vec<String> {
        let sentences: Vec<&str> = regex::Regex::new(r"[.!?]+").unwrap()
            .split(text)
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .collect();
        
        let mut chunks = Vec::new();
        let mut current_chunk = String::new();
        let mut current_size = 0;
        
        for sentence in sentences {
            let sentence_size = sentence.len();
            
            if current_size + sentence_size > chunk_size && !current_chunk.is_empty() {
                chunks.push(current_chunk.trim().to_string());
                
                // Start new chunk with overlap
                if overlap > 0 {
                    let words: Vec<&str> = current_chunk.split_whitespace().collect();
                    let overlap_words = (overlap / 10).min(words.len());
                    if overlap_words > 0 {
                        current_chunk = words[words.len() - overlap_words..].join(" ") + " ";
                        current_size = current_chunk.len();
                    } else {
                        current_chunk = String::new();
                        current_size = 0;
                    }
                } else {
                    current_chunk = String::new();
                    current_size = 0;
                }
            }
            
            current_chunk.push_str(sentence);
            current_chunk.push_str(". ");
            current_size += sentence_size + 2;
        }
        
        if !current_chunk.trim().is_empty() {
            chunks.push(current_chunk.trim().to_string());
        }
        
        chunks
    }

    async fn extract_keywords_impl(&self, text: &str, max_keywords: usize) -> Vec<String> {
        let stop_words = [
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might", "must",
            "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
        ];
        
        let words: Vec<&str> = regex::Regex::new(r"\b[a-zA-Z]+\b").unwrap()
            .find_iter(text)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| word.len() > 2 && !stop_words.contains(&word.as_str()))
            .collect();
        
        let mut word_count: HashMap<String, usize> = HashMap::new();
        for word in words {
            *word_count.entry(word).or_insert(0) += 1;
        }
        
        let mut word_freq: Vec<(String, usize)> = word_count.into_iter().collect();
        word_freq.sort_by(|a, b| b.1.cmp(&a.1));
        
        word_freq.into_iter()
            .take(max_keywords)
            .map(|(word, _)| word)
            .collect()
    }

    fn generate_summary(&self, text: &str) -> String {
        let sentences: Vec<&str> = regex::Regex::new(r"[.!?]+").unwrap()
            .split(text)
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .collect();
        
        if sentences.len() <= 3 {
            return text.to_string();
        }
        
        // Simple extractive summarization - take first few sentences
        let summary_sentences = sentences.into_iter().take(3).collect::<Vec<&str>>();
        summary_sentences.join(". ") + "."
    }
}

#[pymodule]
fn nocturnal_performance(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<HighPerformanceScraper>()?;
    Ok(())
}