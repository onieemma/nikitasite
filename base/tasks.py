# from background_task import background
# from base.models import NewsArticle
# from base.utils import summarize_article
# from django.utils.dateparse import parse_datetime
# import feedparser

# # Working RSS Feeds
# RSS_FEEDS = [
#     'https://www.inman.com/feed/',
#     'https://www.propertywire.com/feed/',
#     'https://www.globest.com/feed/',
#     'https://www.housingwire.com/rss/',
#     'https://www.realtytimes.com/rss',
# ]

# @background(schedule=5)
# def fetch_news_task():
#     print("Background task: Fetching news...")

#     for feed_url in RSS_FEEDS:
#         try:
#             d = feedparser.parse(feed_url)

#             for entry in d.entries[:20]:
#                 url = entry.get('link')

#                 # Avoid duplicates
#                 if not url or NewsArticle.objects.filter(url=url).exists():
#                     continue

#                 title = entry.get('title') or 'No title'
#                 raw_content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
#                 published = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
#                 published_at = parse_datetime(published) if published else None

#                 # Create the article
#                 article = NewsArticle.objects.create(
#                     source=d.feed.get('title'),
#                     title=title,
#                     url=url,
#                     published_at=published_at,
#                     raw_content=raw_content
#                 )

#                 # Summarize with AI
#                 try:
#                     article.summary = summarize_article(title, raw_content, url)
#                     article.save()
#                 except Exception as e:
#                     print(f"Failed to summarize: {e}")

#         except Exception as e:
#             print(f"Error fetching {feed_url}: {e}")

#     print("Completed news fetch task.")






from background_task import background
from base.models import NewsArticle
from base.utils import summarize_article
from django.utils.dateparse import parse_datetime
import feedparser
import logging

logger = logging.getLogger(__name__)

# Working RSS Feeds
RSS_FEEDS = [
    'https://www.inman.com/feed/',
    'https://www.propertywire.com/feed/',
    'https://www.globest.com/feed/',
    'https://www.housingwire.com/rss/',
    'https://www.realtytimes.com/rss',
]


@background(schedule=0)  # Schedule=0 means run immediately when called
def fetch_news_task():
    """
    Background task to fetch news from RSS feeds.
    This runs in the background without blocking the main application.
    """
    logger.info("=" * 60)
    logger.info("Background task: Starting news fetch...")
    logger.info("=" * 60)
    
    total_new = 0
    total_errors = 0

    for feed_url in RSS_FEEDS:
        try:
            logger.info(f"Fetching from: {feed_url}")
            d = feedparser.parse(feed_url)
            
            if not d.entries:
                logger.warning(f"  No entries found for {feed_url}")
                continue

            feed_new = 0
            for entry in d.entries[:20]:  # Latest 20 articles
                try:
                    url = entry.get('link')

                    # Skip if no URL or already exists
                    if not url or NewsArticle.objects.filter(url=url).exists():
                        continue

                    title = entry.get('title', 'No title')[:1000]
                    raw_content = (
                        getattr(entry, 'summary', '') or 
                        getattr(entry, 'description', '') or
                        getattr(entry, 'content', [{}])[0].get('value', '')
                    )[:5000]
                    
                    published = (
                        getattr(entry, 'published', None) or 
                        getattr(entry, 'updated', None)
                    )
                    published_at = parse_datetime(published) if published else None
                    
                    # Extract image
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        image_url = entry.enclosures[0].get('href')

                    # Create article
                    article = NewsArticle.objects.create(
                        source=d.feed.get('title', 'Unknown Source'),
                        title=title,
                        url=url,
                        published_at=published_at,
                        raw_content=raw_content,
                        image_url=image_url
                    )

                    # Summarize with AI
                    try:
                        article.summary = summarize_article(title, raw_content, url)
                        article.save()
                        feed_new += 1
                        logger.info(f"  ✓ Created: {title[:60]}...")
                    except Exception as e:
                        logger.error(f"  ✗ Failed to summarize '{title}': {str(e)}")
                        # Article saved but without summary
                        
                except Exception as e:
                    logger.error(f"  ✗ Error processing article: {str(e)}")
                    total_errors += 1
                    continue
                    
            logger.info(f"  Feed complete: {feed_new} new articles")
            total_new += feed_new

        except Exception as e:
            logger.error(f"✗ Error fetching {feed_url}: {str(e)}")
            total_errors += 1

    logger.info("=" * 60)
    logger.info(
        f"News fetch completed: {total_new} new articles, {total_errors} errors"
    )
    logger.info("=" * 60)