import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from notification_reader import process_notification_data, NotificationParser, BlacklistError, AllowlistError
from feedback_system import FeedbackSystem

GOOGLE_SHEET_ID = "1E-yEi6C38Ju5tZPgom-MNY5dC5UmOtxSckQrdTq9dAE"
FEEDBACK_SYSTEM = FeedbackSystem(sheet_id=GOOGLE_SHEET_ID)

# Set page config
st.set_page_config(
    page_title="Transaction Parser Dashboard",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .instruction-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        border: none;
    }
    .instruction-box h3 {
        color: #ffffff;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .instruction-box p {
        color: #f0f0f0;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    .instruction-box ol {
        color: #f0f0f0;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .instruction-box ol li {
        margin-bottom: 0.5rem;
        padding-left: 0.5rem;
    }
    .instruction-box a {
        color: #ffd700;
        text-decoration: none;
        font-weight: bold;
    }
    .instruction-box a:hover {
        color: #ffed4e;
        text-decoration: underline;
    }
    .test-section {
        border: 2px solid #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .single-result {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sample-button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    .highlight-banner {
        background: linear-gradient(90deg, #ff6b6b, #ffa500, #32cd32, #1e90ff);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 1rem 0;
        animation: glow 2s ease-in-out infinite alternate;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    @keyframes glow {
        from { box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        to { box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
    }
    .failure-reason {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .failure-reason h4 {
        color: #856404;
        margin-bottom: 0.5rem;
    }
    .solution-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }
    .solution-box h4 {
        color: #0c5460;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">💰 Transaction Parser Dashboard</h1>', unsafe_allow_html=True)

# Highlighted banner
st.markdown("""
<div class="highlight-banner">
    🎯 Help Us Train Our AI! Test Your Transaction Notifications Below 👇
</div>
""", unsafe_allow_html=True)

# Instructions section with better visibility
st.markdown("""
<div class="instruction-box">
<h3>🚀 Help Us Train Our AI From Your Notifications</h3>
<p>We're building an engine (patent pending) that reads your spending notifications — and auto-detects the <strong>merchant, amount, and category</strong>.</p>
<p>To make it smarter, we need real examples. Here's how you can help:</p>
<ol>
<li>📲 Install this app to <strong>record your push notifications</strong> (stored privately on your phone): 👉 <a href="https://play.google.com/store/apps/details?id=com.argonremote.notificationhistory" target="_blank">https://play.google.com/store/apps/details?id=com.argonremote.notificationhistory</a></li>
<li>Use your phone as usual — let notifications come in naturally.</li>
<li>When you spot a <strong>transaction-related notification</strong>, <strong>tap it in the app and copy the text</strong>.</li>
<li>Paste it into our engine here: 👉 <a href="https://notification-reader-imkdavmoew4hp3ys4ngkzo.streamlit.app/" target="_blank">https://notification-reader-imkdavmoew4hp3ys4ngkzo.streamlit.app/</a></li>
<li>💬 After seeing how it gets categorized, give your feedback <strong>directly in the same page</strong>.</li>
</ol>
<p>Every example helps improve accuracy and brings us closer to effortless personal finance tracking.</p>
<p><strong>Thanks for being part of the journey 🙌</strong></p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'single_test_result' not in st.session_state:
    st.session_state.single_test_result = None
if 'parsing_failure_reason' not in st.session_state:
    st.session_state.parsing_failure_reason = None
if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = False
if 'failed_feedback_submitted' not in st.session_state:
    st.session_state.failed_feedback_submitted = False
if 'current_notification_data' not in st.session_state:
    st.session_state.current_notification_data = None
if 'test_inputs' not in st.session_state:
    st.session_state.test_inputs = {
        'message': '',
        'app_label': ''
    }
if 'suggested_feedback' not in st.session_state:
    st.session_state.suggested_feedback = None

# Check if default files exist
default_dict_exists = os.path.exists("dictionary.json")
default_patterns_exists = os.path.exists("regex_patterns.json")

# Set default file paths
dictionary_file_path = "dictionary.json" if default_dict_exists else None
patterns_file_path = "regex_patterns.json" if default_patterns_exists else None
config_files_ready = default_dict_exists and default_patterns_exists

# Show configuration status
if not config_files_ready:
    st.error("⚠️ Configuration files missing. Please ensure dictionary.json and regex_patterns.json are available.")
    st.stop()

def get_suggested_feedback(reason_code, reason_description, message, app_label):
    """
    Generate suggested feedback based on the failure reason
    """
    suggestions = {
        "promotional_message": {
            "category": "Marketing/Promotional",
            "remarks": f"This was incorrectly identified as promotional content. It's actually a transaction notification from {app_label}. Please update the promotional detection patterns."
        },
        "no_amount_found": {
            "category": "Unknown - Amount Detection Issue",
            "remarks": f"No amount could be extracted from the message. The amount format might not be supported: '{message[:100]}...'. Please update amount extraction patterns."
        },
        "invalid_amount": {
            "category": "Unknown - Invalid Amount",
            "remarks": f"The amount extracted was zero or negative. Please check the amount extraction logic for this format: '{message[:100]}...'"
        },
        "app_not_allowlisted": {
            "category": "Unknown - New App",
            "remarks": f"The app '{app_label}' is not in the allowlist. Please add this app to the processing list if it's a financial app."
        },
        "app_blacklisted": {
            "category": "Unknown - Blacklisted App",
            "remarks": f"The app '{app_label}' is blacklisted. If this is actually a financial app, please remove it from the blacklist."
        },
        "unknown_transaction_type": {
            "category": "Unknown - Transaction Type",
            "remarks": f"Could not determine if this is income, expense, or transfer. The message may need clearer transaction indicators: '{message[:100]}...'"
        },
        "unknown_error": {
            "category": "Unknown - System Error",
            "remarks": f"Parsing failed for unknown reasons. Please investigate this message format: '{message[:100]}...'"
        }
    }
    
    return suggestions.get(reason_code, {
        "category": "Unknown",
        "remarks": f"Parsing failed: {reason_description}. Please provide the correct category and help us understand this transaction format."
    })

def diagnose_parsing_failure(message, contents, app_label, parser):
    """
    Diagnose why parsing failed and return specific reason
    """
    full_text = f"{message} {contents}"
    
    # Check if app is allowlisted
    if not parser._is_app_allowlisted(app_label):
        return "app_not_allowlisted", f"App '{app_label}' is not in the allowlist"
    
    # Check if app is blacklisted  
    if parser._is_app_blacklisted(app_label):
        return "app_blacklisted", f"App '{app_label}' is blacklisted"
    
    # Check if promotional
    if parser._is_promotional_message(full_text):
        return "promotional_message", "Message was detected as promotional/marketing content"
    
    # Check if amount can be extracted
    amount = parser.extract_amount(full_text)
    if amount is None:
        return "no_amount_found", "No valid amount could be extracted from the message"
    
    if amount <= 0:
        return "invalid_amount", f"Amount found ({amount}) is zero or negative"
    
    # Check transaction type
    transaction_type = parser.extract_transaction_type(full_text)
    if transaction_type.value == "unknown":
        return "unknown_transaction_type", "Transaction type could not be determined"
    
    # If we reach here, parsing should have succeeded
    return "unknown_error", "Parsing failed for unknown reasons"

# Single notification testing section
st.markdown('<div class="test-section">', unsafe_allow_html=True)
st.subheader("🧪 Test Your Notification")
st.write("Paste your notification details below to see how our AI categorizes it.")

col1, col2 = st.columns([2, 1])

with col1:
    # Input fields for single notification
    st.write("**Enter notification details:**")
    
    # Use session state for persistent inputs
    test_message = st.text_area(
        "Notification Message",
        value=st.session_state.test_inputs['message'],
        placeholder="Enter the notification message text here...",
        help="The actual notification message content",
        height=150,
        key="input_message"
    )
    
    test_app_label = st.text_input(
        "App Label",
        value=st.session_state.test_inputs['app_label'],
        placeholder="e.g., myBCA, GoPay",
        help="The app name/label",
        key="input_app_label"
    )
    
    # Update session state when inputs change
    st.session_state.test_inputs['message'] = test_message
    st.session_state.test_inputs['app_label'] = test_app_label
    
    # Test button
    if st.button("🧪 Test Notification", type="primary"):
        if test_message.strip():
            # Store the current notification data in session state BEFORE processing
            st.session_state.current_notification_data = {
                'message': test_message,
                'contents': '',
                'app_label': test_app_label,
                'package_name': '',
                'user_id': 'tester',
                'notification_id': f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Reset failure reason and suggested feedback
            st.session_state.parsing_failure_reason = None
            st.session_state.suggested_feedback = None
                
            with st.spinner("Testing notification..."):
                try:
                    # Create parser instance for diagnosis
                    parser = NotificationParser(dictionary_file_path, patterns_file_path)
                    
                    # Create a single-row DataFrame for testing
                    test_df = pd.DataFrame({
                        'id': [st.session_state.current_notification_data['notification_id']],
                        'package_name': ["unknown"],
                        'app_label': [test_app_label or "unknown"],
                        'message': [test_message],
                        'contents': [""],
                        'timestamp': [datetime.now().isoformat()],
                        'user_id': ['tester']
                    })
                    
                    # Process the single notification
                    result_df = process_notification_data(
                        test_df,
                        dictionary_file_path,
                        patterns_file_path,
                        filter_promotional=True
                    )
                    
                    st.session_state.single_test_result = result_df
                    
                    if not result_df.empty:
                        st.success("✅ Notification processed successfully!")
                    else:
                        st.warning("⚠️ No transaction data extracted from this notification")
                        
                        # Diagnose why parsing failed
                        reason_code, reason_description = diagnose_parsing_failure(
                            test_message, "", test_app_label, parser
                        )
                        st.session_state.parsing_failure_reason = {
                            'code': reason_code,
                            'description': reason_description
                        }
                        
                        # Generate suggested feedback
                        st.session_state.suggested_feedback = get_suggested_feedback(
                            reason_code, reason_description, test_message, test_app_label
                        )
                    
                except Exception as e:
                    st.error(f"❌ Error processing notification: {str(e)}")
                    st.exception(e)
                    st.session_state.parsing_failure_reason = {
                        'code': 'processing_error',
                        'description': f"Error during processing: {str(e)}"
                    }
                    st.session_state.suggested_feedback = get_suggested_feedback(
                        'processing_error', f"Error during processing: {str(e)}", test_message, test_app_label
                    )
        else:
            st.warning("⚠️ Please enter a notification message to test")

with col2:
    # Sample notifications for testing
    st.write("**Sample Notifications:**")
    st.write("Click to use as test input")
    
    sample_data = [
        {
            "message": "Catatan Finansial. Pengeluaran sebesar IDR 6,500.00 di kategori Biaya Admin.",
            "app_label": "myBCA",
            "description": "BCA Admin Fee"
        },
        {
            "message": "Catatan Finansial. Pengeluaran sebesar IDR 10,000,000.00 di kategori Transfer Rekening.",
            "app_label": "myBCA",
            "description": "BCA Transfer"
        },
        {
            "message": "Payment successful! Awesome, you just paid Rp10.000 to DAIRY QUEEN - MALL KELAPA dana.",
            "app_label": "GoPay",
            "description": "GoPay Payment"
        }
    ]
    
    for i, sample in enumerate(sample_data):
        if st.button(f"📱 {sample['description']}", key=f"sample_{i}", help=sample['message'][:50] + "..."):
            # Update session state inputs directly
            st.session_state.test_inputs['message'] = sample['message']
            st.session_state.test_inputs['app_label'] = sample['app_label']
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Display single test results
if st.session_state.single_test_result is not None:
    st.subheader("🔍 Test Results")
    
    result_data = st.session_state.single_test_result
    
    if not result_data.empty:
        # Display parsed transaction details
        st.markdown('<div class="single-result">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Amount", f"${result_data.iloc[0]['amount']:.2f}")
        
        with col2:
            st.metric("Transaction Type", result_data.iloc[0]['transaction_type'])
        
        with col3:
            parsed_category = result_data.iloc[0]['category']
            st.metric("Category", parsed_category)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show detailed parsing results
        st.subheader("Detailed Parsing Results")
        # Select relevant columns for display
        display_columns = ['transaction_type', 'amount', 'category', 'account_number', 'timestamp']
        display_data = result_data[[col for col in display_columns if col in result_data.columns]]
        st.dataframe(display_data, use_container_width=True)
        
        # Feedback Section
        st.subheader("📝 Help Us Improve")
        st.write("Is the parsed category correct? Your feedback helps us train our AI!")
        
        # Check if feedback was just submitted
        if st.session_state.get('feedback_submitted', False):
            st.success("✅ Thank you! Your feedback has been submitted successfully.")
            st.session_state.feedback_submitted = False
        
        # Create columns for feedback form
        feedback_col1, feedback_col2 = st.columns([2, 1])
        
        with feedback_col1:
            # Check if category is correct
            is_correct = st.radio(
                "Is the parsed category correct?",
                ["✅ Yes, it's correct", "❌ No, it's wrong"],
                key="category_feedback"
            )
            
            if is_correct == "❌ No, it's wrong":
                # Input for correct category
                correct_category = st.text_input(
                    "What should be the correct category?",
                    placeholder="e.g., Food & Dining, Transportation, Shopping, etc.",
                    key="correct_category"
                )
                
                # Remarks
                remarks = st.text_area(
                    "Additional remarks (optional)",
                    placeholder="Any additional comments about this transaction...",
                    key="feedback_remarks"
                )
                
                # Submit feedback button
                if st.button("📤 Submit Feedback", type="primary"):
                    if correct_category.strip():
                        # Use the stored notification data from session state
                        if st.session_state.current_notification_data:
                            notification_data = st.session_state.current_notification_data
                            
                            # Submit feedback
                            with st.spinner("Submitting feedback..."):
                                success = FEEDBACK_SYSTEM.submit_feedback(
                                    notification_data=notification_data,
                                    parsed_category=parsed_category,
                                    correct_category=correct_category,
                                    remarks=remarks,
                                    user_id=notification_data.get('user_id', 'tester')
                                )
                                
                                if success:
                                    st.success("✅ Thank you! Your feedback has been submitted.")
                                    st.balloons()
                                    # Set a flag to show success message and reset form
                                    st.session_state.feedback_submitted = True
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to submit feedback. Please try again.")
                        else:
                            st.error("❌ No notification data available. Please test a notification first.")
                    else:
                        st.warning("⚠️ Please enter the correct category.")
            else:
                st.success("✅ Great! The parser is working correctly for this transaction.")
        
        with feedback_col2:
            st.info(
                "**Help us improve!** 🚀\n\n"
                "Your feedback helps us:\n"
                "- Improve category detection\n"
                "- Add new transaction patterns\n"
                "- Fix parsing errors\n"
                "- Better understand spending habits"
            )
        
        # Download single result
        single_csv = result_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Test Result",
            data=single_csv,
            file_name=f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        # Show specific failure reason and solution
        if st.session_state.parsing_failure_reason:
            failure_reason = st.session_state.parsing_failure_reason
            
            # Display failure reason
            st.markdown('<div class="failure-reason">', unsafe_allow_html=True)
            st.markdown(f"<h4>❌ Why parsing failed:</h4>", unsafe_allow_html=True)
            
            reason_code = failure_reason['code']
            reason_description = failure_reason['description']
            
            st.write(f"**Issue:** {reason_description}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display solution
            st.markdown('<div class="solution-box">', unsafe_allow_html=True)
            st.markdown(f"<h4>💡 How to help us fix this:</h4>", unsafe_allow_html=True)
            
            # Display specific solutions with aligned explanations
            if reason_code == "promotional_message":
                st.write("**Solution:** If this is actually a transaction (not promotional content), please provide feedback below. We'll use your input to improve our promotional detection system.")
            elif reason_code == "no_amount_found":
                st.write("**Solution:** The system couldn't find a valid monetary amount. Please provide feedback below with the correct category, and we'll improve our amount detection patterns.")
            elif reason_code == "invalid_amount":
                st.write("**Solution:** The amount found was zero or negative. Please provide feedback below to help us fix the amount extraction logic.")
            elif reason_code == "app_not_allowlisted":
                st.write("**Solution:** This app isn't in our financial apps list. Please provide feedback below if this is a banking/financial app, and we'll add it to our system.")
            elif reason_code == "app_blacklisted":
                st.write("**Solution:** This app is currently blocked. Please provide feedback below if this app actually sends financial notifications, and we'll review our blacklist.")
            elif reason_code == "unknown_transaction_type":
                st.write("**Solution:** We couldn't determine if this is income, expense, or transfer. Please provide feedback below with the correct category to help us improve transaction type detection.")
            elif reason_code == "processing_error":
                st.write("**Solution:** A technical error occurred. Please provide feedback below with the correct category, and we'll investigate the issue.")
            else:
                st.write("**Solution:** Please provide feedback below with the correct category and any additional details to help us understand this transaction format.")
            
            st.write("**👇 Your feedback below will help us fix this specific issue.**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Feedback for failed parsing with auto-filled suggestions
        st.subheader("📝 Help Us Learn From This Failure")
        st.write("This notification couldn't be parsed. Your feedback will help us improve!")
        
        # Check if feedback was just submitted
        if st.session_state.get('failed_feedback_submitted', False):
            st.success("✅ Thank you! Your feedback has been submitted successfully.")
            st.session_state.failed_feedback_submitted = False
        
        # Use suggested feedback if available
        suggested_category = ""
        suggested_remarks = ""
        
        if st.session_state.suggested_feedback:
            suggested_category = st.session_state.suggested_feedback.get('category', '')
            suggested_remarks = st.session_state.suggested_feedback.get('remarks', '')
        
        # Show auto-filled suggestion info
        if suggested_category or suggested_remarks:
            st.info("💡 **Auto-filled suggestions based on the failure analysis** - Feel free to modify these suggestions:")
        
        expected_category = st.text_input(
            "What category should this transaction be?",
            value=suggested_category,
            placeholder="e.g., Food & Dining, Transportation, Shopping, etc.",
            key="failed_category",
            help="This field has been auto-filled based on the failure analysis. Please modify if needed."
        )
        
        failed_remarks = st.text_area(
            "Additional details about this transaction:",
            value=suggested_remarks,
            placeholder="e.g., New transaction format, missing keywords, different language, etc.",
            key="failed_remarks",
            help="This field has been auto-filled with diagnostic information. Please add any additional details."
        )
        
        if st.button("📤 Submit Feedback for Failed Parsing", type="primary"):
            if expected_category.strip():
                # Use the stored notification data from session state
                if st.session_state.current_notification_data:
                    notification_data = st.session_state.current_notification_data
                    
                    # Add specific failure reason to remarks if not already included
                    combined_remarks = failed_remarks
                    if st.session_state.parsing_failure_reason and not suggested_remarks:
                        failure_info = st.session_state.parsing_failure_reason
                        combined_remarks = f"Failure reason: {failure_info['description']}\n\nUser remarks: {failed_remarks}"
                    
                    with st.spinner("Submitting feedback..."):
                        success = FEEDBACK_SYSTEM.submit_feedback(
                            notification_data=notification_data,
                            parsed_category="PARSING_FAILED",
                            correct_category=expected_category,
                            remarks=combined_remarks,
                            user_id=notification_data.get('user_id', 'tester')
                        )
                        
                        if success:
                            st.success("✅ Thank you! Your feedback has been submitted.")
                            st.balloons()
                            # Set flag for feedback submission
                            st.session_state.failed_feedback_submitted = True
                            st.rerun()
                        else:
                            st.error("❌ Failed to submit feedback. Please try again.")
                else:
                    st.error("❌ No notification data available. Please test a notification first.")
            else:
                st.warning("⚠️ Please enter the expected category.")

# Footer
st.markdown("---")
st.markdown(
    "💡 **Tip:** The more examples you provide, the smarter our AI becomes at categorizing your transactions!"
)
