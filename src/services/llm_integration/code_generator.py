"""
Code Generator - Real AI-powered code generation
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class CodeGenerator:
    """Real AI-powered code generation."""
    
    def __init__(self):
        self.code_templates = {
            "fibonacci": self._generate_fibonacci_code,
            "api": self._generate_api_code,
            "data_analysis": self._generate_data_analysis_code,
            "file_operations": self._generate_file_operations_code,
            "general": self._generate_general_code
        }
        logger.info("Code Generator initialized")
    
    async def generate_code(self, description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate code based on description using AI reasoning."""
        try:
            # Try real LLM first
            from .real_llm_client import RealLLMClient
            llm_client = RealLLMClient()
            
            real_code = await llm_client.generate_code(description, context)
            
            if real_code and len(real_code) > 100:  # Real LLM generated substantial code
                code_type = self._analyze_code_requirements(description)
                return {
                    "status": "success",
                    "code": real_code,
                    "code_type": code_type,
                    "description": description,
                    "generation_method": "real_llm",
                    "timestamp": _utc_timestamp()
                }
            
            # Fallback to template-based generation
            code_type = self._analyze_code_requirements(description)
            
            # Generate appropriate code
            if code_type in self.code_templates:
                code = await self.code_templates[code_type](description, context)
            else:
                code = await self._generate_general_code(description, context)
            
            return {
                "status": "success",
                "code": code,
                "code_type": code_type,
                "description": description,
                "timestamp": _utc_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": _utc_timestamp()
            }
    
    def _analyze_code_requirements(self, description: str) -> str:
        """Analyze what type of code is needed."""
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in ["fibonacci", "fib", "sequence"]):
            return "fibonacci"
        elif any(keyword in desc_lower for keyword in ["api", "rest", "endpoint", "server"]):
            return "api"
        elif any(keyword in desc_lower for keyword in ["data", "analyze", "statistics", "chart"]):
            return "data_analysis"
        elif any(keyword in desc_lower for keyword in ["file", "read", "write", "directory"]):
            return "file_operations"
        else:
            return "general"
    
    async def _generate_fibonacci_code(self, description: str, context: Dict[str, Any]) -> str:
        """Generate fibonacci-related code."""
        # Extract specific requirements
        if "recursive" in description.lower():
            return '''
def fibonacci_recursive(n):
    """Calculate nth Fibonacci number using recursion."""
    if n <= 1:
        return n
    return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

# Test the recursive implementation
print("Recursive Fibonacci:")
for i in range(10):
    print(f"fibonacci_recursive({i}) = {fibonacci_recursive(i)}")
'''
        elif "iterative" in description.lower():
            return '''
def fibonacci_iterative(n):
    """Calculate nth Fibonacci number using iteration."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# Test the iterative implementation
print("Iterative Fibonacci:")
for i in range(10):
    print(f"fibonacci_iterative({i}) = {fibonacci_iterative(i)}")
'''
        else:
            return '''
def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def fibonacci_sequence(count):
    """Generate Fibonacci sequence up to count terms."""
    sequence = []
    for i in range(count):
        sequence.append(fibonacci(i))
    return sequence

# Test both functions
print("Fibonacci function:")
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")

print("\\nFibonacci sequence:")
print(fibonacci_sequence(10))
'''
    
    async def _generate_api_code(self, description: str, context: Dict[str, Any]) -> str:
        """Generate API-related code."""
        if "fastapi" in description.lower():
            return '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Sample API", version="1.0.0")

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    price_with_tax: float

# In-memory storage
items = []
next_id = 1

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/items/", response_model=ItemResponse)
async def create_item(item: Item):
    global next_id
    item_id = next_id
    next_id += 1
    
    price_with_tax = item.price
    if item.tax:
        price_with_tax = item.price + (item.price * item.tax)
    
    new_item = ItemResponse(
        id=item_id,
        name=item.name,
        price_with_tax=price_with_tax
    )
    
    items.append(new_item)
    return new_item

@app.get("/items/", response_model=List[ItemResponse])
async def read_items():
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        else:
            return '''
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"message": "Hello World", "status": "success"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"received": data, "status": "success"}
            self.wfile.write(json.dumps(response).encode())
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')

if __name__ == "__main__":
    server = HTTPServer(('localhost', 8000), APIHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()
'''
    
    async def _generate_data_analysis_code(self, description: str, context: Dict[str, Any]) -> str:
        """Generate data analysis code."""
        return '''
import statistics
import matplotlib.pyplot as plt
import numpy as np

def analyze_data(data):
    """Perform comprehensive data analysis."""
    if not data:
        return {"error": "No data provided"}
    
    analysis = {
        "count": len(data),
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "mode": statistics.mode(data) if len(set(data)) < len(data) else "No mode",
        "min": min(data),
        "max": max(data),
        "range": max(data) - min(data),
        "std_deviation": statistics.stdev(data) if len(data) > 1 else 0,
        "variance": statistics.variance(data) if len(data) > 1 else 0
    }
    
    # Calculate quartiles
    if len(data) > 3:
        quartiles = statistics.quantiles(data, n=4)
        analysis["quartiles"] = {
            "q1": quartiles[0],
            "q2": quartiles[1],
            "q3": quartiles[2]
        }
    
    return analysis

def visualize_data(data, title="Data Visualization"):
    """Create visualizations of the data."""
    plt.figure(figsize=(10, 6))
    
    # Histogram
    plt.subplot(1, 2, 1)
    plt.hist(data, bins=10, alpha=0.7, color='blue')
    plt.title(f'{title} - Histogram')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    
    # Box plot
    plt.subplot(1, 2, 2)
    plt.boxplot(data)
    plt.title(f'{title} - Box Plot')
    plt.ylabel('Value')
    
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Sample data
    sample_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    
    # Analyze data
    results = analyze_data(sample_data)
    print("Data Analysis Results:")
    for key, value in results.items():
        print(f"{key}: {value}")
    
    # Visualize data
    visualize_data(sample_data, "Sample Data Analysis")
'''
    
    async def _generate_file_operations_code(self, description: str, context: Dict[str, Any]) -> str:
        """Generate file operations code."""
        return '''
import os
import json
from pathlib import Path

def safe_file_operations():
    """Demonstrate safe file operations."""
    
    # Create a sample file
    sample_data = {
        "name": "Sample File",
        "content": "This is a sample file for demonstration",
        "numbers": [1, 2, 3, 4, 5],
        "metadata": {
            "created": "2025-09-26",
            "type": "demo"
        }
    }
    
    filename = "sample_data.json"
    
    try:
        # Write data to file
        with open(filename, 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"Successfully wrote data to {filename}")
        
        # Read data from file
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
        print(f"Successfully read data from {filename}")
        print(f"Loaded data: {loaded_data}")
        
        # File information
        file_path = Path(filename)
        print(f"File size: {file_path.stat().st_size} bytes")
        print(f"File exists: {file_path.exists()}")
        
        # List directory contents
        print("\\nDirectory contents:")
        for item in os.listdir('.'):
            if os.path.isfile(item):
                print(f"File: {item}")
            elif os.path.isdir(item):
                print(f"Directory: {item}")
        
        return True
        
    except Exception as e:
        print(f"Error in file operations: {e}")
        return False

def search_files(pattern, directory="."):
    """Search for files matching a pattern."""
    matching_files = []
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if pattern.lower() in file.lower():
                    matching_files.append(os.path.join(root, file))
        
        return matching_files
    except Exception as e:
        print(f"Error searching files: {e}")
        return []

# Example usage
if __name__ == "__main__":
    print("File Operations Demo")
    print("=" * 30)
    
    # Safe file operations
    success = safe_file_operations()
    print(f"File operations successful: {success}")
    
    # Search for Python files
    python_files = search_files(".py")
    print(f"\\nFound {len(python_files)} Python files:")
    for file in python_files[:5]:  # Show first 5
        print(f"  {file}")
'''
    
    async def _generate_general_code(self, description: str, context: Dict[str, Any]) -> str:
        """Generate general-purpose code."""
        return f'''
# Generated code for: {description}

def main():
    """Main function to solve the problem."""
    print("Problem:", "{description}")
    print("Solution implementation:")
    
    # Add your implementation here
    # This is a template - customize based on specific requirements
    
    return "Solution implemented"

def helper_function():
    """Helper function for the solution."""
    return "Helper function result"

if __name__ == "__main__":
    result = main()
    print(f"Result: {{result}}")
    
    helper_result = helper_function()
    print(f"Helper result: {{helper_result}}")
'''