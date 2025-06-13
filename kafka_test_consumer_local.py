from kafka import KafkaConsumer
import json
import sys
import datetime

def consume_messages(topic='processed-notifications'):
    consumer = None
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['localhost:29092'],
            group_id='test-consumer-group',  # Consumer group to track offset
            auto_offset_reset='latest',  # For first time, start from latest
            enable_auto_commit=True,  # Automatically commit offsets
            auto_commit_interval_ms=1000,  # Commit every 1 second
            value_deserializer=lambda x: x.decode('utf-8') if x else None,
            api_version=(0, 10, 1),
            request_timeout_ms=15000,
            session_timeout_ms=10000,
            heartbeat_interval_ms=3000
        )
        
        print(f"Consuming messages from '{topic}' topic...")
        print("Press Ctrl+C to stop...")
        print("=" * 60)
        
        message_count = 0
        
        for message in consumer:
            message_count += 1
            
            # Convert Kafka timestamp to readable format
            readable_timestamp = datetime.datetime.fromtimestamp(message.timestamp / 1000)
            
            print(f"Message {message_count}:")
            print(f"  Offset: {message.offset}")
            print(f"  Partition: {message.partition}")
            print(f"  Kafka Timestamp: {readable_timestamp}")
            print(f"  Value: {message.value}")
            print("-" * 50)
            
    except KeyboardInterrupt:
        print(f"\n\nStopped by user. Total messages consumed: {message_count}")
        print("Closing consumer...")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if consumer:
            consumer.close()
            print("Consumer closed successfully.")

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else 'processed-notifications'
    consume_messages(topic)