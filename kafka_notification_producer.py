import json
import time
from kafka import KafkaProducer
from datetime import datetime

class NotificationProducer:
    def __init__(self, bootstrap_servers=['18.136.193.239:9092'], topic='raw-notifications'):  # Updated to remote Kafka broker
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            api_version=(0, 10, 1),
            request_timeout_ms=60000,
            metadata_max_age_ms=300000,
            max_block_ms=60000,
            batch_size=16384,
            linger_ms=10,
            acks='all',
            retries=3
        )
        print(f"🌐 Connected to Kafka broker: {bootstrap_servers}")
    
    def send_notification(self, notification_data):
        """Send a single notification"""
        try:
            future = self.producer.send(self.topic, notification_data)
            result = future.get(timeout=10)  # Reasonable timeout for remote connection
            return True
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
            return False
    
    def send_test_batch(self):
        """Send a batch of test notifications"""
        test_notifications = [
            {
                'ID': f'test_{int(time.time())}_001',
                'PACKAGE_NAME': 'com.hdfc.bank',
                'APP_LABEL': 'HDFC Bank',
                'MESSAGE': 'Your account has been debited with Rs. 1,500.00 at ATM',
                'DATE': datetime.now().strftime('%Y-%m-%d'),
                'CONTENTS': 'ATM withdrawal transaction notification',
                'TIMESTAMP': datetime.now().isoformat()
            },
            {
                'ID': f'test_{int(time.time())}_002',
                'PACKAGE_NAME': 'com.sbi.bank',
                'APP_LABEL': 'SBI Bank',
                'MESSAGE': 'Your account has been credited with Rs. 25,000.00 - Salary',
                'DATE': datetime.now().strftime('%Y-%m-%d'),
                'CONTENTS': 'Salary credit notification',
                'TIMESTAMP': datetime.now().isoformat()
            },
            {
                'ID': f'test_{int(time.time())}_003',
                'PACKAGE_NAME': 'com.paytm',
                'APP_LABEL': 'Paytm',
                'MESSAGE': 'UPI payment of Rs. 450.00 sent to merchant',
                'DATE': datetime.now().strftime('%Y-%m-%d'),
                'CONTENTS': 'UPI transaction notification',
                'TIMESTAMP': datetime.now().isoformat()
            },
            {
                'ID': f'test_{int(time.time())}_004',
                'PACKAGE_NAME': 'com.icici.bank',
                'APP_LABEL': 'ICICI Bank',
                'MESSAGE': 'Transfer of Rs. 2,000.00 to John Doe completed',
                'DATE': datetime.now().strftime('%Y-%m-%d'),
                'CONTENTS': 'Fund transfer notification',
                'TIMESTAMP': datetime.now().isoformat()
            }
        ]
        
        print(f"📨 Sending {len(test_notifications)} test notifications...")
        print("=" * 60)
        
        sent_count = 0
        for i, notification in enumerate(test_notifications, 1):
            if self.send_notification(notification):
                sent_count += 1
                print(f"✅ {i}/{len(test_notifications)} - {notification['APP_LABEL']}: Rs.{self._extract_amount(notification['MESSAGE'])}")
            time.sleep(1)  # Small delay between sends
        
        print("=" * 60)
        print(f"🎉 Sent {sent_count}/{len(test_notifications)} notifications successfully!")
        return sent_count
    
    def send_continuous_notifications(self, interval=15, count=None):
        """Send notifications continuously for testing"""
        print(f"🔄 Sending notifications every {interval} seconds...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        notification_templates = [
            {
                'PACKAGE_NAME': 'com.hdfc.bank',
                'APP_LABEL': 'HDFC Bank',
                'MESSAGE': 'Your account debited Rs. {amount} for {merchant}',
                'CONTENTS': 'Purchase transaction'
            },
            {
                'PACKAGE_NAME': 'com.paytm',
                'APP_LABEL': 'Paytm',
                'MESSAGE': 'UPI payment Rs. {amount} sent successfully',
                'CONTENTS': 'UPI transaction'
            },
            {
                'PACKAGE_NAME': 'com.sbi.bank',
                'APP_LABEL': 'SBI Bank',
                'MESSAGE': 'Account credited with Rs. {amount}',
                'CONTENTS': 'Credit transaction'
            }
        ]
        
        merchants = ['Coffee Shop', 'Grocery Store', 'Gas Station', 'Restaurant', 'Online Store']
        amounts = [50, 100, 250, 500, 750, 1000, 1500]
        
        sent_count = 0
        try:
            while count is None or sent_count < count:
                import random
                template = random.choice(notification_templates)
                amount = random.choice(amounts)
                merchant = random.choice(merchants)
                
                notification = {
                    'ID': f'auto_{int(time.time())}_{sent_count:03d}',
                    'PACKAGE_NAME': template['PACKAGE_NAME'],
                    'APP_LABEL': template['APP_LABEL'],
                    'MESSAGE': template['MESSAGE'].format(amount=amount, merchant=merchant),
                    'DATE': datetime.now().strftime('%Y-%m-%d'),
                    'CONTENTS': template['CONTENTS'],
                    'TIMESTAMP': datetime.now().isoformat()
                }
                
                if self.send_notification(notification):
                    sent_count += 1
                    print(f"📤 #{sent_count} - {notification['APP_LABEL']}: Rs.{amount}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Stopped. Sent {sent_count} notifications total.")
    
    def _extract_amount(self, message):
        """Extract amount from message for display"""
        import re
        match = re.search(r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d{2})?)', message)
        return match.group(1) if match else "N/A"
    
    def close(self):
        """Close the producer"""
        self.producer.flush()
        self.producer.close()

def main():
    import sys
    
    producer = NotificationProducer()
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "continuous":
                interval = int(sys.argv[2]) if len(sys.argv) > 2 else 15
                producer.send_continuous_notifications(interval=interval)
            elif sys.argv[1] == "single":
                # Send a single test notification
                notification = {
                    'ID': f'manual_{int(time.time())}',
                    'PACKAGE_NAME': 'com.test.bank',
                    'APP_LABEL': 'Test Bank',
                    'MESSAGE': 'Account debited Rs. 100.00 for coffee',
                    'DATE': datetime.now().strftime('%Y-%m-%d'),
                    'CONTENTS': 'Test transaction',
                    'TIMESTAMP': datetime.now().isoformat()
                }
                if producer.send_notification(notification):
                    print("✅ Single notification sent!")
                else:
                    print("❌ Failed to send notification")
            else:
                print("Usage: python test_producer.py [single|continuous [interval]]")
        else:
            # Send test batch
            producer.send_test_batch()
    
    finally:
        producer.close()

if __name__ == "__main__":
    main()