import os

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def summarize_article(title, content, url):
    """
    Summarize the article in 1 paragraph suitable for a real-estate audience.
    Returns summary text.
    """
    if not OPENAI_API_KEY:
        # Fallback if no API key: take first 300 chars
        return (content or '')[:300] + ('...' if len(content or '') > 300 else '')

    try:
        import openai
        openai.api_key = OPENAI_API_KEY

        prompt = (
            f"Summarize the following real-estate news article in 1 clear paragraph. "
            f"Audience: real estate investors and property buyers.\n\n"
            f"Title: {title}\n\n"
            f"Content/Excerpt: {content or 'No content provided.'}\n\n"
            f"Article URL: {url}\n\n"
            f"Return plain text summary only."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.2
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary[:1000]  # limit length
    except Exception as e:
        return (content or '')[:300] + ('...' if len(content or '') > 300 else '')
