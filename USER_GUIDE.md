# Cite-Agent User Guide

## 🚀 Getting Started

### Installation

```bash
# Install from PyPI
pip install cite-agent

# Verify installation
cite-agent --version
```

### First Time Setup

```bash
# Run setup wizard
cite-agent --setup

# Enter your academic email (e.g., user@university.edu)
# Enter your password
# The system will create your account automatically
```

---

## 💬 Basic Usage

### Interactive Mode

```bash
# Start interactive chat
cite-agent

# You'll see:
# 🤖 Processing: Your question here
# 📝 Response: [AI response with sources]
# 📊 Tokens used: 150 (Daily usage: 0.6%)
```

### Single Query Mode

```bash
# Ask a single question
cite-agent "Find research papers on machine learning in healthcare"

# Get financial data
cite-agent "What is Apple's current revenue?"

# Fact-check something
cite-agent "Is water's boiling point 100°C at standard pressure?"
```

---

## 🔬 Research Features

### Academic Paper Search

#### Basic Search
```bash
cite-agent "Find papers on transformer architecture"
```

#### Advanced Search
```bash
cite-agent "Find papers on 'attention mechanism' published after 2020 with more than 100 citations"
```

#### Specific Journal Search
```bash
cite-agent "Find papers in Nature about artificial intelligence"
```

### Citation Verification

#### Verify a Citation
```bash
cite-agent "Verify this citation: Smith, J. (2023). AI in Medicine. Nature, 45(2), 123-145."
```

#### Check DOI
```bash
cite-agent "Check DOI 10.1038/s41586-023-12345-6"
```

### Research Synthesis

#### Summarize Multiple Papers
```bash
cite-agent "Synthesize the key findings from these papers about deep learning in medical imaging"
```

#### Compare Research
```bash
cite-agent "Compare the approaches used in these two papers on neural networks"
```

---

## 💰 Financial Data

### Company Information

#### Basic Financial Data
```bash
cite-agent "What is Apple's revenue?"
cite-agent "Get Tesla's market cap"
cite-agent "Show Microsoft's profit margin"
```

#### Historical Data
```bash
cite-agent "Show Apple's revenue over the last 5 years"
cite-agent "Get Tesla's stock performance for 2024"
```

#### Financial Metrics
```bash
cite-agent "What are Apple's key financial ratios?"
cite-agent "Show Tesla's debt-to-equity ratio"
```

### Industry Analysis

#### Sector Comparison
```bash
cite-agent "Compare the financial performance of Apple, Microsoft, and Google"
```

#### Market Trends
```bash
cite-agent "What are the current trends in the tech sector?"
```

---

## 🎯 Fact-Checking & Verification

### Scientific Facts

#### Physics & Chemistry
```bash
cite-agent "What is the speed of light in vacuum?"
cite-agent "At what temperature does water boil at sea level?"
cite-agent "What is the chemical formula for water?"
```

#### Biology & Medicine
```bash
cite-agent "How many chambers does the human heart have?"
cite-agent "What is the normal human body temperature?"
cite-agent "What causes diabetes?"
```

### Historical Facts

#### Historical Events
```bash
cite-agent "When did World War II end?"
cite-agent "Who wrote Romeo and Juliet?"
cite-agent "What year was the internet invented?"
```

#### Cultural Facts
```bash
cite-agent "Who painted the Mona Lisa?"
cite-agent "What is the capital of France?"
cite-agent "Who wrote Harry Potter?"
```

---

## 🌍 Multi-Language Support

### Chinese (中文)

#### Research Questions
```bash
cite-agent "我的p值是0.05，這顯著嗎？"
cite-agent "找一些關於機器學習的論文"
cite-agent "驗證這個引用：張三 (2023). 人工智能研究. 科學雜誌, 45(2), 123-145."
```

#### Fact-Checking
```bash
cite-agent "天空是藍色的嗎？"
cite-agent "水在攝氏100度沸騰，對嗎？"
cite-agent "地球是圓的嗎？"
```

### Other Languages
```bash
cite-agent "¿Cuál es la capital de España?"  # Spanish
cite-agent "Quelle est la capitale de la France?"  # French
cite-agent "Was ist die Hauptstadt von Deutschland?"  # German
```

---

## 📊 Understanding Responses

### Response Format

Every response includes:

#### 📝 Response
The main answer to your question

#### 📊 Source Grounding
Information about where the data came from:
- API sources used
- Database queries executed
- External services accessed

#### 🔧 Tools Used
List of tools/functions used to generate the response:
- `archive_api` - Academic research
- `finsight_api` - Financial data
- `web_search` - Web search
- `calculation` - Mathematical computation

#### 📈 Confidence Score
A score from 0.0 to 1.0 indicating how confident the AI is in the response:
- 0.9-1.0: Very high confidence
- 0.7-0.9: High confidence
- 0.5-0.7: Medium confidence
- 0.0-0.5: Low confidence

#### 📊 Tokens Used
- Number of tokens consumed
- Daily usage percentage
- Remaining tokens for the day

### Example Response

```bash
cite-agent "What is Apple's revenue?"

📝 Response:
Apple's revenue for the most recent quarter is $94.04 billion (as of 2025-06-28).

📊 Source Grounding:
Data retrieved from SEC filings via FinSight API.

🔧 Tools Used: ['finsight_api']

📈 Confidence Score: 0.9

📊 Tokens Used: 150 (Daily usage: 0.6%)

_Data sources: FinSight GET calc/AAPL/revenue – ok_
```

---

## ⚙️ Advanced Usage

### Python API

#### Basic Usage
```python
import asyncio
from cite_agent import EnhancedNocturnalAgent, ChatRequest

async def main():
    # Initialize agent
    agent = EnhancedNocturnalAgent()
    await agent.initialize()
    
    # Create request
    request = ChatRequest(
        question="Find papers on machine learning",
        user_id="user123",
        conversation_id="conv456"
    )
    
    # Get response
    response = await agent.process_request(request)
    
    print(f"Response: {response.response}")
    print(f"Confidence: {response.confidence_score}")
    print(f"Tools used: {response.tools_used}")
    
    # Clean up
    await agent.close()

# Run the example
asyncio.run(main())
```

#### Streaming Responses
```python
async def streaming_example():
    agent = EnhancedNocturnalAgent()
    await agent.initialize()
    
    request = ChatRequest(
        question="Explain quantum computing",
        user_id="user123"
    )
    
    # Get streaming response
    stream = await agent.process_request_streaming(request)
    
    # Process chunks as they arrive
    async for chunk in stream:
        print(chunk, end='', flush=True)
    
    await agent.close()
```

#### Direct API Calls
```python
# Search academic papers
papers = await agent.search_academic_papers("machine learning", limit=5)
print(f"Found {len(papers['results'])} papers")

# Get financial data
financial_data = await agent.get_financial_data("AAPL", "revenue")
print(f"Apple revenue: ${financial_data['value']} billion")

# Synthesize research
synthesis = await agent.synthesize_research(
    paper_ids=["paper1", "paper2"], 
    max_words=500
)
print(f"Synthesis: {synthesis['synthesis']}")
```

---

## 🎨 Tips & Best Practices

### Writing Effective Queries

#### Be Specific
```bash
# ❌ Too vague
cite-agent "Tell me about AI"

# ✅ Specific and focused
cite-agent "Find recent papers on transformer architecture in natural language processing"
```

#### Use Keywords
```bash
# Include relevant keywords
cite-agent "Find papers on 'attention mechanism' in 'computer vision' published after 2020"
```

#### Ask Follow-up Questions
```bash
# First question
cite-agent "Find papers on machine learning in healthcare"

# Follow-up
cite-agent "What are the main challenges mentioned in those papers?"
cite-agent "Which papers have the highest citation counts?"
```

### Understanding Limitations

#### What Cite-Agent Does Well
- ✅ Academic research and citations
- ✅ Financial data and analysis
- ✅ Fact-checking with sources
- ✅ Multi-language support
- ✅ Mathematical calculations

#### What Cite-Agent Doesn't Do
- ❌ Real-time news (beyond what's in databases)
- ❌ Personal advice or medical diagnosis
- ❌ Creative writing or subjective opinions
- ❌ Access to private or restricted content

### Maximizing Accuracy

#### Use Academic Email
- Register with a .edu or .ac email for best results
- Academic emails get priority access to research databases

#### Be Patient
- Complex queries may take 30-60 seconds
- The system is searching multiple databases
- Quality takes time

#### Verify Sources
- Always check the provided citations
- Look at the confidence score
- Cross-reference with original sources

---

## 🐛 Troubleshooting

### Common Issues

#### "Not authenticated" Error
```bash
# Solution: Run setup again
cite-agent --setup
```

#### Slow Responses
```bash
# This is normal for complex queries
# Try breaking down your question into smaller parts
```

#### "No results found"
```bash
# Try different keywords
# Check spelling
# Use more general terms
# Try synonyms
```

#### CLI Hangs
```bash
# Press Ctrl+C to cancel
# Restart the CLI
# Check your internet connection
```

### Getting Help

#### Debug Mode
```bash
# Enable debug logging
export NOCTURNAL_DEBUG=1
cite-agent "your question"
```

#### Check Status
```bash
# Verify system status
cite-agent --version
cite-agent --tips
```

#### Contact Support
- **Email**: support@cite-agent.com
- **GitHub**: [Report issues](https://github.com/yourusername/cite-agent/issues)
- **Discord**: [Community support](https://discord.gg/cite-agent)

---

## 📚 Examples by Use Case

### For Students

#### Literature Reviews
```bash
cite-agent "Find papers on 'machine learning' in 'education' published in 2023"
cite-agent "What are the key findings in these papers about AI in student assessment?"
cite-agent "Compare the methodologies used in these studies"
```

#### Thesis Research
```bash
cite-agent "Find seminal papers on neural networks from the 1980s"
cite-agent "What is the current state of research in computer vision?"
cite-agent "Identify research gaps in AI ethics literature"
```

### For Researchers

#### Literature Discovery
```bash
cite-agent "Find papers citing 'Attention Is All You Need' (Vaswani et al., 2017)"
cite-agent "What are the most cited papers in 'Nature Machine Intelligence' this year?"
cite-agent "Find recent preprints on arXiv about large language models"
```

#### Citation Analysis
```bash
cite-agent "Verify the accuracy of this citation: [citation]"
cite-agent "Find the DOI for this paper: [title and authors]"
cite-agent "Check if this paper is peer-reviewed"
```

### For Professionals

#### Market Research
```bash
cite-agent "What is the current market size for AI in healthcare?"
cite-agent "Find industry reports on machine learning adoption"
cite-agent "What are the key trends in fintech innovation?"
```

#### Competitive Analysis
```bash
cite-agent "Compare the financial performance of Apple, Microsoft, and Google"
cite-agent "What are the latest developments in autonomous vehicles?"
cite-agent "Find patents filed by Tesla in 2024"
```

---

## 🎯 Pro Tips

### Power User Features

#### Batch Processing
```python
# Process multiple questions at once
questions = [
    "Find papers on AI in healthcare",
    "What is Apple's revenue?",
    "Verify this citation: ..."
]

for question in questions:
    response = await agent.process_request(ChatRequest(question=question))
    print(f"Q: {question}")
    print(f"A: {response.response}\n")
```

#### Custom Context
```python
# Add context to your requests
request = ChatRequest(
    question="Explain this concept",
    context={
        "domain": "machine learning",
        "level": "beginner",
        "focus": "practical applications"
    }
)
```

#### Response Filtering
```python
# Filter responses by confidence
if response.confidence_score > 0.8:
    print("High confidence response:", response.response)
else:
    print("Low confidence - verify sources:", response.response)
```

---

**Happy researching with Cite-Agent!** 🔬📚