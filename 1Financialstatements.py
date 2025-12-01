#!/usr/bin/env python
# coding: utf-8

# # EDGARTools Playground (Rav)
# 
# Interactive notebook to explore:
# 
# - Company metadata
# - Latest 10-K / 10-Q
# - Balance sheet / income statement / cash flow as DataFrames
# - Insider Form 4 filings
# 
# Requires:
# - `edgartools` installed (`pip install edgartools`)
# - A real email for SEC identity
# 

# In[45]:


# If edgartools is not installed in this environment, uncomment:
#!pip install edgartools

from edgar import *
from edgar.xbrl.xbrl import *
import pandas as pd

# 👇 IMPORTANT: use your real email (SEC user-agent requirement)
set_identity("kamboj.r@gmail.com")

pd.set_option("display.max_rows", 50)
pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 120)


# In[38]:


def normalize_statement(stmt):
    """
    Take whatever edgartools returns for a statement
    and turn it into a pandas DataFrame.

    Handles:
    - functions that must be called
    - objects with .get_dataframe()
    - objects with .to_pandas() / .to_dataframe()
    - a raw pandas DataFrame
    """
    # If it's callable (function/method), call it
    if callable(stmt):
        stmt = stmt()

    # Try common methods
    for attr in ("get_dataframe", "to_pandas", "to_dataframe"):
        if hasattr(stmt, attr):
            return getattr(stmt, attr)()

    # If it's already a DataFrame, just return it
    if isinstance(stmt, pd.DataFrame):
        return stmt

    # Last resort: show what we got
    raise TypeError(f"Unexpected statement type: {type(stmt)}")


# In[39]:


def get_latest_filing_obj(cik_or_ticker: str, form: str = "10-K"):
    """
    Returns the latest filing object (e.g. TenK / TenQ) for a given ticker/CIK.
    """
    company = Company(cik_or_ticker)
    filings = company.get_filings(form=form)
    latest = filings.latest(1).obj()
    return latest


# In[49]:


#Single, simple filing for 10-Q or 10-K

from edgar import *
from edgar.xbrl.xbrl import *

# Get a company's latest 10-K filing
#company = Company('MSFT')
#filing = company.latest("10-Q")

ticker = input("Enter ticker: ").upper().strip()
form_type = input("Enter 'q' for 10-Q or 'k' for 10-K: ").lower().strip()

# Convert shorthand to SEC form name
if form_type == "q":
    form = "10-Q"
elif form_type == "k":
    form = "10-K"
else:
    raise ValueError("Invalid input: must be 'q' or 'k'.")

from edgar import Company

company = Company('AAPL')
filing = company.latest('k')

print(f"Loaded latest {form} filing for {ticker}:")
print(filing)


# Parse XBRL data
xbrl = filing.xbrl()

# Access statements through the user-friendly API
statements = xbrl.statements

# Display financial statements
balance_sheet = statements.balance_sheet()
income_statement = statements.income_statement()
cash_flow = statements.cashflow_statement()

#Convert each statement to dataframes
balance_sheet_df = statements.balance_sheet()
income_stmt_df = statements.income_statement()
cash_flow_df = statements.cashflow_statement()

print(income_statement)
print(balance_sheet)
print(cash_flow)





# In[ ]:




