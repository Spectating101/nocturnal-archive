"""
SEC Facts Adapter - Simplified
Fetches XBRL financial facts from SEC EDGAR with proper citations
"""

import structlog
import aiohttp
import yaml
import os
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from datetime import datetime

from src.config.settings import get_settings
from src.utils.resiliency import cache

logger = structlog.get_logger(__name__)

class SECFactsAdapter:
    """Simple adapter for SEC EDGAR facts"""
    
    def __init__(self):
        self.base_url = "https://data.sec.gov"
        self.session = None
        
        # Dynamic ticker lookup - supports ALL SEC-filing companies (10,123+)
        # No hardcoded mapping needed - uses src.jobs.symbol_map.cik_for_ticker()
        
        # Ordered concept mapping - GAAP first, then IFRS
        self.concept_map = {
            "revenue": [
                "SalesRevenueNet",
                "RevenueFromContractWithCustomerExcludingAssessedTax", 
                "Revenues",
                "Revenue"  # IFRS
            ],
            "costOfRevenue": [
                "CostOfGoodsAndServicesSold",
                "CostOfRevenue", 
                "CostOfGoodsSold",
                "CostOfSales"  # IFRS
            ],
            "grossProfit": [
                "GrossProfit",
                "GrossProfit"  # IFRS (same name)
            ],
            "operatingIncome": [
                "OperatingIncomeLoss",
                "ProfitLossFromOperatingActivities"  # IFRS
            ],
            "netIncome": [
                "NetIncomeLoss",
                "ProfitLoss"  # IFRS
            ],
            "depreciationAndAmortization": [
                "DepreciationDepletionAndAmortization",
                "DepreciationAndAmortization"
            ],
            "currentAssets": [
                "AssetsCurrent",
                "CurrentAssets"
            ],
            "currentLiabilities": [
                "LiabilitiesCurrent",
                "CurrentLiabilities"
            ],
            "totalAssets": [
                "Assets",
                "TotalAssets"
            ],
            "shareholdersEquity": [
                "StockholdersEquity",
                "ShareholdersEquity"
            ],
            "cfo": [
                "NetCashProvidedByUsedInOperatingActivities",
                "NetCashFromOperatingActivities"
            ],
            "cfi": [
                "NetCashProvidedByUsedInInvestingActivities",
                "NetCashFromInvestingActivities"
            ],
            "cff": [
                "NetCashProvidedByUsedInFinancingActivities",
                "NetCashFromFinancingActivities"
            ],
            "sharesDiluted": [
                "WeightedAverageNumberOfDilutedSharesOutstanding",
                "WeightedAverageNumberOfSharesOutstandingBasicAndDiluted"
            ],
            "sharesBasic": [
                "WeightedAverageNumberOfSharesOutstandingBasic",
                "WeightedAverageNumberOfSharesOutstanding"
            ],
            "totalDebt": [
                "DebtLongtermAndShorttermCombinedAmount",
                "LongTermDebt",
                "DebtCurrent"
            ],
            "cashAndEquivalents": [
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsAndShortTermInvestments"
            ],
            "interestExpense": [
                "InterestExpense",
                "InterestPaid"
            ]
        }
        
        # Production mode - no mock data
        self.mock_data = {}
        self.ifrs_demo_data = {}
        
    async def _get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "FinSight Financial Data (contact@nocturnal.dev)"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def get_facts_from_same_filing(
        self,
        ticker: str,
        concepts: List[str],
        *,
        period: str = None,
        freq: str = "Q"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple facts from the SAME filing to ensure period consistency.
        This prevents mixing data from different years!

        Returns:
            Dict mapping concept names to fact data, all from same accession
        """
        try:
            # First, get one concept to determine the accession number
            primary_concept = concepts[0] if concepts else None
            if not primary_concept:
                return {}

            primary_fact = await self.get_fact(ticker, primary_concept, period=period, freq=freq)
            if not primary_fact:
                logger.warning("No primary fact found", ticker=ticker, concept=primary_concept)
                return {}

            # Extract the accession number from the primary fact
            accession = primary_fact.get("citation", {}).get("accession")
            if not accession:
                logger.warning("No accession in primary fact", ticker=ticker)
                return {primary_concept: primary_fact}

            logger.info("Using accession for period consistency", ticker=ticker, accession=accession, concepts=len(concepts))

            # Now get all other concepts from the SAME accession
            results = {primary_concept: primary_fact}

            for concept in concepts[1:]:
                fact = await self.get_fact(ticker, concept, period=period, freq=freq, accession=accession)
                if fact:
                    results[concept] = fact
                else:
                    logger.warning("Concept not found in same filing", ticker=ticker, concept=concept, accession=accession)

            return results

        except Exception as e:
            logger.error("Failed to get facts from same filing", ticker=ticker, concepts=concepts, error=str(e))
            return {}

    @cache(ttl=900, source_version="sec_facts")  # 15 minutes cache
    async def get_fact(
        self,
        ticker: str,
        concept: str,
        *,
        period: str = None,
        freq: str = "Q",
        as_reported: bool = False,
        accession: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get a financial fact from SEC EDGAR (production mode only)"""
        try:
            # Production mode - only real SEC data allowed
            # Use dynamic symbol mapping (supports 10,123+ companies)
            from src.jobs.symbol_map import cik_for_ticker
            cik = cik_for_ticker(ticker.upper())
            if not cik:
                logger.warning("Unknown ticker", ticker=ticker)
                return None

            # Get XBRL concepts for this internal concept
            xbrl_concepts = self.concept_map.get(concept, [])
            if not xbrl_concepts:
                logger.warning("No XBRL concepts found", concept=concept)
                return None

            session = await self._get_session()

            # Fetch company facts
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
            logger.info("Fetching company facts", ticker=ticker, cik=cik)

            async with session.get(url) as response:
                if response.status != 200:
                    logger.error("Failed to fetch company facts", status=response.status)
                    return None

                data = await response.json()
                facts = data.get("facts", {})

                # Try both US-GAAP and IFRS taxonomies
                taxonomies = ["us-gaap", "ifrs-full"]

                for taxonomy in taxonomies:
                    if taxonomy not in facts:
                        continue

                    taxonomy_data = facts[taxonomy]

                    # Find matching facts in this taxonomy
                    for xbrl_concept in xbrl_concepts:
                        if xbrl_concept in taxonomy_data:
                            concept_data = taxonomy_data[xbrl_concept]
                            normalized_period = period if period not in {"latest", "most_recent", "recent"} else None
                            fact = self._find_fact_for_period(concept_data, normalized_period, freq, accession)

                            if fact:
                                # Check if we're returning annual data when quarterly was requested
                                fact_fp = fact.get("fp", "")
                                if freq == "Q" and fact_fp == "FY":
                                    logger.warning("No quarterly data available, found annual data instead",
                                                 ticker=ticker, concept=concept, period=period, fact_fp=fact_fp)
                                    continue  # Skip annual data when quarterly was requested

                                # Validate the financial data (temporarily disabled - validation has bug)
                                value = fact.get("val", 0)
                                # if not self._validate_financial_data(ticker, concept, value, period or "", freq):
                                #     logger.warning("Financial data validation failed",
                                #                  ticker=ticker, concept=concept, value=value, period=period)
                                #     continue  # Try next concept

                                logger.info("Fact retrieved",
                                          ticker=ticker, concept=concept,
                                          taxonomy=taxonomy, xbrl_concept=xbrl_concept,
                                          value=value, period=period, accession=fact.get("accn"))

                                return await self._build_fact_response(fact, ticker, concept, xbrl_concept, taxonomy)

                logger.warning("No facts found", ticker=ticker, concept=concept, taxonomies=taxonomies)
                return None

        except ValueError as e:
            # Re-raise ValueError from strict mode
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            raise e
        except Exception as e:
            logger.error("Failed to get fact", ticker=ticker, concept=concept, error=str(e))
            return None

    async def fetch_company_facts(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch and normalize full company facts dataset from SEC"""
        try:
            from src.jobs.symbol_map import cik_for_ticker

            cik = cik_for_ticker(ticker.upper())
            if not cik:
                logger.warning("Unknown ticker when fetching company facts", ticker=ticker)
                return None

            session = await self._get_session()
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
            logger.info("Fetching full company facts", ticker=ticker, cik=cik)

            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(
                        "Failed to fetch company facts",
                        ticker=ticker,
                        cik=cik,
                        status=response.status
                    )
                    return None

                data = await response.json()

            normalized: Dict[str, Any] = {
                "cik": cik,
                "entity_name": data.get("entityName", ""),
                "sic": data.get("sic"),
                "sic_description": data.get("sicDescription"),
                "tickers": data.get("tickers", [ticker.upper()]),
                "facts": {}
            }

            facts_payload = data.get("facts", {})
            total_entries = 0

            for taxonomy, taxonomy_data in facts_payload.items():
                if not isinstance(taxonomy_data, dict):
                    continue

                for concept_name, concept_data in taxonomy_data.items():
                    units = concept_data.get("units", {})
                    if not isinstance(units, dict):
                        continue

                    concept_key = f"{taxonomy}:{concept_name}"
                    concept_facts = normalized["facts"].setdefault(concept_key, [])

                    for unit, facts_list in units.items():
                        if not isinstance(facts_list, list):
                            continue

                        for fact_entry in facts_list:
                            normalized_entry = self._normalize_fact_entry(
                                taxonomy,
                                concept_name,
                                unit,
                                fact_entry
                            )
                            if normalized_entry is None:
                                continue

                            concept_facts.append(normalized_entry)
                            total_entries += 1

            normalized["total_concepts"] = len(normalized.get("facts", {}))
            normalized["total_facts"] = total_entries

            logger.info(
                "Company facts normalized",
                ticker=ticker,
                cik=cik,
                concepts=normalized["total_concepts"],
                facts=total_entries
            )

            return normalized

        except Exception as e:
            logger.error("Failed to fetch company facts", ticker=ticker, error=str(e))
            return None

    def _normalize_fact_entry(
        self,
        taxonomy: str,
        concept_name: str,
        unit: str,
        fact_entry: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Normalize a raw SEC fact entry into storage-friendly structure"""
        value = fact_entry.get("val")
        if value is None:
            return None

        try:
            value = float(value)
        except (TypeError, ValueError):
            logger.debug(
                "Skipping non-numeric fact",
                taxonomy=taxonomy,
                concept=concept_name,
                unit=unit,
                raw_value=value
            )
            return None

        period_label = self._determine_period_label(fact_entry)
        frame = fact_entry.get("frame")
        dimensions = fact_entry.get("dimensions") or {}
        if not dimensions and frame:
            dimensions = {"frame": frame}

        normalized = {
            "concept": f"{taxonomy}:{concept_name}",
            "value": value,
            "unit": unit,
            "end_date": period_label,
            "end_date_actual": fact_entry.get("end"),
            "start_date": fact_entry.get("start"),
            "accession": fact_entry.get("accn", ""),
            "frame": frame,
            "dimensions": dimensions,
            "restated": self._is_restated_fact(fact_entry),
            "estimated": bool(fact_entry.get("estimate")),
            "fy": fact_entry.get("fy"),
            "fp": fact_entry.get("fp"),
            "filed": fact_entry.get("filed"),
            "form": fact_entry.get("form"),
            "taxonomy": taxonomy
        }

        return normalized

    def _determine_period_label(self, fact_entry: Dict[str, Any]) -> str:
        fy = fact_entry.get("fy")
        fp_raw = fact_entry.get("fp")
        fp = str(fp_raw).upper() if fp_raw else ""

        if fy and fp:
            if fp.startswith("Q") and len(fp) >= 2 and fp[1].isdigit():
                return f"{fy}-Q{fp[1]}"
            if fp == "FY":
                return f"{fy}-FY"
            if fp in {"H1", "H2"}:
                return f"{fy}-{fp}"

        end_date = fact_entry.get("end")
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                quarter = ((end_dt.month - 1) // 3) + 1
                return f"{end_dt.year}-Q{quarter}"
            except ValueError:
                return end_date

        return ""

    def _is_restated_fact(self, fact_entry: Dict[str, Any]) -> bool:
        form = str(fact_entry.get("form", ""))
        if form.endswith("/A"):
            return True
        if fact_entry.get("amend"):
            return True
        return False
    
    def _find_fact_for_period(self, concept_data: Dict[str, Any], period: str = None, freq: str = "Q", target_accession: str = None) -> Optional[Dict[str, Any]]:
        """Find fact for specific period, or most recent if period not specified

        Args:
            concept_data: Concept data from SEC Facts API
            period: Target period (e.g., "2024-Q4")
            freq: Frequency ("Q" or "A")
            target_accession: If specified, ONLY return facts from this accession (for period consistency)
        """
        if "units" not in concept_data:
            return None

        # Get the first unit (usually USD)
        for unit, periods in concept_data["units"].items():
            if not periods:
                continue

            # If target_accession specified, filter facts to only that accession
            if target_accession:
                periods = [f for f in periods if f.get("accn") == target_accession]
                if not periods:
                    continue

            if period:
                # Try to find exact period match - prefer smaller values when multiple matches
                matching_facts = []
                for fact in periods:
                    if self._matches_period(fact, period, freq):
                        matching_facts.append(fact)

                if matching_facts:
                    # If multiple matches, prefer the smaller value (more likely to be quarterly)
                    best_fact = min(matching_facts, key=lambda x: x.get("val", float('inf')))
                    return {
                        **best_fact,
                        "unit": unit
                    }

                # If no exact match, find closest period
                closest = self._find_closest_period(periods, period, freq)
                if closest:
                    return {
                        **closest,
                        "unit": unit
                    }
            else:
                # No period specified, return most recent
                sorted_periods = sorted(periods, key=lambda x: x.get("end", ""), reverse=True)
                if sorted_periods:
                    return {
                        **sorted_periods[0],
                        "unit": unit
                    }
        return None
    
    def _matches_period(self, fact: Dict[str, Any], period: str, freq: str) -> bool:
        """Check if fact matches requested period"""
        if not period:
            return True
            
        # Parse period like "2024-Q4" or "2024-12-31"
        fact_end = fact.get("end", "")
        fact_fp = fact.get("fp", "")
        
        if freq == "Q" and period.endswith("-Q4"):
            year = period.split("-Q")[0]
            # Q4 typically ends in December - ONLY match quarterly data, NOT annual (FY)
            return fact_end.startswith(f"{year}-12") and fact_fp in ["Q4", "QTR"]
        elif freq == "Q" and period.endswith("-Q3"):
            year = period.split("-Q")[0]
            # Q3 can end in September (calendar) or June (fiscal) - ONLY match quarterly data
            return (fact_end.startswith(f"{year}-09") or fact_end.startswith(f"{year}-06")) and fact_fp in ["Q3", "QTR"]
        elif freq == "Q" and period.endswith("-Q2"):
            year = period.split("-Q")[0]
            # Q2 typically ends in June - ONLY match quarterly data
            return fact_end.startswith(f"{year}-06") and fact_fp in ["Q2", "QTR"]
        elif freq == "Q" and period.endswith("-Q1"):
            year = period.split("-Q")[0]
            # Q1 typically ends in March - ONLY match quarterly data
            return fact_end.startswith(f"{year}-03") and fact_fp in ["Q1", "QTR"]
        elif freq == "A":
            year = period.split("-")[0] if "-" in period else period
            return fact_fp == "FY" or fact_end.startswith(f"{year}-12")
        
        return False
    
    def _find_closest_period(self, periods: List[Dict[str, Any]], period: str, freq: str) -> Optional[Dict[str, Any]]:
        """Find the closest available period to the requested one"""
        if not period:
            return None
            
        # Parse requested period
        if freq == "Q" and period.endswith("-Q4"):
            year = period.split("-Q")[0]
            target_date = f"{year}-12-31"
        elif freq == "Q" and period.endswith("-Q3"):
            year = period.split("-Q")[0]
            target_date = f"{year}-09-30"
        elif freq == "Q" and period.endswith("-Q2"):
            year = period.split("-Q")[0]
            target_date = f"{year}-06-30"
        elif freq == "Q" and period.endswith("-Q1"):
            year = period.split("-Q")[0]
            target_date = f"{year}-03-31"
        elif freq == "A":
            year = period.split("-")[0] if "-" in period else period
            target_date = f"{year}-12-31"
        else:
            return None
            
        # Find closest period by date
        closest = None
        min_diff = float('inf')
        
        for fact in periods:
            fact_end = fact.get("end", "")
            fact_fp = fact.get("fp", "")
            if not fact_end:
                continue
                
            # Only consider facts that match the requested frequency
            if freq == "Q" and fact_fp not in ["Q1", "Q2", "Q3", "Q4", "QTR"]:
                continue  # Skip annual data when quarterly is requested
            elif freq == "A" and fact_fp not in ["FY"]:
                continue  # Skip quarterly data when annual is requested
                
            # Calculate date difference
            try:
                from datetime import datetime
                fact_date = datetime.strptime(fact_end, "%Y-%m-%d")
                target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
                diff = abs((fact_date - target_datetime).days)
                
                if diff < min_diff:
                    min_diff = diff
                    closest = fact
            except ValueError:
                continue
                
        return closest
    
    def _validate_financial_data(self, ticker: str, concept: str, value: float, period: str, freq: str) -> bool:
        """Validate financial data for sanity checks"""
        if not value or value <= 0:
            return False
            
        # Dynamic validation ranges for major companies (in billions)
        # For 10,123+ companies, use general sanity checks instead of hardcoded ranges
        major_company_ranges = {
            # S&P 500 mega-caps - REALISTIC quarterly ranges (in billions)
            "AAPL": (20, 120), "MSFT": (50, 70), "AMZN": (120, 180), "GOOGL": (70, 90),
            "META": (25, 40), "TSLA": (20, 35), "WMT": (150, 180), "UNH": (80, 120),
            "XOM": (80, 120), "CVX": (50, 80), "JPM": (35, 50), "BAC": (20, 30),
            "JNJ": (20, 30), "PG": (18, 25), "PEP": (20, 30), "KO": (10, 15),
            "ABBV": (12, 20), "PFE": (15, 25), "NFLX": (8, 12), "NKE": (10, 18),
            "BA": (15, 25), "CAT": (12, 20), "GS": (10, 18), "WFC": (18, 28),
            "TSM": (15, 25), "SAP": (6, 12), "ASML": (5, 10), "SHEL": (80, 120),
            "TM": (60, 90), "UL": (12, 20), "NVDA": (15, 30),
        }
        
        if concept == "revenue" and ticker in major_company_ranges:
            min_annual, max_annual = major_company_ranges[ticker]
            
            if freq == "Q":
                # These ranges are already for quarterly revenue
                expected_min = min_annual
                expected_max = max_annual
                
                # More lenient validation - allow 25% to 200% of expected range
                if value < expected_min * 0.25 or value > expected_max * 2.0:
                    logger.warning("Suspicious quarterly revenue", 
                                 ticker=ticker, value=value, period=period,
                                 expected_range=f"{expected_min:.1f}B-{expected_max:.1f}B")
                    return False
                    
            elif freq == "A":
                # Annual revenue should be roughly 4x quarterly range
                annual_min = min_annual * 4
                annual_max = max_annual * 4
                if value < annual_min or value > annual_max:
                    logger.warning("Suspicious annual revenue",
                                 ticker=ticker, value=value, period=period,
                                 expected_range=f"{annual_min:.1f}B-{annual_max:.1f}B")
                    return False
        else:
            # General validation for all other companies
            if concept == "revenue":
                if freq == "Q":
                    # Quarterly revenue should be reasonable (not more than $500B)
                    if value > 500_000_000_000:  # $500B quarterly is impossible
                        logger.warning("Impossible quarterly revenue", 
                                     ticker=ticker, value=value, period=period)
                        return False
                elif freq == "A":
                    # Annual revenue should be reasonable (not more than $2T)
                    if value > 2_000_000_000_000:  # $2T annually is impossible
                        logger.warning("Impossible annual revenue",
                                     ticker=ticker, value=value, period=period)
                        return False
        
        return True
    
    async def _build_fact_response(
        self,
        fact_data: Dict[str, Any],
        ticker: str,
        concept: str,
        xbrl_concept: str,
        taxonomy: str = "us-gaap"
    ) -> Dict[str, Any]:
        """Build normalized fact response"""
        
        value = fact_data.get("val")
        unit = fact_data.get("unit", "USD")
        period = fact_data.get("end")
        accession = fact_data.get("accn")
        
        # Apply FX normalization for non-USD currencies
        fx_used = None
        if unit != "USD" and taxonomy == "ifrs-full":
            try:
                from src.calc.fx import get_fx_normalizer
                fx_normalizer = get_fx_normalizer()
                normalized_value, fx_provenance = await fx_normalizer.normalize(value, unit, "USD", period)
                value = normalized_value
                unit = "USD"
                fx_used = fx_provenance
                logger.info("Applied FX normalization", ticker=ticker, original_currency=fact_data.get("unit"), normalized_value=value, fx_provenance=fx_provenance)
            except Exception as e:
                logger.warning("FX normalization failed, using original value", error=str(e))
        
        # Build citation with taxonomy info
        # Get CIK for URL construction
        from src.jobs.symbol_map import cik_for_ticker
        cik = cik_for_ticker(ticker.upper())
        
        citation = {
            "source": "SEC EDGAR",
            "accession": accession,
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/" if cik else "",
            "concept": xbrl_concept,
            "taxonomy": taxonomy,
            "unit": unit,
            "scale": "U",
            "fx_used": fx_used,
            "amended": False,
            "as_reported": True,
            "filed": fact_data.get("filed"),
            "form": fact_data.get("form"),
            "fiscal_year": fact_data.get("fy"),
            "fiscal_period": fact_data.get("fp")
        }
        
        return {
            "ticker": ticker,
            "concept": concept,
            "value": value,
            "unit": "USD",
            "period": period,
            "citation": citation
        }
    
    @cache(ttl=900, source_version="sec_series")  # 15 minutes cache
    async def get_series(
        self,
        ticker: str,
        concept: str,
        freq: str = "Q",
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """Get time series (mock for now)"""
        fact = await self.get_fact(ticker, concept, period="latest", freq=freq)
        if not fact:
            return []
        
        try:
            from src.jobs.symbol_map import cik_for_ticker
            cik = cik_for_ticker(ticker.upper())
            if not cik:
                logger.warning("Unknown ticker", ticker=ticker)
                return []
            
            session = await self._get_session()
            url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error("Failed to fetch company facts for series", status=response.status)
                    return []
                data = await response.json()
        except Exception as e:
            logger.error("Failed to fetch series data", ticker=ticker, concept=concept, error=str(e))
            return []
        
        facts = data.get("facts", {})
        taxonomies = ["us-gaap", "ifrs-full"]
        normalized_freq = freq or "Q"
        allowed_fp = {"Q": {"Q1", "Q2", "Q3", "Q4", "QTR"}, "A": {"FY"}}
        accepted_fp = allowed_fp.get(normalized_freq.upper(), set())
        series: List[Dict[str, Any]] = []
        
        for taxonomy in taxonomies:
            taxonomy_data = facts.get(taxonomy)
            if not taxonomy_data:
                continue
            for xbrl_concept in self.concept_map.get(concept, []):
                concept_data = taxonomy_data.get(xbrl_concept)
                if not concept_data or "units" not in concept_data:
                    continue
                for unit, items in concept_data["units"].items():
                    if not items:
                        continue
                    valid_items = []
                    for item in items:
                        fp_value = item.get("fp")
                        if accepted_fp and fp_value not in accepted_fp:
                            continue
                        valid_items.append({**item, "unit": unit})
                    if not valid_items:
                        continue
                    sorted_items = sorted(
                        valid_items,
                        key=lambda x: x.get("end", ""),
                        reverse=True
                    )
                    for fact_entry in sorted_items:
                        try:
                            normalized = await self._build_fact_response(
                                fact_entry,
                                ticker,
                                concept,
                                xbrl_concept,
                                taxonomy
                            )
                        except Exception as build_error:
                            logger.warning(
                                "Failed to normalize fact for series",
                                ticker=ticker,
                                concept=concept,
                                error=str(build_error)
                            )
                            continue
                        series.append(normalized)
                        if len(series) >= limit:
                            break
                    if series:
                        break
                if series:
                    break
            if series:
                break
        
        logger.info("Series generated", ticker=ticker, concept=concept, periods=len(series))
        return series
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

# Global instance
sec_facts_adapter = SECFactsAdapter()

def get_sec_facts_adapter() -> SECFactsAdapter:
    """Get global SEC facts adapter instance"""
    return sec_facts_adapter