"""
Data processing utilities for transaction parsing.

This module contains functions for processing notification data from DataFrames
and testing with raw CSV input.
"""

import pandas as pd
import io
import os
from ..core.parser import NotificationParser
from ..core.models import BlacklistError


def process_notification_data(df, patterns_file=os.path.join('dictionary', 'regex_patterns.json')):
    """
    Process notifications dataframe to extract structured transaction data.
    
    Args:
        df (pd.DataFrame): DataFrame containing notification data with columns:
            - MESSAGE: Notification message text
            - CONTENTS: Notification content text
            - ID: Unique identifier for the notification
            - TIMESTAMP: When the notification was received
            - APP LABEL: Name/label of the app that sent the notification
        patterns_file (str): Path to regex patterns JSON file
    
    Returns:
        pd.DataFrame: DataFrame containing extracted transaction data
    
    Raises:
        Exception: If there are errors processing individual rows
    """
    parser = NotificationParser(patterns_file)
    results = []
    blacklisted_count = 0
    
    for _, row in df.iterrows():
        try:
            # Extract and clean row data
            message = str(row.get('MESSAGE', '')) if pd.notna(row.get('MESSAGE')) else ""
            contents = str(row.get('CONTENTS', '')) if pd.notna(row.get('CONTENTS')) else ""
            id_val = str(row.get('ID', 'unknown_id')) if pd.notna(row.get('ID')) else "unknown_id"
            timestamp = row.get('TIMESTAMP') if pd.notna(row.get('TIMESTAMP')) else None
            app_name = str(row.get('APP LABEL', '')) if pd.notna(row.get('APP LABEL')) else ""
            
            # Parse the notification
            transaction = parser.parse_notification(message, contents, id_val, timestamp, app_name)
            results.append(transaction.to_dict())
        
        except BlacklistError as e:
            blacklisted_count += 1
            continue
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
        
    print(f"Processed {len(results)} transactions, skipped {blacklisted_count} blacklisted apps")
    return pd.DataFrame(results)


def test_raw_csv_input(raw_input, patterns_file=os.path.join('dictionary', 'regex_patterns.json')):
    """
    Test notifications using raw CSV input without headers.
    
    This function is useful for testing the parser with CSV data that doesn't
    have column headers. It assumes a specific column order.
    
    Args:
        raw_input (str): Raw CSV string data
        patterns_file (str): Path to regex patterns JSON file
    
    Returns:
        list: List of dictionaries containing parsed transaction data.
              Returns list with error dict if parsing fails.
    
    Example:
        >>> csv_data = "1,com.app,AppName,Payment received,2024-01-01,Amount: $100,2024-01-01T10:00:00"
        >>> result = test_raw_csv_input(csv_data)
        >>> print(result[0]['amount'])  # Should print the extracted amount
    """
    try:
        # Define expected column order for headerless CSV
        column_names = ['ID', 'PACKAGE NAME', 'APP LABEL', 'MESSAGE', 'DATE', 'CONTENTS', 'TIMESTAMP']
        
        # Ensure the input ends with a newline for proper CSV parsing
        if '\n' not in raw_input:
            raw_input += '\n'
            
        # Parse CSV without headers
        df = pd.read_csv(io.StringIO(raw_input), names=column_names, header=None)
        
        # Process using the main processing function
        result_df = process_notification_data(df, patterns_file)
        
        # Convert to list of dictionaries for easier handling
        return [row.to_dict() for _, row in result_df.iterrows()]
        
    except Exception as e:
        return [{"error": f"Failed to parse CSV: {str(e)}"}]


def validate_dataframe_columns(df, required_columns=None):
    """
    Validate that a DataFrame has the required columns for processing.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        required_columns (list): List of required column names.
                               Defaults to standard notification columns.
    
    Returns:
        tuple: (is_valid, missing_columns)
    
    Example:
        >>> is_valid, missing = validate_dataframe_columns(df)
        >>> if not is_valid:
        ...     print(f"Missing columns: {missing}")
    """
    if required_columns is None:
        required_columns = ['MESSAGE', 'CONTENTS', 'ID', 'TIMESTAMP', 'APP LABEL']
    
    df_columns = set(df.columns)
    required_set = set(required_columns)
    missing_columns = required_set - df_columns
    
    return len(missing_columns) == 0, list(missing_columns)


def clean_transaction_dataframe(df):
    """
    Clean and standardize a transaction DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df_clean = df.copy()
    
    # Convert timestamp to datetime if it's a string
    if 'timestamp' in df_clean.columns:
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], errors='coerce')
    
    # Ensure amount is numeric
    if 'amount' in df_clean.columns:
        df_clean['amount'] = pd.to_numeric(df_clean['amount'], errors='coerce')
    
    # Fill empty categories with 'other'
    if 'category' in df_clean.columns:
        df_clean['category'] = df_clean['category'].fillna('other')
    
    # Remove rows with no amount (likely failed parsing)
    if 'amount' in df_clean.columns:
        df_clean = df_clean.dropna(subset=['amount'])
    
    return df_clean


def get_processing_summary(original_count, processed_df, blacklisted_count=0):
    """
    Generate a summary of the processing results.
    
    Args:
        original_count (int): Number of original notifications
        processed_df (pd.DataFrame): Processed transaction DataFrame
        blacklisted_count (int): Number of blacklisted notifications skipped
    
    Returns:
        dict: Summary statistics
    """
    processed_count = len(processed_df)
    failed_count = original_count - processed_count - blacklisted_count
    
    summary = {
        'original_notifications': original_count,
        'processed_transactions': processed_count,
        'blacklisted_skipped': blacklisted_count,
        'failed_processing': failed_count,
        'success_rate': (processed_count / original_count * 100) if original_count > 0 else 0
    }
    
    # Add transaction type breakdown if available
    if 'transaction_type' in processed_df.columns:
        type_counts = processed_df['transaction_type'].value_counts().to_dict()
        summary['transaction_types'] = type_counts
    
    # Add category breakdown if available
    if 'category' in processed_df.columns:
        category_counts = processed_df['category'].value_counts().to_dict()
        summary['categories'] = category_counts
    
    return summary