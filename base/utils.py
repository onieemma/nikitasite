# # import os

# # OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# # def summarize_article(title, content, url):
# #     """
# #     Summarize the article in 1 paragraph suitable for a real-estate audience.
# #     Returns summary text.
# #     """
# #     if not OPENAI_API_KEY:
# #         # Fallback if no API key: take first 300 chars
# #         return (content or '')[:300] + ('...' if len(content or '') > 300 else '')

# #     try:
# #         import openai
# #         openai.api_key = OPENAI_API_KEY

# #         prompt = (
# #             f"Summarize the following real-estate news article in 1 clear paragraph. "
# #             f"Audience: real estate investors and property buyers.\n\n"
# #             f"Title: {title}\n\n"
# #             f"Content/Excerpt: {content or 'No content provided.'}\n\n"
# #             f"Article URL: {url}\n\n"
# #             f"Return plain text summary only."
# #         )

# #         response = openai.ChatCompletion.create(
# #             model="gpt-4o-mini",
# #             messages=[{"role": "user", "content": prompt}],
# #             max_tokens=200,
# #             temperature=0.2
# #         )
# #         summary = response['choices'][0]['message']['content'].strip()
# #         return summary[:1000]  # limit length
# #     except Exception as e:
# #         return (content or '')[:300] + ('...' if len(content or '') > 300 else '')



# import os
# import logging

# logger = logging.getLogger(__name__)

# def summarize_article(title, content, url, timeout=10):
#     """
#     Summarize the article in 1 paragraph for real estate investors/buyers.
#     Falls back safely if OpenAI is unavailable.
#     """
#     api_key = os.getenv("OPENAI_API_KEY")

#     # If no API key, fallback immediately
#     if not api_key:
#         return fallback_summary(content)

#     try:
#         from openai import OpenAI

#         client = OpenAI(api_key=api_key)

#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": (
#                         "Summarize the following real-estate news article "
#                         "in 1 clear paragraph for investors and buyers.\n\n"
#                         f"Title: {title}\n\n"
#                         f"Content: {content or 'No content'}"
#                     ),
#                 }
#             ],
#             max_tokens=200,
#             temperature=0.2,
#             timeout=timeout,
#         )

#         return response.choices[0].message.content.strip()[:1000]

#     except Exception as e:
#         logger.warning(f"OpenAI summarization failed: {e}")
#         return fallback_summary(content)


# def fallback_summary(content):
#     return (content or "")[:300] + ("..." if len(content or "") > 300 else "")




# ============================================================================
# UPDATED UTILS (base/utils.py)
# ============================================================================

import os
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def summarize_article(title, content, url):
    """
    Summarize the article in 1 paragraph suitable for a real-estate audience.
    Uses the NEW OpenAI API format (v1.0+)
    """
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found, using fallback summary")
        return (content or '')[:300] + ('...' if len(content or '') > 300 else '')

    try:
        # NEW: Use the updated OpenAI client
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = (
            f"Summarize the following real-estate news article in 1 clear paragraph "
            f"(2-3 sentences max). Target audience: real estate investors and property buyers.\n\n"
            f"Title: {title}\n\n"
            f"Content: {(content or 'No content provided.')[:1000]}\n\n"  # Limit input
            f"URL: {url}\n\n"
            f"Provide a concise summary focusing on key facts and implications."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Most cost-effective model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Successfully summarized article: {title[:50]}...")
        return summary[:800]  # Reasonable limit
        
    except ImportError:
        logger.error("OpenAI package not installed. Run: pip install openai")
        return (content or '')[:300] + ('...' if len(content or '') > 300 else '')
    except Exception as e:
        logger.error(f"Failed to summarize article '{title}': {str(e)}")
        return (content or '')[:300] + ('...' if len(content or '') > 300 else '')
