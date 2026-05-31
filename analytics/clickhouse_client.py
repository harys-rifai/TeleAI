import clickhouse_connect
from django.conf import settings
from datetime import datetime

_client = None

def get_clickhouse_client():
    global _client
    if _client is not None:
        return _client
    
    try:
        # Create client connection
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            username=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DB
        )
        
        # Initialize schema and table
        db_name = settings.CLICKHOUSE_DB
        schema_name = settings.CLICKHOUSE_SCHEMA
        
        # Clickhouse database and schema setup
        client.command(f"CREATE DATABASE IF NOT EXISTS {schema_name}")
        
        client.command(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.message_analytics (
                timestamp DateTime,
                user_id Int64,
                account_id Int64,
                direction LowCardinality(String),
                status LowCardinality(String),
                chat_id String,
                word_count UInt32
            ) ENGINE = MergeTree()
            ORDER BY (user_id, timestamp)
        """)
        
        _client = client
        return _client
    except Exception as e:
        # Gracefully print and return None so Postgres fallback can take over
        print(f"[ClickHouse Error] Failed to initialize ClickHouse client: {e}")
        return None

def log_message_event(user_id, account_id, direction, status, chat_id, text):
    """
    Log a messaging event to ClickHouse.
    """
    client = get_clickhouse_client()
    if client is None:
        return False
        
    try:
        word_count = len(text.split()) if text else 0
        timestamp = datetime.utcnow()
        
        # Insert event data
        data = [[timestamp, user_id, account_id, direction, status, chat_id, word_count]]
        column_names = ['timestamp', 'user_id', 'account_id', 'direction', 'status', 'chat_id', 'word_count']
        
        client.insert(
            table='message_analytics',
            database=settings.CLICKHOUSE_SCHEMA,
            data=data,
            column_names=column_names
        )
        return True
    except Exception as e:
        print(f"[ClickHouse Error] Failed to log event: {e}")
        return False

def get_clickhouse_metrics(user_id, days=7):
    """
    Fetch message volume, status ratios, and word counts from ClickHouse.
    """
    client = get_clickhouse_client()
    if client is None:
        return None
        
    try:
        schema = settings.CLICKHOUSE_SCHEMA
        query = f"""
            SELECT 
                toStartOfDay(timestamp) as day,
                count() as msg_count,
                sum(word_count) as total_words,
                countIf(direction = 'outbound') as outbound_count,
                countIf(direction = 'inbound') as inbound_count,
                countIf(status = 'success') as success_count,
                countIf(status = 'failed') as failed_count
            FROM {schema}.message_analytics
            WHERE user_id = %(user_id)s AND timestamp >= subtractDays(now(), %(days)s)
            GROUP BY day
            ORDER BY day ASC
        """
        result = client.query(query, parameters={'user_id': user_id, 'days': days})
        
        metrics = []
        for row in result.result_rows:
            metrics.append({
                'day': row[0].strftime('%Y-%m-%d'),
                'msg_count': row[1],
                'total_words': row[2],
                'outbound_count': row[3],
                'inbound_count': row[4],
                'success_count': row[5],
                'failed_count': row[6]
            })
            
        # Get overall totals
        total_query = f"""
            SELECT 
                count() as total,
                avg(word_count) as avg_words,
                countIf(status = 'success') as success,
                countIf(status = 'failed') as failed
            FROM {schema}.message_analytics
            WHERE user_id = %(user_id)s AND timestamp >= subtractDays(now(), %(days)s)
        """
        total_res = client.query(total_query, parameters={'user_id': user_id, 'days': days})
        totals = total_res.result_rows[0] if total_res.result_rows else [0, 0, 0, 0]
        
        return {
            'daily': metrics,
            'summary': {
                'total': totals[0],
                'avg_words_per_msg': round(float(totals[1] or 0), 1),
                'success_rate': round(float((totals[2] / totals[0] * 100) if totals[0] > 0 else 100), 1),
                'success': totals[2],
                'failed': totals[3]
            }
        }
    except Exception as e:
        print(f"[ClickHouse Error] Failed to fetch metrics: {e}")
        return None
