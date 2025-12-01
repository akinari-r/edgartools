"""
Single-cell friendly helper for Jupyter:
- Prompts (interactive input) for ticker and filing type (k = annual 10-K, q = quarterly 10-Q)
- Fetches the latest filing, parses XBRL, returns DataFrames for balance sheet, income statement, cash flow
- Handles library-specific Statement objects by attempting common conversion methods or converting to DataFrame
- Prints short summary and returns the three DataFrames

Usage (Jupyter):
- Paste this whole cell into one notebook cell and run.
- Follow the prompts in the notebook cell output.
"""
from typing import Tuple, Optional, Any
import pandas as pd

# adapt import paths to your repo layout
try:
    from edgar import Company
    from edgar.xbrl.xbrl import XBRL  # not strictly required, kept for clarity
except Exception:
    # If imports differ in your environment adjust them
    raise

def _prompt_ticker() -> str:
    while True:
        t = input("Enter ticker (e.g. AAPL): ").strip().upper()
        if t:
            return t
        print("Ticker cannot be empty. Try again.")

def _prompt_freq() -> str:
    """
    Ask user for 'k' (annual 10-K) or 'q' (quarterly 10-Q).
    Returns the filing type string used by Company.latest().
    """
    while True:
        s = input("Choose filing type — k = annual (10-K), q = quarterly (10-Q) [k/q]: ").strip().lower()
        if s in ("k", "10-k", "10k", "annual"):
            return "10-K"
        if s in ("q", "10-q", "10q", "quarterly"):
            return "10-Q"
        print("Invalid choice. Enter 'k' or 'q'.")

def ensure_dataframe(obj: Any, name: str = "object") -> pd.DataFrame:
    """
    Try to coerce various statement objects into a pandas DataFrame.
    Strategy:
      - if already DataFrame, return it
      - try common conversion methods: to_frame, to_dataframe, to_df, to_pandas, as_dataframe
      - if list/tuple/dict try pd.DataFrame(...)
      - as last resort, try pd.json_normalize on __dict__
    Raises TypeError if conversion fails.
    """
    if isinstance(obj, pd.DataFrame):
        return obj

    if obj is None:
        raise TypeError(f"{name} is None")

    # common conversion method names
    for meth in ("to_frame", "to_dataframe", "to_df", "to_pandas", "as_dataframe", "as_df", "as_pandas"):
        fn = getattr(obj, meth, None)
        if callable(fn):
            try:
                res = fn()
                if isinstance(res, pd.DataFrame):
                    return res
                # if returns records, attempt DataFrame conversion
                if isinstance(res, (list, dict, tuple)):
                    return pd.DataFrame(res)
            except Exception:
                # ignore and continue trying other methods
                pass

    # attributes that might contain tabular representation
    for attr in ("df", "data", "dataframe", "table", "rows", "items", "statements"):
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if isinstance(val, pd.DataFrame):
                return val
            if isinstance(val, (list, dict, tuple)):
                return pd.DataFrame(val)

    # list/tuple/dict conversion
    if isinstance(obj, (list, tuple, dict)):
        try:
            return pd.DataFrame(obj)
        except Exception:
            pass

    # try json normalize on __dict__
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict) and d:
        try:
            return pd.json_normalize(d)
        except Exception:
            pass

    # fallback - show helpful diagnostics to user
    raise TypeError(
        f"{name} is a {type(obj)} and could not be converted automatically to DataFrame.\n"
        f"Inspect with: print(type({name})); print(dir({name})); print(repr({name})[:400])\n"
        f"Common fix: call the object's conversion method (e.g. {name}.to_frame()) before passing it here."
    )

def fetch_and_prepare_statements(ticker: str, filing_type: str, prefer_edgar: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Fetches the latest filing of the given type for the ticker and returns DataFrames:
      (balance_sheet_df, income_stmt_df, cash_flow_df_or_None)
    """
    # Build Company and get latest filing
    company = Company(ticker)
    filing = company.latest(filing_type)  # filing_type: "10-K" or "10-Q"
    if filing is None:
        raise RuntimeError(f"No latest {filing_type} filing found for {ticker}")

    # parse XBRL (many implementations use filing.xbrl() to parse)
    xb = filing.xbrl()
    statements = xb.statements

    # statements.balance_sheet() etc may already be DataFrames or Statement objects
    bs_obj = statements.balance_sheet()
    is_obj = statements.income_statement()
    cf_obj = None
    # cashflow may be named cashflow_statement or cash_flow; try both
    try:
        cf_obj = statements.cashflow_statement()
    except Exception:
        if hasattr(statements, "cash_flow") and callable(getattr(statements, "cash_flow")):
            cf_obj = statements.cash_flow()
        else:
            cf_obj = None

    # coerce to DataFrames
    bs_df = ensure_dataframe(bs_obj, "balance_sheet")
    is_df = ensure_dataframe(is_obj, "income_statement")
    cf_df = ensure_dataframe(cf_obj, "cash_flow") if cf_obj is not None else None

    # Normalize index/period handling: if 'period' column exists make it the index and cast to str
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        if "period" in df.columns:
            df = df.set_index("period")
        df.index = df.index.astype(str)
        return df

    bs_df = _normalize(bs_df)
    is_df = _normalize(is_df)
    if cf_df is not None:
        cf_df = _normalize(cf_df)

    return bs_df, is_df, cf_df

def interactive_fetch_and_show():
    """
    Single-cell interactive flow: prompt, fetch, convert, and print brief summaries.
    Returns the three DataFrames for further use in the same notebook cell.
    """
    ticker = _prompt_ticker()
    filing_type = _prompt_freq()  # "10-K" or "10-Q"
    print(f"Fetching {filing_type} for {ticker} ...")
    bs_df, is_df, cf_df = fetch_and_prepare_statements(ticker, filing_type)
    print("\nBalance sheet (columns):", list(bs_df.columns))
    print("Income statement (columns):", list(is_df.columns))
    if cf_df is not None:
        print("Cash flow (columns):", list(cf_df.columns))
    else:
        print("Cash flow: None")

    # show small head previews
    print("\nBalance sheet preview:")
    display(bs_df.head())  # display works in Jupyter
    print("\nIncome statement preview:")
    display(is_df.head())
    if cf_df is not None:
        print("\nCash flow preview:")
        display(cf_df.head())

    # return for reuse in notebook
    return bs_df, is_df, cf_df

# If running as a script, call interactive helper; in notebook paste and run the cell and call interactive_fetch_and_show()
if __name__ == "__main__":
    interactive_fetch_and_show()