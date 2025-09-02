"""
Reddit Ingestion Cloud Function
This script contains the logic for a Google Cloud Function that extracts, transforms,
and loads data from Reddit into Google Cloud Platform services.
"""

import os
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import praw
from prawcore.exceptions import PrawcoreException
import concurrent.futures
from google.api_core import exceptions as google_exceptions
from google.cloud import pubsub_v1, storage, monitoring_v3, secretmanager
from google.protobuf.timestamp_pb2 import Timestamp

# --- Structured Logging Configuration ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

setup_logging()

# --- Constants ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# --- Credential Loading ---
def load_reddit_credentials_from_secret_manager(project_id, secret_id, version_id="latest"):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(name=name)
        payload = response.payload.data.decode("UTF-8")
        credentials = json.loads(payload)
        logging.info(f"Successfully loaded Reddit credentials from Secret Manager: {secret_id}")
        return credentials
    except Exception as e:
        logging.error("Failed to load credentials from Secret Manager", exc_info=True)
        raise

# --- Metrics Class ---
class MetricsManager:
    def __init__(self, project_id):
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

    def _create_time_series(self, metric_name, value):
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/{metric_name}"
        series.resource.type = "global"
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10**9)
        interval = monitoring_v3.TimeInterval(end_time=Timestamp(seconds=seconds, nanos=nanos))
        point = monitoring_v3.Point(interval=interval)
        point.value.int64_value = value
        series.points = [point]
        return series

    def increment_posts_extracted(self, count=1):
        series = self._create_time_series("posts_extracted_total", count)
        self.client.create_time_series(name=self.project_name, time_series=[series])
        logging.info(f"Metric 'posts_extracted_total' incremented by {count}.")

    def record_pubsub_latency(self, duration_ms):
        series = self._create_time_series("pubsub_publish_duration_ms", int(duration_ms))
        self.client.create_time_series(name=self.project_name, time_series=[series])
        logging.info(f"Metric 'pubsub_publish_duration_ms' recorded: {duration_ms} ms.")

    def increment_gcs_uploads(self, success=True):
        metric_name = "gcs_upload_success_total" if success else "gcs_upload_failure_total"
        series = self._create_time_series(metric_name, 1)
        self.client.create_time_series(name=self.project_name, time_series=[series])
        logging.info(f"Metric '{metric_name}' incremented.")

# --- Service Classes ---
class RedditExtractor:
    def __init__(self, credentials, metrics_manager=None):
        self.reddit = praw.Reddit(**credentials)
        self.metrics = metrics_manager
        logging.info(f"PRAW instance created. Read-only mode: {self.reddit.read_only}")

    def extract_posts(self, subreddit_name, limit=10):
        for attempt in range(MAX_RETRIES):
            try:
                logging.info(f"Attempt {attempt + 1} to extract from r/{subreddit_name}...")
                posts = list(subreddit.hot(limit=limit))
                if self.metrics:
                    self.metrics.increment_posts_extracted(len(posts))
                return [self.format_post_data(post) for post in posts]
            except PrawcoreException as e:
                logging.warning(f"Network error extracting from Reddit: {e}. Retrying...", exc_info=True)
                if attempt == MAX_RETRIES - 1:
                    logging.error(f"Final attempt failed to extract from Reddit for r/{subreddit_name}")
                    raise
                time.sleep(RETRY_DELAY_SECONDS)
        return []

    @staticmethod
    def format_post_data(post):
        return {
            "id": post.id,
            "title": post.title,
            "score": post.score,
            "num_comments": post.num_comments,
            "author": str(post.author),
            "created_utc": datetime.utcfromtimestamp(post.created_utc).isoformat(),
            "url": post.url,
            "selftext": post.selftext,
            "subreddit": str(post.subreddit),
            "extraction_timestamp": datetime.utcnow().isoformat()
        }

class PubSubPublisher:
    def __init__(self, project_id, topic_name, dead_letter_topic_name=None, metrics_manager=None):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
        self.metrics = metrics_manager
        self._dlq_publisher = None
        if dead_letter_topic_name:
            self._dlq_publisher = pubsub_v1.PublisherClient()
            self._dlq_topic_path = self._dlq_publisher.topic_path(project_id, dead_letter_topic_name)
            logging.info(f"Dead-letter queue configured: {dead_letter_topic_name}")

    def publish_message(self, data):
        message_data = json.dumps(data, default=str).encode("utf-8")
        start_time = time.time()
        try:
            future = self.publisher.publish(self.topic_path, message_data)
            message_id = future.result(timeout=60)
            duration_ms = (time.time() - start_time) * 1000
            if self.metrics:
                self.metrics.record_pubsub_latency(duration_ms)
            logging.info(f"Published message ID: {message_id} to {self.topic_path}")
            return message_id
        except Exception as e:
            logging.error(f"Failed to publish to {self.topic_path}", exc_info=True)
            if self._dlq_publisher:
                logging.warning(f"Forwarding message to DLQ: {self._dlq_topic_path}")
                dlq_future = self._dlq_publisher.publish(self._dlq_topic_path, message_data)
                try:
                    dlq_message_id = dlq_future.result(timeout=60)
                    logging.info(f"Message forwarded to DLQ with ID: {dlq_message_id}")
                except Exception as dlq_e:
                    logging.critical("Failed to publish to DLQ", exc_info=True)
            raise

    def close(self):
        if hasattr(self.publisher.transport, 'close'):
            self.publisher.transport.close()
            logging.info("Primary Pub/Sub publisher closed.")
        if self._dlq_publisher and hasattr(self._dlq_publisher.transport, 'close'):
            self._dlq_publisher.transport.close()
            logging.info("Dead-letter Pub/Sub publisher closed.")

class GCSArchiver:
    def __init__(self, bucket_name, metrics_manager=None):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.metrics = metrics_manager

    def upload_raw_data(self, data, file_path):
        try:
            blob = self.bucket.blob(file_path)
            blob.upload_from_string(
                data=json.dumps(data, indent=4, default=str),
                content_type='application/json'
            )
            if self.metrics:
                self.metrics.increment_gcs_uploads(success=True)
            logging.info(f"Uploaded to gs://{self.bucket.name}/{file_path}")
        except Exception as e:
            if self.metrics:
                self.metrics.increment_gcs_uploads(success=False)
            logging.error("GCS upload failed", exc_info=True)
            raise

    def generate_file_path(self, post_data):
        post_id = post_data['id']
        extraction_ts = datetime.fromisoformat(post_data['extraction_timestamp'])
        year, month, day = extraction_ts.strftime('%Y'), extraction_ts.strftime('%m'), extraction_ts.strftime('%d')
        timestamp_str = extraction_ts.strftime('%Y%m%dT%H%M%S')
        return f"{year}/{month}/{day}/post_{post_id}_{timestamp_str}.json"

# --- Global Client Initialization ---
reddit_extractor = None
pubsub_publisher = None
gcs_archiver = None
metrics_manager = None

try:
    load_dotenv()
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    REDDIT_SECRET_ID = os.getenv("REDDIT_SECRET_ID")
    PUBSUB_TOPIC_NAME = os.getenv("PUBSUB_TOPIC_NAME")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    DEAD_LETTER_TOPIC_NAME = os.getenv("DEAD_LETTER_TOPIC_NAME")

    if not all([GCP_PROJECT_ID, REDDIT_SECRET_ID, PUBSUB_TOPIC_NAME, GCS_BUCKET_NAME]):
        raise ValueError("Missing required environment variables.")

    reddit_credentials = load_reddit_credentials_from_secret_manager(GCP_PROJECT_ID, REDDIT_SECRET_ID)
    metrics_manager = MetricsManager(project_id=GCP_PROJECT_ID)
    reddit_extractor = RedditExtractor(credentials=reddit_credentials, metrics_manager=metrics_manager)
    pubsub_publisher = PubSubPublisher(
        project_id=GCP_PROJECT_ID,
        topic_name=PUBSUB_TOPIC_NAME,
        dead_letter_topic_name=DEAD_LETTER_TOPIC_NAME,
        metrics_manager=metrics_manager
    )
    gcs_archiver = GCSArchiver(bucket_name=GCS_BUCKET_NAME, metrics_manager=metrics_manager)

except Exception as e:
    logging.critical("Failed to initialize global clients", exc_info=True)

# --- Main Logic ---
def validate_post_data(post_data):
    required_fields = ["id", "title", "author", "created_utc", "subreddit"]
    for field in required_fields:
        if field not in post_data or post_data[field] is None:
            raise ValueError(f"Missing or null required field: {field}")
    return True

def process_subreddit_batch(subreddits, extractor, publisher, archiver, post_limit=15):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for subreddit_name in subreddits:
            logging.info(f"--- Processing subreddit: r/{subreddit_name} ---")
            try:
                posts = extractor.extract_posts(subreddit_name=subreddit_name, limit=post_limit)
                logging.info(f"Extracted {len(posts)} posts from r/{subreddit_name}")

                futures = []
                for post in posts:
                    try:
                        validate_post_data(post)
                        post['processing_timestamp'] = datetime.utcnow().isoformat()
                        futures.append(executor.submit(publisher.publish_message, post))
                        file_path = archiver.generate_file_path(post)
                        futures.append(executor.submit(archiver.upload_raw_data, post, file_path))
                    except ValueError as ve:
                        logging.error(f"Validation Error for post {post.get('id')}: {ve}. Skipping post.")
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"A processing task failed: {e}")

            except Exception as e:
                logging.critical(f"FATAL: Failed to process subreddit r/{subreddit_name}: {e}")

# --- Entry Point for Cloud Function ---
def http_trigger(request):
    if not all([reddit_extractor, pubsub_publisher, gcs_archiver]):
        logging.critical("Global clients not initialized. Aborting execution.")
        return ("Internal Server Error: Clients not initialized. Check logs for details.", 500)

    try:
        request_json = request.get_json(silent=True)
        subreddits_str = os.getenv("SUBREDDITS_TO_PROCESS", "technology;datascience")
        if request_json and 'subreddits' in request_json:
            subreddits_str = request_json['subreddits']
        
        subreddits = [s.strip() for s in subreddits_str.split(';')]
        limit = int(os.getenv("DEFAULT_POST_LIMIT", 15))
        if request_json and 'limit' in request_json:
            limit = int(request_json['limit'])

        logging.info(f"HTTP trigger invoked. Processing subreddits: {subreddits} with limit: {limit}")
        process_subreddit_batch(subreddits, reddit_extractor, pubsub_publisher, gcs_archiver, post_limit=limit)
        return ("Batch processing started successfully.", 200)

    except Exception as e:
        logging.critical("Error in HTTP trigger execution", exc_info=True)
        return ("Internal Server Error", 500)

# --- Local Execution Block ---
if __name__ == "__main__":
    if not all([reddit_extractor, pubsub_publisher, gcs_archiver]):
        logging.critical("Could not start local execution due to client initialization failure.")
    else:
        subreddits_to_process = os.getenv("SUBREDDITS_TO_PROCESS", "technology;datascience").split(';')
        default_limit = int(os.getenv("DEFAULT_POST_LIMIT", 15))
        logging.info("--- Starting Local Subreddit Processing Batch ---")
        process_subreddit_batch(subreddits_to_process, reddit_extractor, pubsub_publisher, gcs_archiver, post_limit=default_limit)
        logging.info("--- Local Subreddit Processing Batch Finished ---")

        if pubsub_publisher:
            pubsub_publisher.close()
