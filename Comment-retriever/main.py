import requests
import json
import time
from typing import List, Dict

class DigiKalaCommentCrawler:
    def __init__(self):
        self.base_url = "https://api.digikala.com/v1/rate-review/products/{product_id}/?page={page}"
        self.product_id = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def retrive_product_ID(self) -> list[int]:
        """Extract product ID from JSON"""
        with open("../../Data/digikala_product_ids.json", "r") as f:
            data = json.load(f)
        return(data["product_ids"])
        
    def get_comments(self, page: int) -> Dict:
        """Fetch comments for a specific product and page"""
        url = self.base_url.format(product_id=self.product_id, page=page)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return {}
    
    def crawl_all_comments(self, delay: float) -> List[Dict]:
        """Crawl all comments for a product"""
        all_comments = []
        page = 1
        
        print(f"Starting to crawl comments for product {self.product_id}...")
        
        while True:
            print(f"Fetching page {page}...")
            data = self.get_comments(page)
            
            if not data or data.get('status') != 200:
                print(f"Failed to fetch page {page}")
                break
            
            comments = data.get('data', {}).get('comments', [])
            if not comments:
                print("No more comments found")
                break
            
            all_comments.extend(comments)
            print(f"Collected {len(comments)} comments from page {page}")
            
            pager = data.get('data', {}).get('pager', {})
            current_page = pager.get('current_page', page)
            total_pages = pager.get('total_pages', 1)
            
            if current_page >= total_pages:
                print(f"Reached last page ({total_pages})")
                break
            
            page += 1
            time.sleep(delay)
        
        print(f"\nTotal comments collected: {len(all_comments)}")
        return all_comments
    
    def save_comments(self, comments: List[Dict], filename: str = "comments.json"):
        """Save comments to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        print(f"Comments saved to {filename}")
    
    def extract_buyer_comments(self, comments: List[Dict]) -> List[Dict]:
        """Filter only buyer comments (purchased items)"""
        return [c for c in comments if c.get('is_buyer') == 1]
    
    # def format_comment(self, comment: Dict) -> Dict:
    #     """Extract key information from comment"""
    #     return {
    #         'id': comment.get('id'),
    #         'user_name': comment.get('user_name'),
    #         'is_buyer': comment.get('is_buyer') == 1,
    #         'rate': comment.get('rate'),
    #         'body': comment.get('body'),
    #         'created_at': comment.get('created_at'),
    #         'likes': comment.get('reactions', {}).get('likes', 0),
    #         'dislikes': comment.get('reactions', {}).get('dislikes', 0),
    #         'seller': comment.get('purchased_item', {}).get('seller', {}).get('title'),
    #         'color': comment.get('purchased_item', {}).get('color', {}).get('title')
    #     }
    
    def crawl_from_url(self, delay: float = 1.0, buyers_only: bool = True):
        """Crawl comments directly from product URL"""
        
        product_ids = self.retrive_product_ID()

        if not product_ids:
            print("Could not extract product IDs from file.")
            return

        for id in product_ids:
            self.product_id = id
            
            print(f"Extracted product ID: {id}")
            
            comments = self.crawl_all_comments(delay)
            
            if buyers_only:
                comments = self.extract_buyer_comments(comments)
                print(f"Filtered to {len(comments)} buyer comments")
            
            file_path = f"../../Data/product_{id}_comments.json"
            self.save_comments(comments, file_path)

if __name__ == "__main__":
    crawler = DigiKalaCommentCrawler()
    crawler.crawl_from_url(delay=1.0, buyers_only=True)
