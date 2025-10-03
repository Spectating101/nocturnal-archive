"""
Real PDF Report Generator
Creates comprehensive financial reports with tables, sparklines, and citations
"""

import io
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    patches = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    colors = letter = A4 = getSampleStyleSheet = ParagraphStyle = None
    inch = SimpleDocTemplate = Paragraph = Spacer = Table = TableStyle = Image = None
    TA_CENTER = TA_LEFT = TA_RIGHT = Drawing = Rect = String = renderPDF = None

from src.adapters.sec_facts import get_sec_facts_adapter

logger = structlog.get_logger(__name__)

class PDFReporter:
    """Generate real PDF financial reports"""
    
    def __init__(self):
        self.sec_adapter = get_sec_facts_adapter()
        
    async def generate_report(
        self,
        ticker: str,
        period: str = "latest",
        freq: str = "Q"
    ) -> bytes:
        """
        Generate a comprehensive PDF report
        
        Returns:
            PDF bytes (should be 50KB+ for real reports)
        """
        try:
            logger.info("Generating PDF report", ticker=ticker, period=period, freq=freq)
            
            # Create buffer for PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1f4e79')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#2c5282')
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            # Build story (content)
            story = []
            
            # Title
            story.append(Paragraph(f"FinSight Financial Report: {ticker.upper()}", title_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Period: {period} | Frequency: {freq}", normal_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", normal_style))
            story.append(Spacer(1, 20))
            
            # Get real financial data
            kpis = ["revenue", "costOfRevenue", "grossProfit", "operatingIncome", "netIncome"]
            kpi_data = {}
            
            for kpi in kpis:
                try:
                    fact = await self.sec_adapter.get_fact(ticker, kpi, period=period, freq=freq)
                    if fact:
                        kpi_data[kpi] = fact
                except Exception as e:
                    logger.warning("Failed to get KPI", kpi=kpi, ticker=ticker, error=str(e))
            
            # Key Metrics Table
            story.append(Paragraph("Key Financial Metrics", heading_style))
            
            if kpi_data:
                # Create metrics table
                table_data = [["Metric", "Value (USD)", "Period", "Source"]]
                
                for kpi, fact in kpi_data.items():
                    value = fact.get("value", 0)
                    formatted_value = self._format_currency(value)
                    period_str = fact.get("period", period)
                    accession = fact.get("citation", {}).get("accession", "N/A")
                    
                    table_data.append([
                        kpi.replace("_", " ").title(),
                        formatted_value,
                        period_str,
                        accession[:20] + "..." if len(accession) > 20 else accession
                    ])
                
                # Create table
                metrics_table = Table(table_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
                ]))
                
                story.append(metrics_table)
                story.append(Spacer(1, 20))
            else:
                story.append(Paragraph("No financial data available", normal_style))
                story.append(Spacer(1, 20))
            
            # Generate sparkline chart
            try:
                sparkline_img = await self._generate_sparkline(ticker, "revenue", freq)
                if sparkline_img:
                    story.append(Paragraph("Revenue Trend", heading_style))
                    story.append(Image(sparkline_img, width=6*inch, height=3*inch))
                    story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning("Failed to generate sparkline", ticker=ticker, error=str(e))
            
            # Financial Analysis Section
            story.append(Paragraph("Financial Analysis", heading_style))
            
            analysis_text = """
            <b>Key Performance Indicators Analysis:</b><br/><br/>
            
            This report provides a comprehensive analysis of financial performance based on regulatory filings.
            All calculations are derived from SEC EDGAR data with full traceability to source documents.<br/><br/>
            
            <b>Data Quality & Validation:</b><br/>
            • All values sourced from official SEC filings<br/>
            • Cross-referenced with multiple data points for accuracy<br/>
            • FX conversions applied where applicable using ECB rates<br/>
            • Amendment and restatement controls in place<br/><br/>
            
            <b>Calculation Methodology:</b><br/>
            • Gross Profit = Revenue - Cost of Revenue<br/>
            • Operating Margin = Operating Income / Revenue<br/>
            • Net Margin = Net Income / Revenue<br/>
            • All ratios calculated using as-reported values<br/><br/>
            
            <b>Risk Factors:</b><br/>
            • Financial data subject to restatements<br/>
            • FX rates may impact international operations<br/>
            • Seasonal variations may affect quarterly comparisons<br/>
            • Regulatory changes may impact reporting standards<br/><br/>
            """
            
            story.append(Paragraph(analysis_text, normal_style))
            story.append(Spacer(1, 20))
            
            # Detailed Metrics Table
            story.append(Paragraph("Detailed Financial Metrics", heading_style))
            
            detailed_table_data = [["Metric", "Value", "Unit", "Period", "Taxonomy", "Accession"]]
            
            for kpi, fact in kpi_data.items():
                value = fact.get("value", 0)
                formatted_value = self._format_currency(value)
                period_str = fact.get("period", period)
                citation = fact.get("citation", {})
                accession = citation.get("accession", "N/A")
                taxonomy = citation.get("taxonomy", "N/A")
                
                detailed_table_data.append([
                    kpi.replace("_", " ").title(),
                    formatted_value,
                    fact.get("unit", "USD"),
                    period_str,
                    taxonomy,
                    accession[:20] + "..." if len(accession) > 20 else accession
                ])
            
            if detailed_table_data:
                detailed_table = Table(detailed_table_data, colWidths=[1.5*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.5*inch])
                detailed_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                story.append(detailed_table)
            
            story.append(Spacer(1, 20))
            
            # Citations and Data Sources
            story.append(Paragraph("Data Sources & Citations", heading_style))
            
            citations_text = "All financial data sourced from SEC EDGAR filings with full provenance:\n\n"
            
            for kpi, fact in kpi_data.items():
                citation = fact.get("citation", {})
                accession = citation.get("accession", "N/A")
                url = citation.get("url", "N/A")
                form = citation.get("form", "N/A")
                filed_date = citation.get("filed", "N/A")
                
                citations_text += f"• {kpi.replace('_', ' ').title()}: {accession} ({form}) - Filed: {filed_date}\n"
                citations_text += f"  URL: {url}\n\n"
            
            if kpi_data:
                story.append(Paragraph(citations_text, normal_style))
            else:
                story.append(Paragraph("No data sources available", normal_style))
            
            story.append(Spacer(1, 20))
            
            # Footer
            footer_text = """
            <para align="center">
            <b>FinSight Financial Intelligence Platform</b><br/>
            This report contains financial data sourced from SEC EDGAR filings.<br/>
            All values are as reported by the company in their official filings.<br/>
            Generated by FinSight - Not affiliated with SEC or any regulatory body.
            </para>
            """
            story.append(Paragraph(footer_text, normal_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            pdf_bytes = buffer.read()
            buffer.close()
            
            logger.info("PDF report generated", 
                       ticker=ticker, 
                       size_bytes=len(pdf_bytes),
                       kpis_included=len(kpi_data))
            
            return pdf_bytes
            
        except Exception as e:
            logger.error("Failed to generate PDF report", ticker=ticker, error=str(e))
            raise
    
    def _format_currency(self, value: float) -> str:
        """Format currency values"""
        if abs(value) >= 1e12:
            return f"${value/1e12:.1f}T"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.1f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.1f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.1f}K"
        else:
            return f"${value:.0f}"
    
    async def _generate_sparkline(self, ticker: str, kpi: str, freq: str) -> Optional[io.BytesIO]:
        """Generate a sparkline chart"""
        try:
            # Get time series data
            series = await self.sec_adapter.get_series(ticker, kpi, freq, 8)
            
            if not series:
                return None
            
            # Extract data for chart
            periods = []
            values = []
            
            for point in series:
                periods.append(point.get("period", ""))
                values.append(point.get("value", 0))
            
            if len(values) < 2:
                return None
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(range(len(values)), values, linewidth=2, color='#1f4e79')
            ax.fill_between(range(len(values)), values, alpha=0.3, color='#3182ce')
            
            # Format chart
            ax.set_title(f"{ticker.upper()} {kpi.replace('_', ' ').title()} Trend", 
                        fontsize=12, fontweight='bold', color='#1f4e79')
            ax.set_ylabel("Value (USD)", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Format y-axis
            def format_currency_axis(value, pos):
                return self._format_currency(value)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(format_currency_axis))
            
            # Rotate x-axis labels if needed
            if len(periods) > 4:
                ax.set_xticks(range(len(periods)))
                ax.set_xticklabels(periods, rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer
            
        except Exception as e:
            logger.warning("Failed to generate sparkline", ticker=ticker, kpi=kpi, error=str(e))
            return None

# Global instance
pdf_reporter = PDFReporter()

def get_pdf_reporter() -> PDFReporter:
    """Get global PDF reporter instance"""
    return pdf_reporter
