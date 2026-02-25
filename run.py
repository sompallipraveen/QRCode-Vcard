#!/usr/bin/env python3
"""
Tally Trial Balance Extractor
Aligned with FinancialReview.tsx data structure

Usage: python tally_tb_extractor.py --from 01-04-2024 --to 31-03-2025
"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
import hashlib
import argparse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class TallyTrialBalanceLine:
    """
    Matches: useTallyODBC.ts -> TallyTrialBalanceLine interface
    """
    accountHead: str
    openingBalance: float
    totalDebit: float
    totalCredit: float
    closingBalance: float
    accountCode: str
    branch: str
    primaryGroup: str
    parent: str
    isRevenue: bool


@dataclass
class LedgerRow:
    """
    Matches: FinancialReview.tsx -> LedgerRow interface
    Used for classified trial balance display
    """
    ledger_name: str           # 'Ledger Name'
    primary_group: str         # 'Primary Group'
    parent_group: str          # 'Parent Group'
    composite_key: str         # 'Composite Key'
    opening_balance: float     # 'Opening Balance'
    debit: float               # 'Debit'
    credit: float              # 'Credit'
    closing_balance: float     # 'Closing Balance'
    abs_opening_balance: float # 'ABS Opening Balance'
    abs_closing_balance: float # 'ABS Closing Balance'
    is_revenue: str            # 'Is Revenue' - 'Yes' or 'No'
    h1: str = ''               # 'H1' - Asset, Liability, Income, Expense
    h2: str = ''               # 'H2' - Note group
    h3: str = ''               # 'H3' - Sub-note
    notes: str = ''            # 'Notes'
    sheet_name: str = 'TB CY'  # 'Sheet Name'
    auto: str = ''             # 'Auto'
    auto_reason: str = ''      # 'Auto Reason'
    
    def to_excel_dict(self) -> dict:
        """Convert to Excel-compatible dictionary with original column names"""
        return {
            'Ledger Name': self.ledger_name,
            'Primary Group': self.primary_group,
            'Parent Group': self.parent_group,
            'Composite Key': self.composite_key,
            'Opening Balance': self.opening_balance,
            'Debit': self.debit,
            'Credit': self.credit,
            'Closing Balance': self.closing_balance,
            'ABS Opening Balance': self.abs_opening_balance,
            'ABS Closing Balance': self.abs_closing_balance,
            'Is Revenue': self.is_revenue,
            'H1': self.h1,
            'H2': self.h2,
            'H3': self.h3,
            'Notes': self.notes,
            'Sheet Name': self.sheet_name,
        }


def generate_ledger_key(ledger_name: str, primary_group: str) -> str:
    """
    Matches: generateLedgerKey() from trialBalanceNewClassification.ts
    Creates a unique composite key for each ledger
    """
    combined = f"{ledger_name.strip().lower()}|{primary_group.strip().lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def derive_h1_from_revenue_and_balance(is_revenue: bool, closing_balance: float, opening_balance: float) -> str:
    """
    Matches: deriveH1FromRevenueAndBalance() from FinancialReview.tsx
    Determines H1 classification based on revenue flag and balance sign
    """
    sign_value = closing_balance if closing_balance != 0 else opening_balance
    is_debit = sign_value < 0
    
    if is_revenue:
        return 'Expense' if is_debit else 'Income'
    else:
        return 'Asset' if is_debit else 'Liability'


class TallyConnector:
    """
    Tally HTTP/XML API Connector
    Matches the data flow in useTallyODBC.ts
    """
    
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.base_url = f"http://{host}:{port}"
        self.company_name: Optional[str] = None
    
    def test_connection(self) -> bool:
        """
        Matches: testConnection() in useTallyODBC.ts
        """
        try:
            xml_request = """
            <ENVELOPE>
                <HEADER>
                    <VERSION>1</VERSION>
                    <TALLYREQUEST>Export</TALLYREQUEST>
                    <TYPE>Function</TYPE>
                    <ID>$$CurrentCompany</ID>
                </HEADER>
                <BODY></BODY>
            </ENVELOPE>
            """
            response = requests.post(
                self.base_url,
                data=xml_request,
                headers={"Content-Type": "application/xml"},
                timeout=10
            )
            
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                self.company_name = root.text.strip() if root.text else None
                return True
            return False
            
        except requests.exceptions.ConnectionError:
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def fetch_trial_balance(
        self, 
        from_date: str, 
        to_date: str
    ) -> tuple[List[TallyTrialBalanceLine], str]:
        """
        Matches: fetchTrialBalance() in useTallyODBC.ts
        
        Args:
            from_date: DD-MM-YYYY format (e.g., "01-04-2024")
            to_date: DD-MM-YYYY format (e.g., "31-03-2025")
        
        Returns:
            Tuple of (list of TallyTrialBalanceLine, company_name)
        """
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>TrialBalanceCollection</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        <SVFROMDATE>{from_date}</SVFROMDATE>
                        <SVTODATE>{to_date}</SVTODATE>
                    </STATICVARIABLES>
                    <TDL>
                        <TDLMESSAGE>
                            <COLLECTION NAME="TrialBalanceCollection" ISMODIFY="No">
                                <TYPE>Ledger</TYPE>
                                <NATIVEMETHOD>Name</NATIVEMETHOD>
                                <NATIVEMETHOD>Parent</NATIVEMETHOD>
                                <NATIVEMETHOD>OpeningBalance</NATIVEMETHOD>
                                <NATIVEMETHOD>ClosingBalance</NATIVEMETHOD>
                                <NATIVEMETHOD>IsRevenue</NATIVEMETHOD>
                            </COLLECTION>
                            
                            <PART NAME="TBExport">
                                <TOPPARTS>TBExport</TOPPARTS>
                                <XMLTAG>ENVELOPE</XMLTAG>
                            </PART>
                            
                            <LINE NAME="TBLine">
                                <FIELDS>FldName, FldParent, FldPrimaryGroup</FIELDS>
                                <FIELDS>FldOpening, FldDebit, FldCredit, FldClosing</FIELDS>
                                <FIELDS>FldIsRevenue</FIELDS>
                            </LINE>
                            
                            <FIELD NAME="FldName">
                                <SET>$Name</SET>
                                <XMLTAG>LEDGERNAME</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldParent">
                                <SET>$Parent</SET>
                                <XMLTAG>PARENT</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldPrimaryGroup">
                                <SET>$$PrimaryGroup:$Name</SET>
                                <XMLTAG>PRIMARYGROUP</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldOpening">
                                <SET>$OpeningBalance</SET>
                                <XMLTAG>OPENINGBALANCE</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldDebit">
                                <SET>$$TotDebit:$Name</SET>
                                <XMLTAG>TOTALDEBIT</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldCredit">
                                <SET>$$TotCredit:$Name</SET>
                                <XMLTAG>TOTALCREDIT</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldClosing">
                                <SET>$ClosingBalance</SET>
                                <XMLTAG>CLOSINGBALANCE</XMLTAG>
                            </FIELD>
                            
                            <FIELD NAME="FldIsRevenue">
                                <SET>$IsRevenue</SET>
                                <XMLTAG>ISREVENUE</XMLTAG>
                            </FIELD>
                        </TDLMESSAGE>
                    </TDL>
                </DESC>
            </BODY>
        </ENVELOPE>
        """
        
        try:
            response = requests.post(
                self.base_url,
                data=xml_request,
                headers={"Content-Type": "application/xml"},
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP Error: {response.status_code}")
            
            lines = self._parse_tally_response(response.text)
            return lines, self.company_name or ''
            
        except Exception as e:
            print(f"Error fetching trial balance: {e}")
            return [], ''
    
    def _parse_tally_response(self, xml_text: str) -> List[TallyTrialBalanceLine]:
        """
        Parse Tally XML response into TallyTrialBalanceLine objects
        """
        lines = []
        
        try:
            root = ET.fromstring(xml_text)
            
            # Find all LEDGER elements
            for ledger in root.findall('.//LEDGER'):
                name = (
                    ledger.findtext('LEDGERNAME') or 
                    ledger.findtext('NAME') or 
                    ''
                ).strip()
                
                if not name:
                    continue
                
                parent = (ledger.findtext('PARENT') or '').strip()
                primary_group = (ledger.findtext('PRIMARYGROUP') or '').strip()
                
                opening = self._parse_amount(ledger.findtext('OPENINGBALANCE', '0'))
                debit = self._parse_amount(ledger.findtext('TOTALDEBIT', '0'))
                credit = self._parse_amount(ledger.findtext('TOTALCREDIT', '0'))
                closing = self._parse_amount(ledger.findtext('CLOSINGBALANCE', '0'))
                
                is_revenue_text = (ledger.findtext('ISREVENUE') or 'No').strip().lower()
                is_revenue = is_revenue_text in ('yes', 'true', '1')
                
                lines.append(TallyTrialBalanceLine(
                    accountHead=name,
                    openingBalance=opening,
                    totalDebit=abs(debit),
                    totalCredit=abs(credit),
                    closingBalance=closing,
                    accountCode='',
                    branch='',
                    primaryGroup=primary_group or parent,
                    parent=parent,
                    isRevenue=is_revenue
                ))
        
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            print(f"Response preview: {xml_text[:500]}...")
        
        return lines
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        Parse Tally amount string to float
        Handles formats like "1,00,000.00 Dr" or "50,000.00 Cr"
        """
        if not amount_str:
            return 0.0
        
        cleaned = amount_str.replace(',', '').replace(' ', '').strip()
        
        # Determine sign from Dr/Cr suffix
        # Dr = Debit (negative in Tally convention for assets)
        # Cr = Credit (positive in Tally convention for liabilities)
        is_credit = cleaned.endswith('Cr') or cleaned.endswith('Cr.')
        is_debit = cleaned.endswith('Dr') or cleaned.endswith('Dr.')
        
        # Remove suffix
        cleaned = cleaned.rstrip('DrCr. ')
        
        try:
            value = float(cleaned)
            # Apply sign: Credits are negative (liabilities/income), Debits are positive (assets/expenses)
            # This matches Tally's convention used in your React code
            if is_credit:
                value = -value
            return value
        except ValueError:
            return 0.0


def process_tally_lines_to_ledger_rows(
    lines: List[TallyTrialBalanceLine],
    period_type: str = 'current'
) -> List[LedgerRow]:
    """
    Matches: handleFetchFromTally() transformation in FinancialReview.tsx
    
    Converts TallyTrialBalanceLine to LedgerRow format
    """
    ledger_rows = []
    
    for line in lines:
        # Generate composite key (matches generateLedgerKey)
        composite_key = generate_ledger_key(line.accountHead, line.primaryGroup)
        
        # Derive H1 classification (matches deriveH1FromRevenueAndBalance)
        h1 = derive_h1_from_revenue_and_balance(
            line.isRevenue,
            line.closingBalance,
            line.openingBalance
        )
        
        ledger_row = LedgerRow(
            ledger_name=line.accountHead,
            primary_group=line.primaryGroup,
            parent_group=line.parent,
            composite_key=composite_key,
            opening_balance=line.openingBalance,
            debit=abs(line.totalDebit),
            credit=abs(line.totalCredit),
            closing_balance=line.closingBalance,
            abs_opening_balance=abs(line.openingBalance),
            abs_closing_balance=abs(line.closingBalance),
            is_revenue='Yes' if line.isRevenue else 'No',
            h1=h1,
            sheet_name='TB CY' if period_type == 'current' else 'TB PY'
        )
        
        ledger_rows.append(ledger_row)
    
    return ledger_rows


def filter_classified_rows(rows: List[LedgerRow]) -> List[LedgerRow]:
    """
    Matches: filterClassifiedRows() from FinancialReview.tsx
    Filters out rows where both opening and closing are zero
    """
    return [
        row for row in rows
        if row.opening_balance != 0 or row.closing_balance != 0
    ]


def export_to_excel(
    rows: List[LedgerRow],
    filename: str,
    include_all_columns: bool = True
):
    """
    Export LedgerRows to Excel matching the React app's export format
    """
    if include_all_columns:
        data = [row.to_excel_dict() for row in rows]
    else:
        # Minimal columns for actual TB
        data = [{
            'Ledger Name': row.ledger_name,
            'Parent Group': row.parent_group,
            'Primary Group': row.primary_group,
            'Opening Balance': row.opening_balance,
            'Debit': row.debit,
            'Credit': row.credit,
            'Closing Balance': row.closing_balance,
            'Is Revenue': row.is_revenue,
        } for row in rows]
    
    df = pd.DataFrame(data)
    
    # Sort by Primary Group, then Ledger Name (similar to React sorting)
    df = df.sort_values(['Primary Group', 'Ledger Name'])
    
    # Export with formatting
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Trial Balance', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Trial Balance']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            col_letter = chr(65 + idx) if idx < 26 else f"{chr(65 + idx // 26 - 1)}{chr(65 + idx % 26)}"
            worksheet.column_dimensions[col_letter].width = min(max_length, 50)
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description='Extract Trial Balance from Tally (aligned with FinancialReview.tsx)'
    )
    parser.add_argument(
        '--from', 
        dest='from_date', 
        default='01-04-2024',
        help='Start date DD-MM-YYYY (default: 01-04-2024)'
    )
    parser.add_argument(
        '--to', 
        dest='to_date', 
        default='31-03-2025',
        help='End date DD-MM-YYYY (default: 31-03-2025)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=9000,
        help='Tally ODBC port (default: 9000)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Tally host (default: localhost)'
    )
    parser.add_argument(
        '--output', 
        default=None,
        help='Output Excel filename'
    )
    parser.add_argument(
        '--period',
        choices=['current', 'previous'],
        default='current',
        help='Period type for sheet naming (default: current)'
    )
    parser.add_argument(
        '--filter-zero',
        action='store_true',
        help='Filter out zero balance rows'
    )
    
    args = parser.parse_args()
    
    # Initialize connector
    tally = TallyConnector(host=args.host, port=args.port)
    
    # Test connection
    print(f"🔗 Connecting to Tally at {args.host}:{args.port}...")
    if not tally.test_connection():
        print("❌ Cannot connect to Tally. Please ensure:")
        print("   1. Tally is running")
        print("   2. F12 > Advanced Configuration > Allow ODBC/XML Server = Yes")
        print(f"   3. ODBC Server Port = {args.port}")
        return
    
    print(f"✅ Connected to Tally!")
    if tally.company_name:
        print(f"📊 Company: {tally.company_name}")
    
    # Fetch Trial Balance
    print(f"\n📅 Fetching Trial Balance: {args.from_date} to {args.to_date}")
    
    tally_lines, company_name = tally.fetch_trial_balance(args.from_date, args.to_date)
    
    if not tally_lines:
        print("❌ No data returned. Check if company has transactions in this period.")
        return
    
    print(f"✅ Fetched {len(tally_lines)} ledgers from Tally")
    
    # Process to LedgerRow format (matching React app)
    ledger_rows = process_tally_lines_to_ledger_rows(tally_lines, args.period)
    
    # Filter zero balance rows if requested
    if args.filter_zero:
        ledger_rows = filter_classified_rows(ledger_rows)
        print(f"📋 After filtering zeros: {len(ledger_rows)} ledgers")
    
    # Generate filename
    if args.output:
        filename = args.output
    else:
        company_safe = (company_name or 'Unknown').replace(' ', '_').replace('/', '-')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        period_label = 'CY' if args.period == 'current' else 'PY'
        filename = f"TrialBalance_{company_safe}_{period_label}_{timestamp}.xlsx"
    
    # Export
    df = export_to_excel(ledger_rows, filename, include_all_columns=True)
    print(f"\n💾 Exported to: {filename}")
    
    # Summary (matching React totals bar)
    print("\n" + "=" * 50)
    print("📊 SUMMARY (matches TotalsBar in React)")
    print("=" * 50)
    print(f"   Total Ledgers:     {len(df)}")
    print(f"   Opening Balance:   ₹{df['Opening Balance'].sum():>15,.2f}")
    print(f"   Total Debits:      ₹{df['Debit'].sum():>15,.2f}")
    print(f"   Total Credits:     ₹{df['Credit'].sum():>15,.2f}")
    print(f"   Closing Balance:   ₹{df['Closing Balance'].sum():>15,.2f}")
    print("=" * 50)
    
    # Group summary
    if 'H1' in df.columns:
        print("\n📈 By H1 Classification:")
        h1_summary = df.groupby('H1')['Closing Balance'].sum()
        for h1, total in h1_summary.items():
            if h1:
                print(f"   {h1:15} ₹{total:>15,.2f}")


if __name__ == "__main__":
    main()