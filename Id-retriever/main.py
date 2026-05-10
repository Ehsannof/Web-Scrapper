"""
Dependencies:
    pip install requests
 
Usage:
    python main.py
"""

import requests 
import time      
import json      
import os         

# Configuration
CATEGORY_SLUG = "laptop"

TARGET_COUNT = 250   

OUTPUT_FILE_PATH = "../../Data/digikala_product_ids.json"

DELAY_SECONDS = 3

# API Configuration
BASE_URL = "https://api.digikala.com/v1/categories/{slug}/search/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa,en;q=0.9",
    "Referer": f"https://www.digikala.com/landing/{CATEGORY_SLUG}/",
}

def fetch_product_ids_from_page(slug: str, page: int) -> list[int]:
    """ 
    Args:
        slug: Category identifier extracted from the Digikala URL.
        page: 1-based page index to request.
 
    Returns:
        List of integer product IDs found on the page.
        Returns an empty list on any request or parsing failure.
    """

    url = BASE_URL.format(slug=slug)

    params = {
        "page": page,
        "sort": 1,       
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)

        response.raise_for_status()  

        data = response.json()

        products = data.get("data", {}).get("products", [])

        if not products:
            print(f"Page {page}: no products found. Category may have ended.")
            return []

        ids = [int(p["id"]) for p in products if "id" in p]

        print(f"Page {page}: found {len(ids)} product IDs")
        return ids

    except requests.exceptions.HTTPError as e:
        print(f"Page {page}: HTTP error – {e}")
        return []

    except requests.exceptions.ConnectionError:
        print(f"Page {page}: connection failed. Check your internet.")
        return []

    except requests.exceptions.Timeout:
        print(f"Page {page}: request timed out.")
        return []

    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"Page {page}: could not parse response – {e}")
        return []

def collect_product_ids(slug: str, target: int) -> list[int]:
    """
    Args:
        slug:   Category slug to query.
        target: Minimum number of unique IDs to collect.
 
    Returns:
        Sorted, deduplicated list of product IDs.
    """

    print(f"Scraping category: '{slug}'")
    print(f"Target: {target} product IDs\n")

    all_ids = set() 
    page = 1

    while len(all_ids) < target:

        print(f"Fetching page {page}…")
        ids_on_page = fetch_product_ids_from_page(slug, page)

        if not ids_on_page:

            print(f"No more products available. Stopping at page {page}.")
            break

        all_ids.update(ids_on_page)  
        print(f"Total collected so far: {len(all_ids)}")

        page += 1

        if len(all_ids) < target:
            time.sleep(DELAY_SECONDS)

    print(f"Done! Collected {len(all_ids)} unique product IDs.")
    return sorted(all_ids)   

def save_ids(ids: list[int], filepath: str) -> None:
    """
    Output schema:
        {
            "category": str,
            "total": int,
            "product_ids": list[int]
        }
 
    Args:
        ids:      Sorted list of product IDs to serialize.
        filepath: Destination file path.
    """
    payload = {
        "category": CATEGORY_SLUG,
        "total": len(ids),
        "product_ids": ids,
    }
 
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
 
    print(f"Output saved to: {os.path.abspath(filepath)}")
 
 

if __name__ == "__main__":

    product_ids = collect_product_ids(CATEGORY_SLUG, TARGET_COUNT)

    if product_ids:
        save_ids(product_ids, OUTPUT_FILE_PATH)

    else:
        print("No product IDs were collected. Check your slug or internet connection.")
