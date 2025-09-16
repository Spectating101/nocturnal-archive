use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use tokio::time::sleep;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CachedItem<T> {
    pub data: T,
    pub created_at: Instant,
    pub expires_at: Option<Instant>,
}

impl<T> CachedItem<T> {
    pub fn new(data: T, ttl: Option<Duration>) -> Self {
        let now = Instant::now();
        let expires_at = ttl.map(|duration| now + duration);
        
        Self {
            data,
            created_at: now,
            expires_at,
        }
    }

    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            Instant::now() > expires_at
        } else {
            false
        }
    }
}

pub struct ResponseCache {
    cache: DashMap<String, CachedItem<String>>,
    default_ttl: Duration,
    cleanup_interval: Duration,
}

impl ResponseCache {
    pub fn new() -> Self {
        let cache = DashMap::new();
        let default_ttl = Duration::from_secs(3600); // 1 hour
        let cleanup_interval = Duration::from_secs(300); // 5 minutes

        let cache_instance = Self {
            cache,
            default_ttl,
            cleanup_interval,
        };

        // Start cleanup task
        let cache_clone = cache_instance.cache.clone();
        let cleanup_interval = cache_instance.cleanup_interval;
        
        tokio::spawn(async move {
            loop {
                sleep(cleanup_interval).await;
                Self::cleanup_expired(&cache_clone);
            }
        });

        cache_instance
    }

    pub async fn get<T>(&self, key: &str) -> Option<T>
    where
        T: for<'de> Deserialize<'de> + Clone,
    {
        if let Some(cached_item) = self.cache.get(key) {
            if cached_item.is_expired() {
                // Remove expired item
                self.cache.remove(key);
                return None;
            }

            // Try to deserialize the cached data
            if let Ok(data) = serde_json::from_str::<T>(&cached_item.data) {
                return Some(data);
            }
        }
        None
    }

    pub async fn set<T>(&self, key: &str, value: &T)
    where
        T: Serialize,
    {
        if let Ok(serialized) = serde_json::to_string(value) {
            let cached_item = CachedItem::new(serialized, Some(self.default_ttl));
            self.cache.insert(key.to_string(), cached_item);
        }
    }

    pub async fn set_with_ttl<T>(&self, key: &str, value: &T, ttl: Duration)
    where
        T: Serialize,
    {
        if let Ok(serialized) = serde_json::to_string(value) {
            let cached_item = CachedItem::new(serialized, Some(ttl));
            self.cache.insert(key.to_string(), cached_item);
        }
    }

    pub async fn remove(&self, key: &str) {
        self.cache.remove(key);
    }

    pub async fn clear(&self) {
        self.cache.clear();
    }

    pub async fn size(&self) -> usize {
        self.cache.len()
    }

    pub async fn keys(&self) -> Vec<String> {
        self.cache
            .iter()
            .map(|entry| entry.key().clone())
            .collect()
    }

    pub async fn contains_key(&self, key: &str) -> bool {
        self.cache.contains_key(key)
    }

    pub async fn get_stats(&self) -> CacheStats {
        let total_items = self.cache.len();
        let mut expired_items = 0;
        let mut valid_items = 0;

        for entry in self.cache.iter() {
            if entry.is_expired() {
                expired_items += 1;
            } else {
                valid_items += 1;
            }
        }

        CacheStats {
            total_items,
            valid_items,
            expired_items,
        }
    }

    fn cleanup_expired(cache: &DashMap<String, CachedItem<String>>) {
        let mut to_remove = Vec::new();

        for entry in cache.iter() {
            if entry.is_expired() {
                to_remove.push(entry.key().clone());
            }
        }

        for key in to_remove {
            cache.remove(&key);
        }
    }
}

#[derive(Debug, Clone)]
pub struct CacheStats {
    pub total_items: usize,
    pub valid_items: usize,
    pub expired_items: usize,
}

impl Default for ResponseCache {
    fn default() -> Self {
        Self::new()
    }
}

// Thread-safe cache with automatic serialization/deserialization
pub struct TypedCache<T> {
    cache: DashMap<String, CachedItem<T>>,
    default_ttl: Duration,
}

impl<T> TypedCache<T>
where
    T: Clone + Send + Sync + 'static,
{
    pub fn new() -> Self {
        Self {
            cache: DashMap::new(),
            default_ttl: Duration::from_secs(3600),
        }
    }

    pub fn new_with_ttl(default_ttl: Duration) -> Self {
        Self {
            cache: DashMap::new(),
            default_ttl,
        }
    }

    pub fn get(&self, key: &str) -> Option<T> {
        if let Some(cached_item) = self.cache.get(key) {
            if cached_item.is_expired() {
                self.cache.remove(key);
                return None;
            }
            return Some(cached_item.data.clone());
        }
        None
    }

    pub fn set(&self, key: &str, value: T) {
        let cached_item = CachedItem::new(value, Some(self.default_ttl));
        self.cache.insert(key.to_string(), cached_item);
    }

    pub fn set_with_ttl(&self, key: &str, value: T, ttl: Duration) {
        let cached_item = CachedItem::new(value, Some(ttl));
        self.cache.insert(key.to_string(), cached_item);
    }

    pub fn remove(&self, key: &str) {
        self.cache.remove(key);
    }

    pub fn clear(&self) {
        self.cache.clear();
    }

    pub fn size(&self) -> usize {
        self.cache.len()
    }

    pub fn contains_key(&self, key: &str) -> bool {
        self.cache.contains_key(key)
    }
}

impl<T> Default for TypedCache<T>
where
    T: Clone + Send + Sync + 'static,
{
    fn default() -> Self {
        Self::new()
    }
}
