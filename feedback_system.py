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
    
    def submit_feedback(self, notification_data, parsed_category, correct_category, remarks, user_id):
        """
        Submit feedback to Google Sheets
        
        Args:
            notification_data: Dict containing notification details
            parsed_category: Category that was parsed by the system
            correct_category: Correct category provided by user
            remarks: User remarks
            user_id: User identifier
        """
        if not self.connect_to_sheet():
            return False
            
        try:
            # Debug: Print the notification_data to see what's being passed
            print("Notification data being submitted:", notification_data)
            
            # Prepare the row data with better error handling
            row_data = [
                datetime.now().isoformat(),  # timestamp
                str(notification_data.get('message', '')),  # notification_message
                str(notification_data.get('contents', '')),  # notification_contents
                str(notification_data.get('app_label', '')),  # app_label
                str(notification_data.get('package_name', '')),  # package_name
                str(parsed_category),  # parsed_category
                str(correct_category),  # correct_category
                str(remarks),  # remarks
                str(user_id)  # user_id
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
    
    def get_feedback_data(self):
        """Get all feedback data from the sheet"""
        if not self.connect_to_sheet():
            return None
            
        try:
            # Get all records
            records = self.worksheet.get_all_records()
            return pd.DataFrame(records)
            
        except Exception as e:
            st.error(f"Failed to retrieve feedback data: {str(e)}")
            return None

    def initialize_sheet_headers(self):
        """Initialize the sheet with proper headers if it's empty"""
        if not self.connect_to_sheet():
            return False
            
        try:
            # Check if sheet has headers
            all_values = self.worksheet.get_all_values()
            if not all_values:
                # Sheet is empty, add headers
                headers = [
                    'timestamp',
                    'notification_message',
                    'notification_contents',
                    'app_label',
                    'package_name',
                    'parsed_category',
                    'correct_category',
                    'remarks',
                    'user_id'
                ]
                self.worksheet.append_row(headers)
                return True
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize sheet headers: {str(e)}")
            return False