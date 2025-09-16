use anyhow::Result;
use reqwest::Client;
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::Duration;
use tokio::time::sleep;
use url::Url;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapedData {
    pub url: String,
    pub title: String,
    pub content: String,
    pub metadata: HashMap<String, String>,
}

pub struct WebScraper {
    client: Client,
    rate_limit_delay: Duration,
}

impl WebScraper {
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .user_agent("Mozilla/5.0 (compatible; NocturnalArchive/1.0; +https://nocturnalarchive.com/bot)")
            .build()
            .unwrap_or_else(|_| Client::new());

        Self {
            client,
            rate_limit_delay: Duration::from_millis(100), // 10 requests per second
        }
    }

    pub async fn scrape_url(&self, url: &str) -> Result<ScrapedData> {
        // Rate limiting
        sleep(self.rate_limit_delay).await;

        let response = self.client.get(url).send().await?;
        
        if !response.status().is_success() {
            return Err(anyhow::anyhow!("HTTP error: {}", response.status()));
        }

        let html = response.text().await?;
        let document = Html::parse_document(&html);

        // Extract title
        let title_selector = Selector::parse("title").unwrap();
        let title = document
            .select(&title_selector)
            .next()
            .map(|el| el.inner_html())
            .unwrap_or_else(|| "No title".to_string());

        // Extract main content (prioritize article, main, or body)
        let content_selectors = [
            "article",
            "main",
            "[role='main']",
            ".content",
            ".main-content",
            "body"
        ];

        let mut content = String::new();
        for selector_str in &content_selectors {
            if let Ok(selector) = Selector::parse(selector_str) {
                if let Some(element) = document.select(&selector).next() {
                    content = self.clean_html_content(&element.inner_html());
                    if !content.is_empty() {
                        break;
                    }
                }
            }
        }

        // Extract metadata
        let mut metadata = HashMap::new();
        
        // Meta tags
        let meta_selector = Selector::parse("meta").unwrap();
        for meta in document.select(&meta_selector) {
            if let (Some(name), Some(content)) = (
                meta.value().attr("name").or(meta.value().attr("property")),
                meta.value().attr("content")
            ) {
                metadata.insert(name.to_string(), content.to_string());
            }
        }

        // Open Graph tags
        let og_selector = Selector::parse("[property^='og:']").unwrap();
        for og in document.select(&og_selector) {
            if let (Some(property), Some(content)) = (
                og.value().attr("property"),
                og.value().attr("content")
            ) {
                metadata.insert(property.to_string(), content.to_string());
            }
        }

        Ok(ScrapedData {
            url: url.to_string(),
            title,
            content,
            metadata,
        })
    }

    fn clean_html_content(&self, html: &str) -> String {
        // Remove script and style tags
        let re_script = regex::Regex::new(r"<script[^>]*>.*?</script>").unwrap();
        let re_style = regex::Regex::new(r"<style[^>]*>.*?</style>").unwrap();
        let re_nav = regex::Regex::new(r"<nav[^>]*>.*?</nav>").unwrap();
        let re_header = regex::Regex::new(r"<header[^>]*>.*?</header>").unwrap();
        let re_footer = regex::Regex::new(r"<footer[^>]*>.*?</footer>").unwrap();
        let re_ads = regex::Regex::new(r"<div[^>]*class[^>]*ad[^>]*>.*?</div>").unwrap();

        let mut cleaned = html.to_string();
        cleaned = re_script.replace_all(&cleaned, "").to_string();
        cleaned = re_style.replace_all(&cleaned, "").to_string();
        cleaned = re_nav.replace_all(&cleaned, "").to_string();
        cleaned = re_header.replace_all(&cleaned, "").to_string();
        cleaned = re_footer.replace_all(&cleaned, "").to_string();
        cleaned = re_ads.replace_all(&cleaned, "").to_string();

        // Convert HTML to text
        html2text::from_read(cleaned.as_bytes(), 80)
    }

    pub async fn scrape_urls_batch(&self, urls: &[String]) -> Result<Vec<ScrapedData>> {
        let mut results = Vec::new();
        let mut futures = Vec::new();

        for url in urls {
            let scraper = self.clone();
            let url = url.clone();
            let future = async move {
                scraper.scrape_url(&url).await
            };
            futures.push(future);
        }

        // Process in batches to avoid overwhelming servers
        let batch_size = 5;
        for chunk in futures.chunks(batch_size) {
            let batch_results = futures::future::join_all(chunk).await;
            for result in batch_results {
                match result {
                    Ok(data) => results.push(data),
                    Err(e) => eprintln!("Error scraping URL: {}", e),
                }
            }
            // Rate limiting between batches
            sleep(Duration::from_secs(1)).await;
        }

        Ok(results)
    }
}

impl Clone for WebScraper {
    fn clone(&self) -> Self {
        Self {
            client: self.client.clone(),
            rate_limit_delay: self.rate_limit_delay,
        }
    }
}
