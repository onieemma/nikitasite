from background_task import background
from base.models import NewsArticle
from base.utils import summarize_article
from django.utils.dateparse import parse_datetime
import feedparser

# Working RSS Feeds
RSS_FEEDS = [
    'https://www.inman.com/feed/',
    'https://www.propertywire.com/feed/',
    'https://www.globest.com/feed/',
    'https://www.housingwire.com/rss/',
    'https://www.realtytimes.com/rss',
]

@background(schedule=5)
def fetch_news_task():
    print("Background task: Fetching news...")

    for feed_url in RSS_FEEDS:
        try:
            d = feedparser.parse(feed_url)

            for entry in d.entries[:20]:
                url = entry.get('link')

                # Avoid duplicates
                if not url or NewsArticle.objects.filter(url=url).exists():
                    continue

                title = entry.get('title') or 'No title'
                raw_content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                published = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
                published_at = parse_datetime(published) if published else None

                # Create the article
                article = NewsArticle.objects.create(
                    source=d.feed.get('title'),
                    title=title,
                    url=url,
                    published_at=published_at,
                    raw_content=raw_content
                )

                # Summarize with AI
                try:
                    article.summary = summarize_article(title, raw_content, url)
                    article.save()
                except Exception as e:
                    print(f"Failed to summarize: {e}")

        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    print("Completed news fetch task.")
