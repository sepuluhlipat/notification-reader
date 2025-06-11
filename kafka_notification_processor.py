import json
import logging
from kafka import KafkaConsumer, KafkaProducer
import pandas as pd
from datetime import datetime
from notification_reader import process_notification_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaNotificationProcessor:
    def __init__(self, bootstrap_servers, input_topic, output_topic, consumer_group, dictionary_file, patterns_file):
        self.consumer = KafkaConsumer(
            input_topic,
            bootstrap_servers=bootstrap_servers,
            group_id=consumer_group,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest'
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        self.output_topic = output_topic
        self.dictionary_file = dictionary_file
        self.patterns_file = patterns_file
        
    def process_and_send(self, notification_data):
        try:
            # Create DataFrame with exact column structure expected by process_notification_data
            df_data = {
                'ID': [notification_data.get('ID', '')],
                'PACKAGE NAME': [notification_data.get('PACKAGE_NAME', '')],
                'APP LABEL': [notification_data.get('APP_LABEL', '')],
                'MESSAGE': [notification_data.get('MESSAGE', '')],
                'DATE': [notification_data.get('DATE', '')],
                'CONTENTS': [notification_data.get('CONTENTS', '')],
                'TIMESTAMP': [notification_data.get('TIMESTAMP', '')]
            }
            
            df = pd.DataFrame(df_data)
            
            # Process using existing function
            result_df = process_notification_data(df, self.dictionary_file, self.patterns_file)
            
            # Send each processed transaction
            for _, row in result_df.iterrows():
                if row['transaction_type'] != 'unknown':
                    transaction_data = row.to_dict()
                    transaction_data['processed_at'] = datetime.now().isoformat()
                    
                    self.producer.send(self.output_topic, transaction_data)
                    logger.info(f"Sent: {transaction_data['transaction_type']} - {transaction_data.get('amount', 'N/A')} - {transaction_data.get('category', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            logger.error(f"Notification data: {notification_data}")
    
    def run(self):
        logger.info(f"Starting processor - consuming from: {self.consumer._subscription}")
        logger.info(f"Producing to: {self.output_topic}")
        
        try:
            for message in self.consumer:
                self.process_and_send(message.value)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.consumer.close()
            self.producer.close()

def main():
    config = {
        'bootstrap_servers': ['localhost:9092'],
        'input_topic': 'raw-notifications',
        'output_topic': 'processed-notifications', 
        'consumer_group': 'notification-processor',
        'dictionary_file': 'dictionary.json',
        'patterns_file': 'regex_patterns.json'
    }
    
    processor = KafkaNotificationProcessor(**config)
    processor.run()

if __name__ == "__main__":
    main()