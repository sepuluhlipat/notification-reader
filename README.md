# 💰 Transaction Notification Parser

A smart notification parser that automatically extracts transaction details from banking and financial app notifications using configurable patterns and machine learning techniques.

## 🚀 Overview

This project provides a complete solution for parsing financial transaction notifications from mobile banking apps, e-wallets, and other financial services. It extracts key information like amounts, transaction types, categories, and account numbers from raw notification text.

### Key Features

- **Smart Transaction Parsing**: Automatically identifies transaction type (income, expense, transfer)
- **Amount Extraction**: Handles multiple currency formats (Indonesian Rupiah, USD, etc.)
- **Category Classification**: Intelligently categorizes transactions using merchant databases and keywords
- **Multi-language Support**: Works with Indonesian and English notifications
- **Promotional Filtering**: Filters out promotional messages and ads
- **Real-time Processing**: Kafka integration for streaming transaction data
- **Configurable Patterns**: Easily customizable regex patterns and dictionaries
- **Interactive Dashboard**: Web-based interface for testing and batch processing
- **Feedback System**: Integrated feedback collection for continuous improvement

## 🎯 Live Testing

### **[🌐 Try the Live Demo](https://notification-reader-imkdavmoew4hp3ys4ngkzo.streamlit.app/)**

Test the application instantly with our interactive web interface:

- **Single Notification Testing** with sample data
- **Interactive Configuration Editor**
- **Real-time Feedback Collection**
- **Batch CSV Processing** capabilities
- **Pattern Testing** and validation

*No installation required - test your notifications directly in the browser!*

## 🏗️ Architecture

### Standard Processing Pipeline
```
Notification Input → Pattern Matching → Category Classification → Structured Output
```

### Kafka Streaming Architecture
```
Notification Producer → Kafka Topic → Processor → Parsed Transactions → Output Topic
```

## 🛠️ How It Works

### 1. **Configuration System**
- **Dictionary**: Contains categories, merchants, transaction types, and app filters
- **Regex Patterns**: Configurable patterns for extracting amounts, account numbers, and other data
- **Allowlist/Blacklist**: Controls which apps to process or ignore

### 2. **Processing Pipeline**
1. **Input Validation**: Checks if the notification source is allowed/not blacklisted
2. **Promotional Detection**: Identifies and filters promotional messages
3. **Pattern Matching**: Applies regex patterns to extract structured data
4. **Category Classification**: Matches against merchant databases and keywords
5. **Data Cleaning**: Standardizes amounts and formats output

### 3. **Output Format**
```json
{
  "id": "transaction_id",
  "timestamp": "2024-01-15 10:30:00",
  "transaction_type": "expense",
  "amount": 25000.00,
  "account_number": "1234567890",
  "category": "food_dining"
}
```

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.8+
- Apache Kafka (for streaming mode)
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration files**
   
   Create `dictionary.json`:
   ```json
   {
     "categories": {
       "food_dining": ["restaurant", "cafe", "food"],
       "transportation": ["taxi", "bus", "fuel"]
     },
     "merchants": {
       "food_dining": ["mcdonalds", "kfc", "starbucks"],
       "transportation": ["grab", "gojek", "uber"]
     },
     "transaction_types": {
       "income": ["received", "credit", "deposit"],
       "expense": ["paid", "debit", "purchase"],
       "transfer": ["transfer", "sent"]
     },
     "blacklist": ["spam-app", "ads-app"],
     "allowlist": ["bank-app", "wallet-app"]
   }
   ```

   Create `regex_patterns.json`:
   ```json
   {
     "amount_patterns": [
       "(?:IDR|Rp|Rs|\\$)\\s*([0-9.,]+)",
       "sebesar\\s+(?:IDR|Rp)?\\s*([0-9.,]+)"
     ],
     "account_patterns": [
       "(?:a/c|account|rekening)[\\s:]*([0-9]{6,})",
       "ke\\s+([0-9]{6,})"
     ],
     "promotional_patterns": {
       "keywords": ["promo", "discount", "offer"],
       "regex_patterns": ["limited.*time", "special.*offer"]
     },
     "confirmation_patterns": {
       "keywords": ["successful", "completed", "confirmed"]
     }
   }
   ```

## 🧪 Testing Options

### 1. **Web Dashboard Testing**
```bash
streamlit run dashboard.py
```
- Access at `http://localhost:8501`
- Test individual notifications
- Upload CSV files for batch processing
- Interactive configuration editing

### 2. **Single Notification Testing**
```python
from notification_reader import NotificationParser

parser = NotificationParser("dictionary.json", "regex_patterns.json")
transaction = parser.parse_notification(
    message="Payment successful!",
    contents="You paid Rs.25,000 to McDonald's",
    app_name="GoPay"
)
```

### 3. **Batch Processing Testing**
```python
import pandas as pd
from notification_reader import process_notification_data

df = pd.read_csv("notifications.csv")
results = process_notification_data(df, "dictionary.json", "regex_patterns.json")
```

## 🚀 Kafka Streaming (Production Mode)

### Setup Kafka Environment

1. **Start Kafka Server**
   ```bash
   # Start Zookeeper
   bin/zookeeper-server-start.sh config/zookeeper.properties
   
   # Start Kafka
   bin/kafka-server-start.sh config/server.properties
   ```

2. **Create Topics**
   ```bash
   # Input topic for raw notifications
   bin/kafka-topics.sh --create --topic notification_parser_task --bootstrap-server localhost:9092
   
   # Output topic for processed transactions
   bin/kafka-topics.sh --create --topic notification_parser_result --bootstrap-server localhost:9092
   ```

### Running the Kafka Processor

**Start the processor:**
```bash
python kafka_processor.py
```

**Send test notifications:**
```bash
# Send a batch of test notifications
python test_producer.py

# Send single notification
python test_producer.py single

# Send continuous notifications (every 15 seconds)
python test_producer.py continuous 15
```

### Kafka Configuration

The processor uses these default settings:
- **Bootstrap Servers**: `18.136.193.239:9092`
- **Input Topic**: `notification_parser_task`
- **Output Topic**: `notification_parser_result`
- **Consumer Group**: `notification_processor_v1`

**Monitor processing:**
```bash
# Check logs
tail -f /var/log/notification-parser/kafka_processor_*.log

# Monitor topics
bin/kafka-console-consumer.sh --topic notification_parser_result --from-beginning --bootstrap-server localhost:9092
```

## 📊 CSV Data Format

Your input CSV should contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Unique notification ID | "notif_001" |
| `message` | Notification title | "Payment successful" |
| `contents` | Notification body | "You paid Rs.25,000 to McDonald's" |
| `app_label` | App display name | "GoPay" |
| `package_name` | App package identifier | "com.gojek.app" |
| `timestamp` | Notification timestamp | "2024-01-15 10:30:00" |
| `user_id` | User identifier | "user123" |

## 🔧 Configuration

### Dictionary Structure
- **categories**: General transaction categories with keywords
- **merchants**: Specific merchant names mapped to categories
- **transaction_types**: Keywords for identifying transaction types
- **blacklist**: Apps to completely ignore
- **allowlist**: Apps to exclusively process (leave empty to allow all)

### Regex Patterns
- **amount_patterns**: Patterns to extract monetary amounts
- **account_patterns**: Patterns to extract account numbers
- **promotional_patterns**: Patterns to identify promotional content
- **confirmation_patterns**: Patterns to identify transaction confirmations

## 📈 Performance & Monitoring

### Kafka Processor Features
- **Auto-reconnection**: Handles network disconnections gracefully
- **Batch Processing**: Processes multiple notifications efficiently
- **Error Handling**: Logs errors and continues processing
- **Graceful Shutdown**: Properly closes connections on Ctrl+C

### Monitoring
- **Real-time Logs**: Detailed logging with timestamps
- **Processing Metrics**: Track notifications processed per second
- **Error Tracking**: Monitor failed processing attempts
- **Health Checks**: Verify Kafka connectivity

## 🐛 Troubleshooting

### Common Issues

1. **"Configuration files not found"**
   - Ensure `dictionary.json` and `regex_patterns.json` exist
   - Check file permissions and JSON syntax

2. **"Kafka connection failed"**
   - Verify Kafka server is running
   - Check bootstrap server configuration
   - Ensure topics exist

3. **"No transactions extracted"**
   - Verify notification format matches regex patterns
   - Check if the app is blacklisted
   - Test with the [web dashboard](https://notification-reader-imkdavmoew4hp3ys4ngkzo.streamlit.app/) first

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### Core Classes
- **`NotificationParser`**: Main parsing engine
- **`KafkaNotificationProcessor`**: Streaming processor
- **`NotificationProducer`**: Test data generator

### Key Functions
- **`process_notification_data()`**: Batch processing
- **`parse_notification()`**: Single notification parsing
- **`send_test_batch()`**: Generate test data

## 🙋‍♂️ Support & Contribution

- **[🌐 Live Demo](https://notification-reader-imkdavmoew4hp3ys4ngkzo.streamlit.app/)**: Test the application
- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check inline code documentation for detailed API reference
- **Community**: Join discussions for tips and best practices

### Getting Help
1. **Try the [live demo](https://notification-reader-imkdavmoew4hp3ys4ngkzo.streamlit.app/)** first
2. Check the troubleshooting section
3. Enable debug logging for detailed error information
4. Submit issues with sample data and configuration

---

**Built with ❤️ for better financial data management**

*Ready to process millions of notifications in real-time!*