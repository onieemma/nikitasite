import requests

def get_books_from_gutendex(subject="finance"):
    """Fetch free public-domain books from Gutendex API"""
    try:
        url = f"https://gutendex.com/books?topic={subject}&languages=en"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            books = []
            
            for item in data.get('results', [])[:30]:
                books.append({
                    'title': item['title'],
                    'author': ", ".join([a['name'] for a in item['authors']]) if item['authors'] else '',
                    'download_link': item['formats'].get('application/epub+zip') or item['formats'].get('text/plain; charset=utf-8'),
                    'cover_image': item['formats'].get('image/jpeg', ''),
                    'source': 'Gutendex',
                })
            return books
    except Exception as e:
        print(f"Gutendex API error: {e}")
        return []