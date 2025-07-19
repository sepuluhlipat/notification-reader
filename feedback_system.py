import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import streamlit as st
import json

class FeedbackSystem:
    def __init__(self, sheet_id=None):
        """
        Initialize the feedback system with Google Sheets integration
        
        Args:
            sheet_id: Google Sheet ID (from the URL)
        """
        self.sheet_id = sheet_id
        self.gc = None
        self.worksheet = None
        
    def get_credentials(self):
        """Get credentials from Streamlit secrets"""
        try:
            # Get the service account info from secrets
            service_account_info = dict(st.secrets["gcp_service_account"])
            
            # Create credentials from the service account info
            creds = Credentials.from_service_account_info(
                service_account_info,
                scopes=[
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            
            return creds
            
        except Exception as e:
            st.error(f"Failed to get credentials: {str(e)}")
            return None
        
    def connect_to_sheet(self):
        """Connect to Google Sheets"""
        try:
            # Get credentials
            creds = self.get_credentials()
            if not creds:
                return False
            
            # Authorize and connect
            self.gc = gspread.authorize(creds)
            
            # Open the sheet
            sheet = self.gc.open_by_key(self.sheet_id)
            self.worksheet = sheet.sheet1  # Use the first sheet
            
            return True
            
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {str(e)}")
            return False
    
    def submit_feedback(self, notification_data, parsed_category, correct_category, remarks, user_id, is_correct_prediction=None):
        """
        Submit feedback to Google Sheets
        
        Args:
            notification_data: Dict containing notification details
            parsed_category: Category that was parsed by the system
            correct_category: Correct category provided by user (can be same as parsed if correct)
            remarks: User remarks
            user_id: User identifier
            is_correct_prediction: Boolean indicating if the prediction was correct
        """
        if not self.connect_to_sheet():
            return False
            
        try:
            # Debug: Print the notification_data to see what's being passed
            print("Notification data being submitted:", notification_data)
            
            # Determine if prediction is correct
            if is_correct_prediction is None:
                is_correct_prediction = parsed_category.lower() == correct_category.lower()
            
            # Prepare the row data with the new column
            row_data = [
                datetime.now().isoformat(),  # timestamp
                str(notification_data.get('message', '')),  # notification_message
                str(notification_data.get('app_label', '')),  # app_label
                str(parsed_category),  # parsed_category
                str(correct_category) if not is_correct_prediction else "", # correct_category (empty if correct)
                str(remarks) if not is_correct_prediction else "",  # remarks (empty if correct)
                str(user_id),  # user_id
                "Yes" if is_correct_prediction else "No"  # correct_prediction
            ]
            
            # Debug: Print the row data
            print("Row data being submitted:", row_data)
            
            # Append the row to the sheet
            self.worksheet.append_row(row_data)
            
            return True
            
        except Exception as e:
            st.error(f"Failed to submit feedback: {str(e)}")
            print(f"Error details: {e}")
            return False

    def initialize_sheet_headers(self):
        """Initialize the sheet with proper headers if it's empty"""
        if not self.connect_to_sheet():
            return False
            
        try:
            # Check if sheet has headers
            all_values = self.worksheet.get_all_values()
            if not all_values:
                # Sheet is empty, add headers with the new column
                headers = [
                    'timestamp',
                    'notification_message',
                    'app_label',
                    'parsed_category',
                    'correct_category',
                    'remarks',
                    'user_id',
                    'correct_prediction'  # New column
                ]
                self.worksheet.append_row(headers)
                return True
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize sheet headers: {str(e)}")
            return False