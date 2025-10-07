"""
Yahoo Finance Direct Adapter - Stub
"""

class YahooFinanceDirectAdapter:
    """Stub implementation for missing Yahoo Finance Direct adapter"""
    
    def __init__(self):
        pass
    
    async def get_fact(self, ticker: str, concept: str, period: str = None, freq: str = "Q"):
        """Stub method - returns None to indicate no data available"""
        return None
    
    async def get_series(self, ticker: str, concept: str, freq: str = "Q", limit: int = 12):
        """Stub method - returns empty list"""
        return []