import feedparser
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from base.models import NewsArticle
from base.utils import summarize_article

# Global real estate RSS feed
   # Global real estate RSS feeds
RSS_FEEDS = [
    'https://www.inman.com/feed/',
    'https://www.propertywire.com/feed/',
    'https://www.globest.com/feed/',
    'https://www.housingwire.com/rss/',
    'https://www.realtytimes.com/rss',
]
  # replace with valid feed


class Command(BaseCommand):
    help = "Fetch real estate news from RSS feeds and summarize with AI"

    def handle(self, *args, **options):
        self.stdout.write("Starting news fetch...")
        for feed_url in RSS_FEEDS:
            try:
                d = feedparser.parse(feed_url)
                for entry in d.entries[:20]:  # latest 20 per feed
                    url = entry.get('link')
                    if not url or NewsArticle.objects.filter(url=url).exists():
                        continue
                    title = entry.get('title') or 'No title'
                    raw_content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    published = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
                    published_at = parse_datetime(published) if published else None

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
                        self.stdout.write(f"Saved & summarized: {title}")
                    except Exception as e:
                        self.stdout.write(f"Failed summarizing {title}: {e}")
            except Exception as e:
                self.stdout.write(f"Failed fetching feed {feed_url}: {e}")
        self.stdout.write("News fetch complete.")
