import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from notification_reader import process_notification_data, NotificationParser, BlacklistError, AllowlistError

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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .upload-section {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
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
    .config-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">💰 Transaction Parser Dashboard</h1>', unsafe_allow_html=True)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'config_files_ready' not in st.session_state:
    st.session_state.config_files_ready = False
if 'dictionary_file_path' not in st.session_state:
    st.session_state.dictionary_file_path = "dictionary.json"
if 'patterns_file_path' not in st.session_state:
    st.session_state.patterns_file_path = "regex_patterns.json"
if 'single_test_result' not in st.session_state:
    st.session_state.single_test_result = None
if 'use_custom_dictionary' not in st.session_state:
    st.session_state.use_custom_dictionary = False
if 'use_custom_patterns' not in st.session_state:
    st.session_state.use_custom_patterns = False

# Sidebar for configuration
st.sidebar.header("Configuration")

# Check if default files exist
default_dict_exists = os.path.exists("dictionary.json")
default_patterns_exists = os.path.exists("regex_patterns.json")

# Configuration Files Section
st.sidebar.subheader("📁 Configuration Files")

# Dictionary Configuration
st.sidebar.markdown('<div class="config-section">', unsafe_allow_html=True)
st.sidebar.markdown("**Dictionary Configuration**")

# Dictionary toggle
use_custom_dict = st.sidebar.toggle(
    "Use Custom Dictionary",
    value=st.session_state.use_custom_dictionary,
    key="dict_toggle",
    help="Toggle to use custom dictionary file instead of default"
)
st.session_state.use_custom_dictionary = use_custom_dict

# Dictionary file handling
if use_custom_dict:
    # Custom dictionary upload
    dictionary_file = st.sidebar.file_uploader(
        "Upload Custom Dictionary JSON",
        type=['json'],
        key="dictionary_upload",
        help="Upload your custom dictionary file"
    )
    
    if dictionary_file:
        # Save custom dictionary file
        with open("temp_dictionary.json", "w", encoding='utf-8') as f:
            f.write(dictionary_file.getvalue().decode('utf-8'))
        st.session_state.dictionary_file_path = "temp_dictionary.json"
        st.sidebar.success("✅ Custom dictionary uploaded!")
    else:
        st.sidebar.warning("⚠️ Please upload a custom dictionary file")
        st.session_state.dictionary_file_path = None
else:
    # Use default dictionary
    if default_dict_exists:
        st.session_state.dictionary_file_path = "dictionary.json"
        st.sidebar.success("✅ Using default dictionary")
    else:
        st.sidebar.error("❌ Default dictionary not found")
        st.session_state.dictionary_file_path = None

# Download dictionary button
if (not use_custom_dict and default_dict_exists) or (use_custom_dict and os.path.exists("temp_dictionary.json")):
    try:
        dict_file_path = st.session_state.dictionary_file_path
        if dict_file_path and os.path.exists(dict_file_path):
            with open(dict_file_path, "r", encoding='utf-8') as f:
                dict_content = f.read()
            st.sidebar.download_button(
                label="📥 Download Dictionary",
                data=dict_content,
                file_name="dictionary.json",
                mime="application/json",
                help="Download current dictionary file"
            )
    except Exception as e:
        st.sidebar.error(f"Error reading dictionary file: {str(e)}")

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Patterns Configuration
st.sidebar.markdown('<div class="config-section">', unsafe_allow_html=True)
st.sidebar.markdown("**Regex Patterns Configuration**")

# Patterns toggle
use_custom_patterns = st.sidebar.toggle(
    "Use Custom Patterns",
    value=st.session_state.use_custom_patterns,
    key="patterns_toggle",
    help="Toggle to use custom regex patterns file instead of default"
)
st.session_state.use_custom_patterns = use_custom_patterns

# Patterns file handling
if use_custom_patterns:
    # Custom patterns upload
    patterns_file = st.sidebar.file_uploader(
        "Upload Custom Regex Patterns JSON",
        type=['json'],
        key="patterns_upload",
        help="Upload your custom regex patterns file"
    )
    
    if patterns_file:
        # Save custom patterns file
        with open("temp_regex_patterns.json", "w", encoding='utf-8') as f:
            f.write(patterns_file.getvalue().decode('utf-8'))
        st.session_state.patterns_file_path = "temp_regex_patterns.json"
        st.sidebar.success("✅ Custom patterns uploaded!")
    else:
        st.sidebar.warning("⚠️ Please upload a custom patterns file")
        st.session_state.patterns_file_path = None
else:
    # Use default patterns
    if default_patterns_exists:
        st.session_state.patterns_file_path = "regex_patterns.json"
        st.sidebar.success("✅ Using default patterns")
    else:
        st.sidebar.error("❌ Default patterns not found")
        st.session_state.patterns_file_path = None

# Download patterns button
if (not use_custom_patterns and default_patterns_exists) or (use_custom_patterns and os.path.exists("temp_regex_patterns.json")):
    try:
        patterns_file_path = st.session_state.patterns_file_path
        if patterns_file_path and os.path.exists(patterns_file_path):
            with open(patterns_file_path, "r", encoding='utf-8') as f:
                patterns_content = f.read()
            st.sidebar.download_button(
                label="📥 Download Patterns",
                data=patterns_content,
                file_name="regex_patterns.json",
                mime="application/json",
                help="Download current regex patterns file"
            )
    except Exception as e:
        st.sidebar.error(f"Error reading patterns file: {str(e)}")

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Update config ready status
dict_ready = st.session_state.dictionary_file_path and os.path.exists(st.session_state.dictionary_file_path)
patterns_ready = st.session_state.patterns_file_path and os.path.exists(st.session_state.patterns_file_path)
st.session_state.config_files_ready = dict_ready and patterns_ready

# Configuration Status
st.sidebar.subheader("📊 Configuration Status")
if dict_ready:
    dict_source = "Custom" if st.session_state.dictionary_file_path.startswith("temp_") else "Default"
    st.sidebar.success(f"✅ Dictionary: {dict_source}")
else:
    st.sidebar.error("❌ Dictionary: Not available")

if patterns_ready:
    patterns_source = "Custom" if st.session_state.patterns_file_path.startswith("temp_") else "Default"
    st.sidebar.success(f"✅ Patterns: {patterns_source}")
else:
    st.sidebar.error("❌ Patterns: Not available")

# Overall status
if st.session_state.config_files_ready:
    st.sidebar.success("🎉 Configuration Ready!")
else:
    st.sidebar.error("⚠️ Configuration Incomplete")

# Reset to defaults button
if st.sidebar.button("🔄 Reset to Defaults", help="Reset both dictionary and patterns to default files"):
    # Remove temporary files
    if os.path.exists("temp_dictionary.json"):
        os.remove("temp_dictionary.json")
    if os.path.exists("temp_regex_patterns.json"):
        os.remove("temp_regex_patterns.json")
    
    # Reset session state
    st.session_state.use_custom_dictionary = False
    st.session_state.use_custom_patterns = False
    st.session_state.dictionary_file_path = "dictionary.json"
    st.session_state.patterns_file_path = "regex_patterns.json"
    st.session_state.config_files_ready = default_dict_exists and default_patterns_exists
    
    st.sidebar.success("✅ Reset to default configuration!")
    st.rerun()

# Processing options
st.sidebar.subheader("⚙️ Processing Options")
filter_promotional = st.sidebar.checkbox("Filter out promotional messages", value=True)

# Main content area - Choice between single test and batch processing
st.header("🎯 Choose Processing Mode")

# Mode selection
processing_mode = st.radio(
    "Select how you want to process transactions:",
    ["🔍 Test Single Notification", "📊 Process CSV File"],
    horizontal=True
)

if processing_mode == "🔍 Test Single Notification":
    # Single notification testing section
    st.markdown('<div class="test-section">', unsafe_allow_html=True)
    st.subheader("🧪 Single Notification Testing")
    st.write("Test the parser with a single notification message to see how it performs.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input fields for single notification
        st.write("**Enter notification details:**")
        
        # Get auto-filled values if available
        default_message = getattr(st.session_state, 'auto_message', '')
        default_contents = getattr(st.session_state, 'auto_contents', '')
        default_app_label = getattr(st.session_state, 'auto_app_label', '')
        default_package_name = getattr(st.session_state, 'auto_package_name', '')
        
        test_message = st.text_area(
            "Notification Message",
            value=default_message,
            placeholder="Enter the notification message text here...",
            help="The actual notification message content"
        )
        
        test_contents = st.text_area(
            "Notification Contents",
            value=default_contents,
            placeholder="Additional content if available...",
            help="Additional notification contents (usually contains the transaction details)"
        )
        
        col_input1, col_input2 = st.columns(2)
        
        with col_input1:
            test_app_label = st.text_input(
                "App Label",
                value=default_app_label,
                placeholder="e.g., myBCA, GoPay",
                help="The app name/label"
            )
            
            test_package_name = st.text_input(
                "Package Name",
                value=default_package_name,
                placeholder="e.g., com.bca.mybca.omni.android",
                help="The app package name"
            )
        
        with col_input2:
            test_user_id = st.text_input(
                "User ID",
                value="test_user",
                help="User identifier"
            )
            
            test_id = st.text_input(
                "Notification ID",
                value="test_001",
                help="Unique notification identifier"
            )
        
        # Clear auto-fill values after processing
        if st.button("🧪 Test Single Notification", type="primary", disabled=not st.session_state.config_files_ready):
            if test_message.strip():
                # Clear auto-fill values
                if hasattr(st.session_state, 'auto_message'):
                    delattr(st.session_state, 'auto_message')
                if hasattr(st.session_state, 'auto_contents'):
                    delattr(st.session_state, 'auto_contents')
                if hasattr(st.session_state, 'auto_app_label'):
                    delattr(st.session_state, 'auto_app_label')
                if hasattr(st.session_state, 'auto_package_name'):
                    delattr(st.session_state, 'auto_package_name')
                    
                with st.spinner("Testing notification..."):
                    try:
                        # Create a single-row DataFrame for testing
                        test_df = pd.DataFrame({
                            'id': [test_id or "test_001"],
                            'package_name': [test_package_name or "unknown"],
                            'app_label': [test_app_label or "unknown"],
                            'message': [test_message],
                            'contents': [test_contents or ""],
                            'timestamp': [datetime.now().isoformat()],
                            'user_id': [test_user_id or "test_user"]
                        })
                        
                        # Process the single notification
                        result_df = process_notification_data(
                            test_df,
                            st.session_state.dictionary_file_path,
                            st.session_state.patterns_file_path,
                            filter_promotional=filter_promotional
                        )
                        
                        st.session_state.single_test_result = result_df
                        
                        if not result_df.empty:
                            st.success("✅ Notification processed successfully!")
                        else:
                            st.warning("⚠️ No transaction data extracted from this notification")
                        
                    except Exception as e:
                        st.error(f"❌ Error processing notification: {str(e)}")
                        st.exception(e)
            else:
                st.warning("⚠️ Please enter a notification message to test")
        
        # Show configuration status message if not ready
        if not st.session_state.config_files_ready:
            st.error("⚠️ Configuration incomplete. Please ensure both dictionary and patterns files are available.")
    
    with col2:
        # Sample notifications for testing
        st.write("**Sample Notifications:**")
        st.write("Click to use as test input")
        
        sample_data = [
            {
                "message": "Catatan Finansial.",
                "contents": "Pengeluaran sebesar IDR 71,490.00 di kategori Hiburan.",
                "app_label": "myBCA",
                "package_name": "com.bca.mybca.omni.android",
                "description": "BCA Entertainment Expense"
            },
            {
                "message": "Catatan Finansial.",
                "contents": "Pengeluaran sebesar IDR 6,500.00 di kategori Biaya Admin.",
                "app_label": "myBCA",
                "package_name": "com.bca.mybca.omni.android",
                "description": "BCA Admin Fee"
            },
            {
                "message": "Catatan Finansial.",
                "contents": "Pengeluaran sebesar IDR 10,000,000.00 di kategori Transfer Rekening.",
                "app_label": "myBCA",
                "package_name": "com.bca.mybca.omni.android",
                "description": "BCA Account Transfer"
            },
            {
                "message": "Payment successful!.",
                "contents": "Awesome, you just paid Rp10.000 to DAIRY QUEEN - MALL KELAPA dana.",
                "app_label": "GoPay",
                "package_name": "com.gojek.gopay",
                "description": "GoPay Payment"
            }
        ]
        
        for i, sample in enumerate(sample_data):
            if st.button(f"Sample {i+1}: {sample['description']}", key=f"sample_{i}", help=sample['contents'][:50] + "..."):
                # Directly set the session state values for auto-fill
                st.session_state.auto_message = sample['message']
                st.session_state.auto_contents = sample['contents']
                st.session_state.auto_app_label = sample['app_label']
                st.session_state.auto_package_name = sample['package_name']
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
                st.metric("Category", result_data.iloc[0]['category'])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show detailed parsing results
            st.subheader("Detailed Parsing Results")
            st.dataframe(result_data, use_container_width=True)
            
            # Download single result
            single_csv = result_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Test Result",
                data=single_csv,
                file_name=f"single_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No transaction data could be extracted from this notification. This might be because:")
            st.write("- The notification doesn't contain transaction information")
            st.write("- The message format is not recognized by the current patterns")
            st.write("- The notification was filtered out as promotional")
            st.write("- The dictionary doesn't contain matching keywords")

else:
    # CSV file processing section (original functionality)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 CSV File Processing")
        
        # File upload section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Notification Data CSV",
            type=['csv'],
            help="Upload a CSV file containing notification data with columns: id, package_name, app_label, message, contents, timestamp"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file and st.session_state.config_files_ready:
            try:
                # Read the uploaded CSV
                df = pd.read_csv(uploaded_file)
                
                # Display basic info about the uploaded file
                st.subheader("📋 Data Overview")
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.metric("Total Rows", len(df))
                with col_info2:
                    st.metric("Columns", len(df.columns))
                with col_info3:
                    st.metric("Missing Values", df.isnull().sum().sum())
                
                # Show column info
                st.subheader("Column Information")
                expected_columns = ['id', 'package_name', 'app_label', 'message', 'contents', 'timestamp']
                available_columns = df.columns.tolist()
                
                col_check1, col_check2 = st.columns(2)
                with col_check1:
                    st.write("**Expected Columns:**")
                    for col in expected_columns:
                        if col in available_columns:
                            st.write(f"✅ {col}")
                        else:
                            st.write(f"❌ {col} (missing)")
                
                with col_check2:
                    st.write("**Available Columns:**")
                    for col in available_columns:
                        st.write(f"• {col}")
                
                # Preview data
                st.subheader("Data Preview")
                st.dataframe(df.head(10))
                
                # Process button
                if st.button("🔄 Process Transactions", type="primary"):
                    with st.spinner("Processing transactions..."):
                        try:
                            # Process the data
                            processed_df = process_notification_data(
                                df, 
                                st.session_state.dictionary_file_path, 
                                st.session_state.patterns_file_path,
                                filter_promotional=filter_promotional
                            )
                            
                            st.session_state.processed_data = processed_df
                            st.success("✅ Processing completed successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error processing data: {str(e)}")
                            st.exception(e)
            
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {str(e)}")
        
        elif uploaded_file and not st.session_state.config_files_ready:
            st.warning("⚠️ Please ensure both dictionary and patterns files are available in the sidebar configuration.")
    
    with col2:
        st.header("📈 Quick Stats")
        
        if st.session_state.processed_data is not None and not st.session_state.processed_data.empty:
            data = st.session_state.processed_data
            
            # Metrics
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Transactions", len(data))
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Amount", f"${data['amount'].sum():,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Unique Categories", data['category'].nunique())
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            # Handle account_number field safely
            if 'account_number' in data.columns:
                unique_accounts = data['account_number'].nunique()
            else:
                unique_accounts = 0
            st.metric("Unique Accounts", unique_accounts)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Transaction type distribution
            st.subheader("Transaction Types")
            type_counts = data['transaction_type'].value_counts()
            fig_pie = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Transaction Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# Results section (only show for CSV processing)
if processing_mode == "📊 Process CSV File" and st.session_state.processed_data is not None and not st.session_state.processed_data.empty:
    st.header("🔍 Analysis Results")
    
    data = st.session_state.processed_data
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Charts", "📋 Data Table", "💾 Export"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Categories by Amount")
            category_amounts = data.groupby('category')['amount'].sum().sort_values(ascending=False)
            st.dataframe(category_amounts.head(10))
            
            st.subheader("Top Categories by Count")
            category_counts = data['category'].value_counts()
            st.dataframe(category_counts.head(10))
        
        with col2:
            st.subheader("Transaction Type Summary")
            type_summary = data.groupby('transaction_type').agg({
                'amount': ['sum', 'mean', 'count']
            }).round(2)
            st.dataframe(type_summary)
            
            st.subheader("Recent Transactions")
            recent_data = data.sort_values('timestamp', ascending=False).head(5)
            st.dataframe(recent_data[['timestamp', 'transaction_type', 'amount', 'category']])
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution
            st.subheader("Amount by Category")
            category_amounts = data.groupby('category')['amount'].sum().sort_values(ascending=False)
            fig_bar = px.bar(
                x=category_amounts.values,
                y=category_amounts.index,
                orientation='h',
                title="Total Amount by Category"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Transaction type amounts
            st.subheader("Amount by Transaction Type")
            type_amounts = data.groupby('transaction_type')['amount'].sum()
            fig_bar2 = px.bar(
                x=type_amounts.index,
                y=type_amounts.values,
                title="Total Amount by Transaction Type"
            )
            st.plotly_chart(fig_bar2, use_container_width=True)
        
        # Time series if timestamp data is available
        if 'timestamp' in data.columns:
            st.subheader("Transaction Timeline")
            try:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                daily_amounts = data.groupby(data['timestamp'].dt.date)['amount'].sum()
                
                fig_line = px.line(
                    x=daily_amounts.index,
                    y=daily_amounts.values,
                    title="Daily Transaction Amounts"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            except:
                st.info("Unable to parse timestamp data for timeline visualization")
    
    with tab3:
        st.subheader("Processed Transaction Data")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_types = st.multiselect(
                "Filter by Transaction Type",
                options=data['transaction_type'].unique(),
                default=data['transaction_type'].unique()
            )
        
        with col2:
            selected_categories = st.multiselect(
                "Filter by Category",
                options=data['category'].unique(),
                default=data['category'].unique()
            )
        
        with col3:
            min_amount = st.number_input("Minimum Amount", value=0.0)
            max_amount = st.number_input("Maximum Amount", value=float(data['amount'].max()))
        
        # Apply filters
        filtered_data = data[
            (data['transaction_type'].isin(selected_types)) &
            (data['category'].isin(selected_categories)) &
            (data['amount'] >= min_amount) &
            (data['amount'] <= max_amount)
        ]
        
        st.dataframe(filtered_data, use_container_width=True)
        st.info(f"Showing {len(filtered_data)} of {len(data)} transactions")
    
    with tab4:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"processed_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # JSON download
            json_data = data.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"processed_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# Personalization section
st.header("🎨 Personalization")
st.info(
    "💡 **Want to customize the transaction parsing?** \n\n"
    "1. **Toggle** to use custom files in the sidebar configuration\n"
    "2. **Upload** your customized dictionary and/or patterns files\n"
    "3. **Download** the current files to see the format and modify them\n"
    "4. **Test** with single notifications to see how your changes perform\n"
    "5. **Reset** to defaults anytime using the reset button\n\n"
    "This way you can fine-tune the parser to work perfectly with your specific notification formats!"
)

# Footer
st.markdown("---")
st.markdown(
    "💡 **Tip:** Use single notification testing to debug and improve your parsing rules before processing large CSV files!"
)