# modules/fix_float_columns.py
import pandas as pd
import numpy as np

def fix_float_columns(df, float_columns):
    """Fix float columns by converting empty strings to NaN"""
    df = df.copy()
    for col in float_columns:
        if col in df.columns:
            # Replace empty strings with NaN
            df[col] = df[col].replace('', np.nan)
            # Convert to nullable float
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].astype('Float64')
    return df

def clean_input_value(value):
    """Clean user input before assigning to float column"""
    if value is None or value == '' or pd.isna(value):
        return np.nan
    try:
        return float(value)
    except (ValueError, TypeError):
        return np.nan

def safe_float_assign(df, index, column, value):
    """Safely assign a value to a float column"""
    cleaned_value = clean_input_value(value)
    df.loc[index, column] = cleaned_value
    return df