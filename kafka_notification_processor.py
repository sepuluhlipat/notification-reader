import json
import logging
import time
import os
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
import pandas as pd
from notification_reader import process_notification_data

# Setup logging
logs_dir = '/var/log/notification-parser'
os.makedirs(logs_dir, exist_ok=True)

log_filename = os.path.join(logs_dir, f'kafka_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler(log_filename, encoding='utf-8')]
)
logger = logging.getLogger(__name__)

class KafkaNotificationProcessor:
    def __init__(self, bootstrap_servers, input_topic, output_topic, consumer_group, 
                 dictionary_file, patterns_file):
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.consumer_group = consumer_group
        self.dictionary_file = dictionary_file
        self.patterns_file = patterns_file
        
        self.consumer = None
        self.producer = None
        self.processed_count = 0
        self.is_running = False
        
        self._validate_files()
        self._setup_kafka()
        
    def _validate_files(self):
        """Check required files exist"""
        for file_path in [self.dictionary_file, self.patterns_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
        
    def _setup_kafka(self):
        """Initialize Kafka connections"""
        try:
            self.consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000,
                request_timeout_ms=40000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_interval_ms=300000
            )
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
                acks='all',
                retries=3,
                api_version=(0, 10, 1),
                request_timeout_ms=40000,
                batch_size=16384,
                linger_ms=10
            )
            
            logger.info(f"Kafka connections established to {self.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Kafka connection failed: {e}")
            raise
    
    def _process_message(self, message_data):
        """Process a single notification message"""
        try:
            # Convert to DataFrame format
            df = pd.DataFrame([{
                'user_id': message_data.get('user_id', ''),
                'package_name': message_data.get('package_name', ''),
                'app_label': message_data.get('app_label', ''),
                'message': message_data.get('message', ''),
                'date': message_data.get('date', ''),
                'contents': message_data.get('contents', ''),
                'timestamp': message_data.get('timestamp', '')
            }])
            
            # Process with notification reader
            result_df = process_notification_data(df, self.dictionary_file, self.patterns_file)
            
            # Send valid transactions
            sent_count = 0
            for _, row in result_df.iterrows():
                if row.get('transaction_type', 'unknown') != 'unknown':
                    future = self.producer.send(self.output_topic, row.to_dict())
                    future.get(timeout=10)
                    sent_count += 1
            
            self.processed_count += sent_count
            return sent_count
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return 0
    
    def _poll_and_process(self):
        """Poll messages and process immediately"""
        try:
            message_records = self.consumer.poll(timeout_ms=1000)
            processed = 0
            
            for topic_partition, messages in message_records.items():
                for message in messages:
                    sent = self._process_message(message.value)
                    if sent > 0:
                        processed += 1
                        logger.info(f"Processed notification → {sent} transactions")
            
            return processed
            
        except Exception as e:
            logger.error(f"Polling failed: {e}")
            return 0
    
    def run(self):
        """Main processing loop"""
        if not self.consumer or not self.producer:
            print("❌ Kafka connections not established")
            return
        
        self.is_running = True
        
        print("🚀 Kafka Notification Processor Started")
        print(f"🌐 Connected to: {self.bootstrap_servers}")
        print(f"📥 {self.input_topic} → 📤 {self.output_topic}")
        print("Press Ctrl+C to stop\n")
        
        logger.info("Processor started")
        
        try:
            total_processed = 0
            while self.is_running:
                processed = self._poll_and_process()
                if processed > 0:
                    total_processed += processed
                    print(f"✅ Processed {processed} notifications (Total: {total_processed})")
                else:
                    time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            logger.info("Shutdown requested")
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Fatal error: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        self.is_running = False
        
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
        
        print(f"✅ Stopped. Total processed: {self.processed_count} transactions")
        print(f"📝 Logs: {log_filename}")
        
        logger.info(f"Processor stopped. Total processed: {self.processed_count}")

def main():
    config = {
        'bootstrap_servers': ['18.136.193.239:9092'],
        'input_topic': 'notification_parser_task',
        'output_topic': 'notification_parser_result',
        'consumer_group': 'notification_processor_v1',
        'dictionary_file': 'dictionary.json',
        'patterns_file': 'regex_patterns.json'
    }
    
    processor = KafkaNotificationProcessor(**config)
    processor.run()

if __name__ == "__main__":
    main()