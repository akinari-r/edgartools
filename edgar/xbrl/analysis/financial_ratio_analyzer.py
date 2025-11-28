from typing import List, NamedTuple
import pandas as pd


class RatioResult(NamedTuple):
    name: str
    period: str
    result: float


class FinancialRatioAnalyzer:
    """
    Simple ratio analyzer that expects pandas DataFrames for balance sheet,
    income statement, and cash flow. Each DataFrame should either have a
    'period' column or use its index to identify periods.

    Example expected columns:
      - balance_sheet_df: ['period', 'current_assets', 'current_liabilities', 'total_assets']
      - income_stmt_df: ['period', 'net_income']
    """

    def __init__(self, balance_sheet_df: pd.DataFrame, income_stmt_df: pd.DataFrame,
                 cash_flow_df: pd.DataFrame = None, periods: List[str] = None):
        # Save inputs
        self.balance_sheet = balance_sheet_df.copy()
        self.income_stmt = income_stmt_df.copy()
        self.cash_flow = None if cash_flow_df is None else cash_flow_df.copy()

        # Normalize period column -> index for easier joins
        for df in (self.balance_sheet, self.income_stmt, self.cash_flow) if self.cash_flow is not None else (self.balance_sheet, self.income_stmt):
            if df is None:
                continue
            if "period" in df.columns:
                df.set_index("period", inplace=True)

        # If caller passed explicit periods, use them; otherwise use intersection of indexes
        if periods is not None:
            self.periods = list(periods)
        else:
            # use intersection of available periods to avoid mismatches
            bs_periods = set(self.balance_sheet.index.astype(str))
            is_periods = set(self.income_stmt.index.astype(str))
            common = sorted(bs_periods & is_periods)
            self.periods = common

    def _require_columns(self, df: pd.DataFrame, cols: List[str], df_name: str):
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{df_name} missing columns: {missing}")

    def calculate_current_ratio(self) -> List[RatioResult]:
        """
        Current Ratio = Current Assets / Current Liabilities
        Returns a list of RatioResult for each available period.
        """
        self._require_columns(self.balance_sheet, ["current_assets", "current_liabilities"], "balance_sheet")
        results: List[RatioResult] = []

        for period in self.periods:
            if period not in self.balance_sheet.index.astype(str):
                # skip periods not present
                continue
            row = self.balance_sheet.loc[str(period)]
            try:
                current_assets = float(row["current_assets"])
                current_liabilities = float(row["current_liabilities"])
            except (KeyError, TypeError, ValueError):
                # skip if values invalid
                continue

            if current_liabilities == 0:
                ratio_val = float("inf")
            else:
                ratio_val = current_assets / current_liabilities
            results.append(RatioResult(name="Current Ratio", period=str(period), result=ratio_val))

        return results

    def calculate_return_on_assets(self) -> List[RatioResult]:
        """
        ROA = Net Income / Total Assets
        """
        self._require_columns(self.income_stmt, ["net_income"], "income_stmt")
        self._require_columns(self.balance_sheet, ["total_assets"], "balance_sheet")
        results: List[RatioResult] = []

        for period in self.periods:
            if (period not in self.income_stmt.index.astype(str)) or (period not in self.balance_sheet.index.astype(str)):
                continue
            ni_row = self.income_stmt.loc[str(period)]
            bs_row = self.balance_sheet.loc[str(period)]

            try:
                net_income = float(ni_row["net_income"])
                total_assets = float(bs_row["total_assets"])
            except (KeyError, TypeError, ValueError):
                continue

            if total_assets == 0:
                roa = float("inf")
            else:
                roa = net_income / total_assets
            results.append(RatioResult(name="Return on Assets", period=str(period), result=roa))

        return results