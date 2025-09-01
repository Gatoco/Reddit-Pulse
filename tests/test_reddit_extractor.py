
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the project root to the Python path to allow imports from other directories
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reddit_ingestion_cf.main import load_reddit_credentials, RedditExtractor

# --- Mock Data and Classes ---

class MockAuthor:
    """A mock for the PRAW Author object."""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

class MockSubreddit:
    """A mock for the PRAW Subreddit object."""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

class MockSubmission:
    """A mock for the PRAW Submission object."""
    def __init__(self, id, title, score, num_comments, author_name, created_utc, url, selftext, subreddit_name):
        self.id = id
        self.title = title
        self.score = score
        self.num_comments = num_comments
        self.author = MockAuthor(author_name) if author_name is not None else None
        self.created_utc = created_utc
        self.url = url
        self.selftext = selftext
        self.subreddit = MockSubreddit(subreddit_name)

@pytest.fixture
def mock_post():
    """Fixture to create a standard mock post."""
    return MockSubmission(
        id="test_id",
        title="Test Title",
        score=100,
        num_comments=10,
        author_name="test_author",
        created_utc=1672531200,  # 2023-01-01 00:00:00 UTC
        url="http://test.url",
        selftext="This is a test post.",
        subreddit_name="test_subreddit"
    )

# --- Tests ---

def test_format_post_data(mock_post):
    """
    Tests that the data formatting function correctly structures the post data.
    """
    formatted_data = RedditExtractor.format_post_data(mock_post)

    assert formatted_data["id"] == "test_id"
    assert formatted_data["title"] == "Test Title"
    assert formatted_data["author"] == "test_author"
    assert formatted_data["created_utc"] == "2023-01-01T00:00:00"
    assert "extraction_timestamp" in formatted_data

def test_format_post_data_deleted_author(mock_post):
    """
    Tests the formatting function when a post's author has been deleted.
    """
    mock_post.author = None
    formatted_data = RedditExtractor.format_post_data(mock_post)
    assert formatted_data["author"] == "None"

@patch('reddit_ingestion_cf.main.praw.Reddit')
def test_extract_posts(mock_reddit, mock_post):
    """
    Tests the main post extraction logic, ensuring mocks are called correctly.
    """
    # Configure the mock
    mock_instance = mock_reddit.return_value
    mock_instance.subreddit.return_value.hot.return_value = [mock_post]

    # Instantiate the extractor with mock credentials
    extractor = RedditExtractor(credentials={"client_id": "fake", "client_secret": "fake", "user_agent": "fake"})
    
    # Call the method
    posts = extractor.extract_posts("test_subreddit", limit=1)

    # Assertions
    mock_instance.subreddit.assert_called_once_with("test_subreddit")
    assert len(posts) == 1
    assert posts[0]["id"] == "test_id"

@patch('reddit_ingestion_cf.main.load_dotenv')
@patch.dict(os.environ, {}, clear=True)
def test_load_credentials_failure(mock_load_dotenv):
    """
    Tests that loading credentials fails when environment variables are not set.
    """
    with pytest.raises(ValueError, match="Missing Reddit credentials."):
        load_reddit_credentials()

@patch.dict(os.environ, {
    "REDDIT_CLIENT_ID": "test_id",
    "REDDIT_CLIENT_SECRET": "test_secret",
    "REDDIT_USER_AGENT": "test_agent"
})
def test_load_credentials_success():
    """
    Tests that loading credentials succeeds when environment variables are set.
    """
    credentials = load_reddit_credentials()
    assert credentials["client_id"] == "test_id"
    assert credentials["client_secret"] == "test_secret"
    assert credentials["user_agent"] == "test_agent"
