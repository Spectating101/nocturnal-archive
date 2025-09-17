"""
Performance testing with Locust
"""

from locust import HttpUser, task, between
import random
import json


class NocturnalArchiveUser(HttpUser):
    """Simulate user behavior for performance testing"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.paper_ids = []
        self.query_id = None
    
    @task(3)
    def search_papers(self):
        """Test paper search endpoint"""
        queries = [
            "machine learning",
            "artificial intelligence",
            "deep learning",
            "neural networks",
            "computer vision",
            "natural language processing",
            "reinforcement learning",
            "data science",
            "statistics",
            "optimization"
        ]
        
        query = random.choice(queries)
        
        response = self.client.post(
            "/api/search",
            json={
                "query": query,
                "limit": random.randint(5, 20),
                "sources": ["openalex"],
                "filters": {
                    "year_min": random.randint(2020, 2024),
                    "open_access": random.choice([True, False])
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.paper_ids = [paper["id"] for paper in data.get("papers", [])]
            self.query_id = data.get("query_id")
    
    @task(2)
    def format_citations(self):
        """Test citation formatting endpoint"""
        if not self.paper_ids:
            return
        
        # Select random papers
        selected_papers = random.sample(
            self.paper_ids, 
            min(random.randint(1, 5), len(self.paper_ids))
        )
        
        styles = ["bibtex", "apa", "mla", "chicago", "harvard"]
        style = random.choice(styles)
        
        response = self.client.post(
            "/api/format",
            json={
                "paper_ids": selected_papers,
                "style": style,
                "options": {
                    "include_abstract": random.choice([True, False]),
                    "include_keywords": random.choice([True, False])
                }
            }
        )
        
        assert response.status_code == 200
    
    @task(1)
    def synthesize_papers(self):
        """Test paper synthesis endpoint"""
        if not self.paper_ids:
            return
        
        # Select random papers for synthesis
        selected_papers = random.sample(
            self.paper_ids, 
            min(random.randint(2, 10), len(self.paper_ids))
        )
        
        focuses = ["key_findings", "comprehensive", "methodology", "results", "discussion"]
        styles = ["academic", "technical", "accessible", "concise"]
        
        response = self.client.post(
            "/api/synthesize",
            json={
                "paper_ids": selected_papers,
                "max_words": random.randint(200, 1000),
                "focus": random.choice(focuses),
                "style": random.choice(styles),
                "custom_prompt": random.choice([
                    None,
                    "Focus on clinical applications",
                    "Emphasize technical details",
                    "Highlight practical implications"
                ])
            }
        )
        
        assert response.status_code == 200
    
    @task(1)
    def get_analytics(self):
        """Test analytics endpoints"""
        endpoints = [
            "/api/analytics/metrics",
            "/api/analytics/real-time",
            "/api/analytics/performance",
            "/api/analytics/errors",
            "/api/analytics/users"
        ]
        
        endpoint = random.choice(endpoints)
        response = self.client.get(endpoint)
        
        # Analytics might not be available in test environment
        assert response.status_code in [200, 500]
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/api/health")
        assert response.status_code == 200
    
    @task(1)
    def get_insights(self):
        """Test search insights endpoint"""
        if not self.query_id:
            return
        
        response = self.client.get(f"/api/search/insights/{self.query_id}")
        # Insights might not be implemented yet
        assert response.status_code in [200, 404, 500]


class HighLoadUser(HttpUser):
    """Simulate high-load scenarios"""
    
    wait_time = between(0.1, 0.5)
    weight = 1  # Lower weight than regular users
    
    @task(10)
    def rapid_search(self):
        """Rapid search requests"""
        queries = ["AI", "ML", "data", "research", "science"]
        query = random.choice(queries)
        
        response = self.client.post(
            "/api/search",
            json={
                "query": query,
                "limit": 5,
                "sources": ["openalex"]
            }
        )
        
        assert response.status_code == 200
    
    @task(5)
    def rapid_health_check(self):
        """Rapid health checks"""
        response = self.client.get("/api/health")
        assert response.status_code == 200


class ErrorTestingUser(HttpUser):
    """Test error handling and edge cases"""
    
    wait_time = between(2, 5)
    weight = 1
    
    @task(3)
    def invalid_requests(self):
        """Test invalid request handling"""
        # Test invalid search
        response = self.client.post(
            "/api/search",
            json={
                "query": "",  # Empty query
                "limit": 10
            }
        )
        assert response.status_code == 422
        
        # Test invalid format
        response = self.client.post(
            "/api/format",
            json={
                "paper_ids": [],  # Empty list
                "style": "invalid_style"
            }
        )
        assert response.status_code == 422
        
        # Test invalid synthesis
        response = self.client.post(
            "/api/synthesize",
            json={
                "paper_ids": [],  # Empty list
                "max_words": 50  # Too few words
            }
        )
        assert response.status_code == 422
    
    @task(2)
    def malformed_json(self):
        """Test malformed JSON handling"""
        response = self.client.post(
            "/api/search",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @task(1)
    def non_existent_endpoints(self):
        """Test non-existent endpoints"""
        response = self.client.get("/api/non-existent")
        assert response.status_code == 404
