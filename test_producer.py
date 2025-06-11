import json
from kafka import KafkaProducer
from datetime import datetime

def send_test_notification():
    producer = KafkaProducer(
        bootstrap_servers=['18.136.193.239:9092'],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    
    # Sample notification data
    test_notification = {
        'ID': 'test_001',
        'PACKAGE_NAME': 'com.example.bank',
        'APP_LABEL': 'Bank App',
        'MESSAGE': 'Your account has been debited with Rs. 1500.00',
        'DATE': datetime.now().strftime('%Y-%m-%d'),
        'CONTENTS': 'Transaction notification',
        'TIMESTAMP': datetime.now().isoformat()
    }
    
    # Send to raw-notifications topic
    future = producer.send('raw-notifications', test_notification)
    result = future.get(timeout=10)
    
    print(f"Sent test notification: {test_notification}")
    print(f"Result: {result}")
    
    producer.close()

if __name__ == "__main__":
    send_test_notification()

