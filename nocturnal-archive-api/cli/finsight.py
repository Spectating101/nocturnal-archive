#!/usr/bin/env python3
"""
FinSight CLI - Simple command-line interface for FinSight API
"""

import os
import sys
import requests
import json
import argparse
from typing import Dict, Any

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "demo-key-123")

class FinSightCLI:
    """Simple CLI for FinSight API"""
    
    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    def _make_request(self, path: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to FinSight API"""
        url = f"{self.base_url}{path}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error response: {e.response.text}")
            sys.exit(1)
    
    def get_revenue_series(self, ticker: str, limit: int = 12) -> Dict[str, Any]:
        """Get revenue series for a company"""
        path = f"/v1/finance/kpis/{ticker}/revenue?freq=Q&limit={limit}"
        return self._make_request(path)
    
    def get_metric(self, ticker: str, metric: str, period: str = "latest") -> Dict[str, Any]:
        """Get a specific metric for a company"""
        path = f"/v1/finance/calc/{ticker}/{metric}?period={period}&freq=Q"
        return self._make_request(path)
    
    def get_ebitda_margin_ttm(self, ticker: str, limit: int = 8) -> Dict[str, Any]:
        """Get TTM EBITDA margin series"""
        path = f"/v1/finance/calc/series/{ticker}/ebitdaMargin?freq=Q&limit={limit}&ttm=true"
        return self._make_request(path)
    
    def explain_expression(self, ticker: str, expr: str, period: str = "latest") -> Dict[str, Any]:
        """Explain a custom expression"""
        data = {
            "ticker": ticker,
            "expr": expr,
            "period": period,
            "freq": "Q"
        }
        return self._make_request("/v1/finance/calc/explain", method="POST", data=data)
    
    def get_segments(self, ticker: str, kpi: str = "revenue", dim: str = "Geography", limit: int = 8) -> Dict[str, Any]:
        """Get segment data for a company"""
        path = f"/v1/finance/segments/{ticker}/{kpi}?dim={dim}&freq=Q&limit={limit}"
        return self._make_request(path)
    
    def get_available_kpis(self) -> Dict[str, Any]:
        """Get list of available KPIs"""
        return self._make_request("/v1/finance/calc/registry/metrics")
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._make_request("/livez")

def format_number(value: float, unit: str = "") -> str:
    """Format number for display"""
    if abs(value) >= 1e12:
        return f"${value/1e12:.1f}T {unit}".strip()
    elif abs(value) >= 1e9:
        return f"${value/1e9:.1f}B {unit}".strip()
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M {unit}".strip()
    elif abs(value) >= 1e3:
        return f"${value/1e3:.1f}K {unit}".strip()
    else:
        return f"${value:.2f} {unit}".strip()

def format_percent(value: float) -> str:
    """Format percentage for display"""
    return f"{value*100:.1f}%"

def print_metric_result(result: Dict[str, Any]):
    """Print formatted metric result"""
    print(f"\n📊 {result.get('ticker', 'Unknown')} - {result.get('metric', 'Unknown')}")
    print(f"Period: {result.get('period', 'Unknown')}")
    print(f"Formula: {result.get('formula', 'Unknown')}")
    
    # Format value based on output type
    value = result.get('value', 0)
    output_type = result.get('output_type', 'value')
    
    if output_type == 'percent':
        formatted_value = format_percent(value)
    else:
        formatted_value = format_number(value)
    
    print(f"Value: {formatted_value}")
    
    # Show inputs if available
    inputs = result.get('inputs', {})
    if inputs:
        print("\nInputs:")
        for input_name, input_data in inputs.items():
            input_value = input_data.get('value', 0)
            print(f"  {input_name}: {format_number(input_value)}")
    
    # Show quality flags
    flags = result.get('quality_flags', [])
    if flags:
        print(f"\nQuality Flags: {', '.join(flags)}")

def print_series_result(result: Dict[str, Any]):
    """Print formatted series result"""
    ticker = result.get('ticker', 'Unknown')
    kpi = result.get('kpi', 'Unknown')
    data = result.get('data', [])
    
    print(f"\n📈 {ticker} - {kpi} Series")
    print(f"Periods: {len(data)}")
    
    for point in data[:5]:  # Show first 5 points
        period = point.get('period', 'Unknown')
        value = point.get('value', 0)
        unit = point.get('unit', '')
        
        if kpi.endswith('Margin') or 'Ratio' in kpi:
            formatted_value = format_percent(value)
        else:
            formatted_value = format_number(value, unit)
        
        print(f"  {period}: {formatted_value}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="FinSight CLI - Financial data analysis")
    parser.add_argument("ticker", nargs="?", default="AAPL", help="Company ticker symbol (default: AAPL)")
    parser.add_argument("--metric", "-m", help="Specific metric to get")
    parser.add_argument("--series", "-s", action="store_true", help="Get series data")
    parser.add_argument("--explain", "-e", help="Explain expression")
    parser.add_argument("--segments", action="store_true", help="Get segment data")
    parser.add_argument("--kpis", action="store_true", help="List available KPIs")
    parser.add_argument("--health", action="store_true", help="Check API health")
    parser.add_argument("--limit", "-l", type=int, default=8, help="Number of periods to retrieve")
    parser.add_argument("--base-url", default=BASE_URL, help="API base URL")
    parser.add_argument("--api-key", default=API_KEY, help="API key")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = FinSightCLI(args.base_url, args.api_key)
    
    try:
        if args.health:
            result = cli.health_check()
            print("✅ API Health Check")
            print(json.dumps(result, indent=2))
            
        elif args.kpis:
            result = cli.get_available_kpis()
            metrics = result.get('metrics', [])
            print(f"📚 Available KPIs ({len(metrics)} total):")
            for metric in metrics:
                print(f"  • {metric}")
                
        elif args.segments:
            result = cli.get_segments(args.ticker, limit=args.limit)
            print(f"\n🏢 {args.ticker} - Segment Analysis")
            series = result.get('series', [])
            for segment in series:
                segment_name = segment.get('segment', 'Unknown')
                points = segment.get('points', [])
                if points:
                    latest_value = points[0].get('value', 0)
                    latest_period = points[0].get('period', 'Unknown')
                    print(f"  {segment_name}: {format_number(latest_value)} ({latest_period})")
                    
        elif args.explain:
            result = cli.explain_expression(args.ticker, args.explain)
            print_metric_result(result)
            
        elif args.series:
            result = cli.get_ebitda_margin_ttm(args.ticker, args.limit)
            print_series_result(result)
            
        elif args.metric:
            result = cli.get_metric(args.ticker, args.metric)
            print_metric_result(result)
            
        else:
            # Default: show revenue series
            result = cli.get_revenue_series(args.ticker, args.limit)
            print_series_result(result)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
