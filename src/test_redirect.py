"""Test script to compare different redirect resolution methods."""

import requests
import time

# Sample Google redirect URLs from your RSS feed
TEST_URLS = [
    "https://news.google.com/rss/articles/CBMikgFBVV95cUxQM1h6eFVFRjlqZGMzMnNqQ19KMENfZDQ2T3JTZWRNeHRxSFZRMmVGTFJBME5TY3I4TmRVd2dPWUNTNTRnTUkyU0huWXJIN0UzdkZKM1BtR2k3YnRJQW1IUDFxME5nR2pqeVF6cUhDWktnU0stYTlwendiU1U5NzFwOXh2Zkhvd3hIVXE0WkpsbEJvUdIBlwFBVV95cUxNRDZRV3YxdG01ejd0U2NPRUdDZ1VBZlJQM3RaS2dqMW93RDhXZFFxUWJ1cFYyWFI2YnlKWHRGVXM2N2hpeDYzazZfRWMzejh2RXNRQTVkOUpUdG1oemF3RmVod3I3WWo2ZnBEeWFnRUJFRmYxQXhkRmdtcXZUYkxwZ084SzZNb3ZrVzVoaEhaelNpV2MwYTRJ?oc=5",
    "https://news.google.com/rss/articles/CBMixwFBVV95cUxNUy1KMVRfdnJwcEFmazVLNWcyMU9MVlhUY3IyX3VWdlBydnJZTUdKWkMtNUhWSFVsS0NjZFhwTTJrTGtwQV9qV3ZXRE5qVXAwQ2pXOTJQdnI4a3MyQkQwdUlrZENoUjR1M05EdTJHN2xXNmU5Y0hhdDNfU29GMWYxYmtzQzIwRDd3WWUyTFZ0NFl0bDJOVWJlMU80U1IwVzB4WEVDdlVwVmcyMjNtLU9zMVJ6Z2VESG5mVjZ2WXM4eHFqSWYyOVJv0gHMAUFVX3lxTE5WTWxjbzVxTzlMTmhwUWtXV21fUG9JNGh4VGVsLUdXSGVJbGZMSThPLW1RU3FWeDAyYmU3d1BHdHFES2t3eUxid2cydGJhdEY4UWZ3SS1rNlBXSWdOU08wRWVweW1LLUtvM2dCVGR6LTEyeU5BVFBjQ1lpSjZQcERFZU8waDlLZkNDT1FTbVFqSkRqYjBGWmIxSzU3aGx3YnlrWXVIa2g2OXRteHFxWHdMTGU2ak9TVm9aQmJTLWhxZjhoWFo0aHFrS3BLcQ?oc=5",
]


def method_head(url):
    """Method 1: requests.head() - current approach"""
    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        return response.url, "SUCCESS"
    except Exception as e:
        return url, f"FAILED: {e}"


def method_get(url):
    """Method 2: requests.get() - more reliable, downloads body"""
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        return response.url, "SUCCESS"
    except Exception as e:
        return url, f"FAILED: {e}"


def method_get_stream(url):
    """Method 3: requests.get() with stream=True - faster, no body"""
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            stream=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        response.close()
        return response.url, "SUCCESS"
    except Exception as e:
        return url, f"FAILED: {e}"


def main():
    print("=" * 80)
    print("Testing redirect resolution methods on Google News URLs")
    print("=" * 80)

    methods = [
        ("HEAD (current)", method_head),
        ("GET", method_get),
        ("GET stream", method_get_stream),
    ]

    for test_url in TEST_URLS:
        print(f"\n{'=' * 80}")
        print(f"Testing URL: {test_url[:60]}...")
        print("=" * 80)

        for method_name, method_func in methods:
            try:
                start_time = time.time()
                resolved_url, status = method_func(test_url)
                elapsed = time.time() - start_time

                is_resolved = (
                    resolved_url != test_url and "news.google.com" not in resolved_url
                )

                print(f"\n{method_name}:")
                print(f"  Status: {status}")
                print(f"  Time: {elapsed:.2f}s")
                print(f"  Resolved: {'YES' if is_resolved else 'NO'}")
                print(f"  URL: {resolved_url[:80]}")
            except Exception as e:
                print(f"\n{method_name}: ERROR - {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
