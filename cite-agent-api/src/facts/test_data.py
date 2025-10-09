"""Test fixtures for FactsStore enabling deterministic KPI calculations in tests."""
from __future__ import annotations

from typing import Dict, Any

TEST_COMPANY_DATA: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "cik": "0000320193",
        "entity_name": "Apple Inc.",
        "sic": "3571",
        "sic_description": "Electronic Computers",
        "tickers": ["AAPL"],
        "facts": {
            "us-gaap:SalesRevenueNet": [
                {
                    "value": 119_575_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:CostOfGoodsAndServicesSold": [
                {
                    "value": 70_555_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:OperatingIncomeLoss": [
                {
                    "value": 38_000_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:DepreciationDepletionAndAmortization": [
                {
                    "value": 3_600_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:NetIncomeLoss": [
                {
                    "value": 33_916_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:AssetsCurrent": [
                {
                    "value": 146_000_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "instant",
                    "restated": False,
                }
            ],
            "us-gaap:LiabilitiesCurrent": [
                {
                    "value": 140_385_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "instant",
                    "restated": False,
                }
            ],
            "us-gaap:Assets": [
                {
                    "value": 352_755_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "instant",
                    "restated": False,
                }
            ],
            "us-gaap:StockholdersEquity": [
                {
                    "value": 23_090_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "instant",
                    "restated": False,
                }
            ],
            "us-gaap:NetCashProvidedByUsedInOperatingActivities": [
                {
                    "value": 42_000_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:NetCashProvidedByUsedInInvestingActivities": [
                {
                    "value": -3_200_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:NetCashProvidedByUsedInFinancingActivities": [
                {
                    "value": -22_000_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding": [
                {
                    "value": 15_900_000_000,
                    "unit": "shares",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic": [
                {
                    "value": 15_700_000_000,
                    "unit": "shares",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
            "us-gaap:DebtLongtermAndShorttermCombinedAmount": [
                {
                    "value": 110_000_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "instant",
                    "restated": False,
                }
            ],
            "us-gaap:CashAndCashEquivalentsAtCarryingValue": [
                {
                    "value": 30_500_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "instant",
                    "restated": False,
                }
            ],
            "us-gaap:InterestExpense": [
                {
                    "value": 1_950_000_000,
                    "unit": "USD",
                    "end_date": "2024-Q4",
                    "accession": "0000320193-24-000119",
                    "frame": "CY2024Q4",
                    "dimensions": {},
                    "period_type": "duration",
                    "restated": False,
                }
            ],
        },
    }
}

# Convenience lookup by CIK
TEST_COMPANY_BY_CIK = {
    company["cik"]: company for company in TEST_COMPANY_DATA.values()
}
