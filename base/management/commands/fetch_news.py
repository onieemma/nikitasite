# import feedparser
# from django.core.management.base import BaseCommand
# from django.utils.dateparse import parse_datetime
# from base.models import NewsArticle
# from base.utils import summarize_article

# # Global real estate RSS feed
#    # Global real estate RSS feeds
# RSS_FEEDS = [
#     'https://www.inman.com/feed/',
#     'https://www.propertywire.com/feed/',
#     'https://www.globest.com/feed/',
#     'https://www.housingwire.com/rss/',
#     'https://www.realtytimes.com/rss',
# ]
#   # replace with valid feed


# class Command(BaseCommand):
#     help = "Fetch real estate news from RSS feeds and summarize with AI"

#     def handle(self, *args, **options):
#         self.stdout.write("Starting news fetch...")
#         for feed_url in RSS_FEEDS:
#             try:
#                 d = feedparser.parse(feed_url)
#                 for entry in d.entries[:20]:  # latest 20 per feed
#                     url = entry.get('link')
#                     if not url or NewsArticle.objects.filter(url=url).exists():
#                         continue
#                     title = entry.get('title') or 'No title'
#                     raw_content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
#                     published = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
#                     published_at = parse_datetime(published) if published else None

#                     article = NewsArticle.objects.create(
#                         source=d.feed.get('title'),
#                         title=title,
#                         url=url,
#                         published_at=published_at,
#                         raw_content=raw_content
#                     )

#                     # Summarize with AI
#                     try:
#                         article.summary = summarize_article(title, raw_content, url)
#                         article.save()
#                         self.stdout.write(f"Saved & summarized: {title}")
#                     except Exception as e:
#                         self.stdout.write(f"Failed summarizing {title}: {e}")
#             except Exception as e:
#                 self.stdout.write(f"Failed fetching feed {feed_url}: {e}")
#         self.stdout.write("News fetch complete.")


import feedparser
import logging
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from base.models import NewsArticle
from base.utils import summarize_article

logger = logging.getLogger(__name__)

# Global real estate RSS feeds
RSS_FEEDS = [
    'https://www.inman.com/feed/',
    'https://www.propertywire.com/feed/',
    'https://www.globest.com/feed/',
    'https://www.housingwire.com/rss/',
    'https://www.realtytimes.com/rss',
]


class Command(BaseCommand):
    help = "Fetch real estate news from RSS feeds and summarize with AI"

    def add_arguments(self, parser):
        """Add optional command arguments"""
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of articles to fetch per feed (default: 20)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-summarize existing articles'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        self.stdout.write(self.style.WARNING(f"Starting news fetch (limit: {limit} per feed)..."))
        
        total_new = 0
        total_updated = 0
        total_errors = 0

        for feed_url in RSS_FEEDS:
            try:
                self.stdout.write(f"\nFetching from: {feed_url}")
                d = feedparser.parse(feed_url)
                
                if not d.entries:
                    self.stdout.write(self.style.WARNING(f"  No entries found"))
                    continue
                
                feed_new = 0
                feed_updated = 0
                
                for entry in d.entries[:limit]:
                    try:
                        url = entry.get('link')
                        
                        # Skip if no URL
                        if not url:
                            continue
                        
                        # Check if already exists
                        existing = NewsArticle.objects.filter(url=url).first()
                        if existing and not force:
                            continue
                        
                        # Extract data
                        title = entry.get('title', 'No title')[:1000]  # Limit length
                        raw_content = (
                            getattr(entry, 'summary', '') or 
                            getattr(entry, 'description', '') or
                            getattr(entry, 'content', [{}])[0].get('value', '')
                        )[:5000]  # Limit to prevent bloat
                        
                        published = (
                            getattr(entry, 'published', None) or 
                            getattr(entry, 'updated', None)
                        )
                        published_at = parse_datetime(published) if published else None
                        
                        # Extract image if available
                        image_url = None
                        if hasattr(entry, 'media_content') and entry.media_content:
                            image_url = entry.media_content[0].get('url')
                        elif hasattr(entry, 'enclosures') and entry.enclosures:
                            image_url = entry.enclosures[0].get('href')

                        # Create or update article
                        if existing:
                            article = existing
                            self.stdout.write(f"  Updating: {title[:60]}...")
                        else:
                            article = NewsArticle.objects.create(
                                source=d.feed.get('title', 'Unknown Source'),
                                title=title,
                                url=url,
                                published_at=published_at,
                                raw_content=raw_content,
                                image_url=image_url
                            )
                            self.stdout.write(self.style.SUCCESS(f"  Created: {title[:60]}..."))

                        # Summarize with AI
                        try:
                            article.summary = summarize_article(title, raw_content, url)
                            article.save()
                            
                            if existing:
                                feed_updated += 1
                            else:
                                feed_new += 1
                                
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"  Failed summarizing: {str(e)}")
                            )
                            total_errors += 1
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  Error processing article: {str(e)}")
                        )
                        total_errors += 1
                        continue
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Feed complete: {feed_new} new, {feed_updated} updated"
                    )
                )
                total_new += feed_new
                total_updated += feed_updated
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Failed fetching feed: {str(e)}")
                )
                total_errors += 1

        # Final summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(
                f"News fetch complete!\n"
                f"  • New articles: {total_new}\n"
                f"  • Updated articles: {total_updated}\n"
                f"  • Errors: {total_errors}"
            )
        )
        self.stdout.write("="*60)
