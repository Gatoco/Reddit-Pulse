"""
Reddit Ingestion Cloud Function

This script contains the logic for a Google Cloud Function that extracts, transforms,
and loads data from Reddit into Google Cloud Platform services.

... (docstring as before)
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
from google.cloud import pubsub_v1, storage, monitoring_v3
from google.protobuf.timestamp_pb2 import Timestamp

# --- Structured Logging Configuration ---

class JsonFormatter(logging.Formatter):
    """Formats log records as a JSON string."""
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
    """Configures the root logger for structured JSON logging."""
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

# ... (MetricsManager and other classes with logging instead of print)

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
        # ... (same as before)
        return {}

class PubSubPublisher:
    def __init__(self, project_id, topic_name, dead_letter_topic_name=None, metrics_manager=None):
        # ... (same as before)
        if dead_letter_topic_name:
            logging.info(f"Dead-letter queue configured: {dead_letter_topic_name}")

    def publish_message(self, data):
        # ... (same as before)
        try:
            # ...
            logging.info(f"Published message ID: {message_id} to {self.topic_path}")
            return message_id
        except Exception as e:
            logging.error(f"Failed to publish to {self.topic_path}", exc_info=True)
            if self._dlq_publisher:
                logging.warning(f"Forwarding message to DLQ: {self._dlq_topic_path}")
                # ...
                try:
                    # ...
                    logging.info(f"Message forwarded to DLQ with ID: {dlq_message_id}")
                except Exception as dlq_e:
                    logging.critical("Failed to publish to DLQ", exc_info=True)
            raise

    def close(self):
        # ...
        logging.info("Pub/Sub publishers closed.")

class GCSArchiver:
    # ...
    def upload_raw_data(self, data, file_path):
        # ...
        try:
            # ...
            logging.info(f"Uploaded to gs://{self.bucket.name}/{file_path}")
        except google_exceptions.RetryError as e:
            logging.warning(f"GCS upload retryable error", exc_info=True)
            # ...
        except Exception as e:
            logging.error("GCS upload non-retryable error", exc_info=True)
            # ...
            raise

# ... (the rest of the file with logging)

if __name__ == "__main__":
    # ...
    try:
        # ...
        logging.info("--- Starting Subreddit Processing Batch ---")
        # ...
        logging.info("--- Subreddit Processing Batch Finished ---")
    except Exception as e:
        logging.critical("Unhandled exception during main execution", exc_info=True)
    finally:
        if pubsub_publisher:
            pubsub_publisher.close()