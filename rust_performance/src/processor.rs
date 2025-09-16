use anyhow::Result;
use rayon::prelude::*;
use regex::Regex;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct TextProcessor {
    stop_words: Arc<Vec<String>>,
    word_regex: Regex,
    sentence_regex: Regex,
}

impl TextProcessor {
    pub fn new() -> Self {
        let stop_words = vec![
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might", "must",
            "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
            "mine", "yours", "hers", "ours", "theirs", "what", "which", "who", "whom", "whose",
            "where", "when", "why", "how", "all", "any", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "now", "then", "here", "there", "when", "where", "why",
            "again", "ever", "far", "late", "never", "next", "once", "soon", "still", "well",
        ];

        Self {
            stop_words: Arc::new(stop_words),
            word_regex: Regex::new(r"\b[a-zA-Z]+\b").unwrap(),
            sentence_regex: Regex::new(r"[.!?]+").unwrap(),
        }
    }

    pub async fn process_text(&self, text: &str) -> Result<ProcessedText> {
        let cleaned = self.clean_text_sync(text);
        let chunks = self.chunk_text(&cleaned, 1000, 200).await?;
        let keywords = self.extract_keywords(&cleaned, 10).await?;
        let summary = self.generate_summary(&cleaned).await?;

        Ok(ProcessedText {
            original: text.to_string(),
            cleaned,
            chunks,
            keywords,
            summary,
        })
    }

    pub fn process_text_sync(&self, text: &str) -> ProcessedText {
        let cleaned = self.clean_text_sync(text);
        let chunks = self.chunk_text_sync(&cleaned, 1000, 200);
        let keywords = self.extract_keywords_sync(&cleaned, 10);
        let summary = self.generate_summary_sync(&cleaned);

        ProcessedText {
            original: text.to_string(),
            cleaned,
            chunks,
            keywords,
            summary,
        }
    }

    pub fn clean_text_sync(&self, text: &str) -> String {
        // Remove extra whitespace
        let re_whitespace = Regex::new(r"\s+").unwrap();
        let cleaned = re_whitespace.replace_all(text, " ");

        // Remove special characters but keep basic punctuation
        let re_special = Regex::new(r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]").unwrap();
        let cleaned = re_special.replace_all(&cleaned, "");

        // Normalize quotes and dashes
        let cleaned = cleaned
            .replace(""", "\"")
            .replace(""", "\"")
            .replace("'", "'")
            .replace("'", "'")
            .replace("–", "-")
            .replace("—", "-");

        cleaned.trim().to_string()
    }

    pub async fn chunk_text(&self, text: &str, chunk_size: usize, overlap: usize) -> Result<Vec<String>> {
        let sentences: Vec<&str> = self.sentence_regex
            .split(text)
            .filter(|s| !s.trim().is_empty())
            .collect();

        let mut chunks = Vec::new();
        let mut current_chunk = String::new();
        let mut current_size = 0;

        for sentence in sentences {
            let sentence = sentence.trim();
            if sentence.is_empty() {
                continue;
            }

            let sentence_size = sentence.len();
            
            if current_size + sentence_size > chunk_size && !current_chunk.is_empty() {
                chunks.push(current_chunk.trim().to_string());
                
                // Start new chunk with overlap
                if overlap > 0 {
                    let words: Vec<&str> = current_chunk.split_whitespace().collect();
                    let overlap_words = (overlap / 10).min(words.len()); // Rough estimate
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

        Ok(chunks)
    }

    pub fn chunk_text_sync(&self, text: &str, chunk_size: usize, overlap: usize) -> Vec<String> {
        // Synchronous version for use in parallel processing
        let sentences: Vec<&str> = self.sentence_regex
            .split(text)
            .filter(|s| !s.trim().is_empty())
            .collect();

        let mut chunks = Vec::new();
        let mut current_chunk = String::new();
        let mut current_size = 0;

        for sentence in sentences {
            let sentence = sentence.trim();
            if sentence.is_empty() {
                continue;
            }

            let sentence_size = sentence.len();
            
            if current_size + sentence_size > chunk_size && !current_chunk.is_empty() {
                chunks.push(current_chunk.trim().to_string());
                
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

    pub async fn extract_keywords(&self, text: &str, max_keywords: usize) -> Result<Vec<String>> {
        let words: Vec<String> = self.word_regex
            .find_iter(text)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| {
                word.len() > 2 && !self.stop_words.contains(word)
            })
            .collect();

        let mut word_freq: HashMap<String, usize> = HashMap::new();
        for word in words {
            *word_freq.entry(word).or_insert(0) += 1;
        }

        let mut sorted_words: Vec<(String, usize)> = word_freq.into_iter().collect();
        sorted_words.sort_by(|a, b| b.1.cmp(&a.1));

        Ok(sorted_words
            .into_iter()
            .take(max_keywords)
            .map(|(word, _)| word)
            .collect())
    }

    pub fn extract_keywords_sync(&self, text: &str, max_keywords: usize) -> Vec<String> {
        let words: Vec<String> = self.word_regex
            .find_iter(text)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| {
                word.len() > 2 && !self.stop_words.contains(word)
            })
            .collect();

        let mut word_freq: HashMap<String, usize> = HashMap::new();
        for word in words {
            *word_freq.entry(word).or_insert(0) += 1;
        }

        let mut sorted_words: Vec<(String, usize)> = word_freq.into_iter().collect();
        sorted_words.sort_by(|a, b| b.1.cmp(&a.1));

        sorted_words
            .into_iter()
            .take(max_keywords)
            .map(|(word, _)| word)
            .collect()
    }

    pub async fn generate_summary(&self, text: &str) -> Result<String> {
        // Simple extractive summarization
        let sentences: Vec<&str> = self.sentence_regex
            .split(text)
            .filter(|s| !s.trim().is_empty())
            .collect();

        if sentences.len() <= 3 {
            return Ok(text.to_string());
        }

        // Score sentences based on word frequency
        let word_freq = self.calculate_word_frequency(text);
        let mut sentence_scores: Vec<(usize, f64)> = Vec::new();

        for (i, sentence) in sentences.iter().enumerate() {
            let score = self.calculate_sentence_score(sentence, &word_freq);
            sentence_scores.push((i, score));
        }

        // Sort by score and take top sentences
        sentence_scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        
        let summary_sentences: Vec<usize> = sentence_scores
            .into_iter()
            .take(3)
            .map(|(i, _)| i)
            .collect();

        let mut summary_indices: Vec<usize> = summary_sentences.clone();
        summary_indices.sort();

        let summary: String = summary_indices
            .into_iter()
            .map(|i| sentences[i])
            .collect::<Vec<&str>>()
            .join(". ");

        Ok(summary + ".")
    }

    pub fn generate_summary_sync(&self, text: &str) -> String {
        let sentences: Vec<&str> = self.sentence_regex
            .split(text)
            .filter(|s| !s.trim().is_empty())
            .collect();

        if sentences.len() <= 3 {
            return text.to_string();
        }

        let word_freq = self.calculate_word_frequency(text);
        let mut sentence_scores: Vec<(usize, f64)> = Vec::new();

        for (i, sentence) in sentences.iter().enumerate() {
            let score = self.calculate_sentence_score(sentence, &word_freq);
            sentence_scores.push((i, score));
        }

        sentence_scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        
        let summary_sentences: Vec<usize> = sentence_scores
            .into_iter()
            .take(3)
            .map(|(i, _)| i)
            .collect();

        let mut summary_indices: Vec<usize> = summary_sentences.clone();
        summary_indices.sort();

        let summary: String = summary_indices
            .into_iter()
            .map(|i| sentences[i])
            .collect::<Vec<&str>>()
            .join(". ");

        summary + "."
    }

    fn calculate_word_frequency(&self, text: &str) -> HashMap<String, f64> {
        let words: Vec<String> = self.word_regex
            .find_iter(text)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| {
                word.len() > 2 && !self.stop_words.contains(word)
            })
            .collect();

        let total_words = words.len() as f64;
        let mut word_freq: HashMap<String, usize> = HashMap::new();
        
        for word in words {
            *word_freq.entry(word).or_insert(0) += 1;
        }

        word_freq
            .into_iter()
            .map(|(word, count)| (word, count as f64 / total_words))
            .collect()
    }

    fn calculate_sentence_score(&self, sentence: &str, word_freq: &HashMap<String, f64>) -> f64 {
        let words: Vec<String> = self.word_regex
            .find_iter(sentence)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| {
                word.len() > 2 && !self.stop_words.contains(word)
            })
            .collect();

        words
            .iter()
            .map(|word| word_freq.get(word).unwrap_or(&0.0))
            .sum()
    }

    pub fn calculate_similarity_sync(&self, text1: &str, text2: &str) -> f64 {
        let words1: std::collections::HashSet<String> = self.word_regex
            .find_iter(text1)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| {
                word.len() > 2 && !self.stop_words.contains(word)
            })
            .collect();

        let words2: std::collections::HashSet<String> = self.word_regex
            .find_iter(text2)
            .map(|m| m.as_str().to_lowercase())
            .filter(|word| {
                word.len() > 2 && !self.stop_words.contains(word)
            })
            .collect();

        let intersection = words1.intersection(&words2).count();
        let union = words1.union(&words2).count();

        if union == 0 {
            0.0
        } else {
            intersection as f64 / union as f64
        }
    }
}

#[derive(Debug, Clone)]
pub struct ProcessedText {
    pub original: String,
    pub cleaned: String,
    pub chunks: Vec<String>,
    pub keywords: Vec<String>,
    pub summary: String,
}
