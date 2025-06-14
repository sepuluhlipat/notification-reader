import json
import logging
import time
import os
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
import pandas as pd
from notification_reader import process_notification_data

# Setup logging
logs_dir = 'logs'
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
                 dictionary_file, patterns_file, batch_interval=10):
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.consumer_group = consumer_group
        self.dictionary_file = dictionary_file
        self.patterns_file = patterns_file
        self.batch_interval = batch_interval
        
        self.consumer = None
        self.producer = None
        self.message_batch = []
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
                api_version=(0, 10, 1),
                request_timeout_ms=40000,  # Individual request timeout
                session_timeout_ms=30000,  # Session timeout (should be > request_timeout_ms)
                heartbeat_interval_ms=10000,  # Should be < session_timeout_ms/3
                max_poll_interval_ms=300000  # Added for stability
            )
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
                acks='all',
                retries=3,
                api_version=(0, 10, 1),
                request_timeout_ms=40000,  # Individual request timeout
                batch_size=16384,
                linger_ms=10
            )
            
            logger.info(f"Kafka connections established to {self.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Kafka connection failed: {e}")
            raise
    
    def _process_batch(self):
        """Process batch of notifications"""
        if not self.message_batch:
            return
        
        batch_size = len(self.message_batch)
        
        try:
            # Convert to DataFrame
            batch_data = {
                'ID': [msg.get('ID', '') for msg in self.message_batch],
                'PACKAGE NAME': [msg.get('PACKAGE_NAME', '') for msg in self.message_batch],
                'APP LABEL': [msg.get('APP_LABEL', '') for msg in self.message_batch],
                'MESSAGE': [msg.get('MESSAGE', '') for msg in self.message_batch],
                'DATE': [msg.get('DATE', '') for msg in self.message_batch],
                'CONTENTS': [msg.get('CONTENTS', '') for msg in self.message_batch],
                'TIMESTAMP': [msg.get('TIMESTAMP', '') for msg in self.message_batch]
            }
            
            df_batch = pd.DataFrame(batch_data)
            
            # Process with notification reader
            result_df = process_notification_data(df_batch, self.dictionary_file, self.patterns_file)
            
            # Send valid transactions
            sent_count = 0
            for _, row in result_df.iterrows():
                if row.get('transaction_type', 'unknown') != 'unknown':
                    try:
                        future = self.producer.send(self.output_topic, row.to_dict())
                        future.get(timeout=10)  # Increased timeout for remote connection
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send transaction: {e}")
            
            self.processed_count += sent_count
            logger.info(f"Batch: {batch_size} notifications → {sent_count} transactions sent")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise
        finally:
            self.message_batch.clear()
    
    def _collect_messages(self):
        """Collect messages from Kafka"""
        try:
            message_records = self.consumer.poll(timeout_ms=1000)  # Increased timeout
            collected = 0
            
            for topic_partition, messages in message_records.items():
                for message in messages:
                    self.message_batch.append(message.value)
                    collected += 1
            
            return collected
        except Exception as e:
            logger.error(f"Message collection failed: {e}")
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
        print(f"⏱️  Batch every {self.batch_interval}s")
        print("Press Ctrl+C to stop\n")
        
        logger.info("Processor started")
        
        try:
            batch_count = 0
            while self.is_running:
                start_time = time.time()
                
                # Collect messages for batch interval
                while time.time() - start_time < self.batch_interval:
                    self._collect_messages()
                    time.sleep(0.1)
                
                batch_count += 1
                
                # Process batch
                if self.message_batch:
                    batch_size = len(self.message_batch)
                    self._process_batch()
                    print(f"✅ Batch {batch_count}: {batch_size} notifications processed")
                else:
                    print(f"⌛ Batch {batch_count}: No new notifications")
                
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
        
        # Process remaining messages
        if self.message_batch:
            try:
                self._process_batch()
            except Exception as e:
                logger.error(f"Final batch processing failed: {e}")
        
        # Close connections
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
        'bootstrap_servers': ['18.136.193.239:9092'],  # Updated to remote Kafka broker
        'input_topic': 'raw-notifications',
        'output_topic': 'processed-notifications',
        'consumer_group': 'notification-processor',
        'dictionary_file': 'dictionary.json',
        'patterns_file': 'regex_patterns.json',
        'batch_interval': 10
    }
    
    processor = KafkaNotificationProcessor(**config)
    processor.run()

if __name__ == "__main__":
    main()