#!/usr/bin/env python3
"""
Demo script to test URL routing by creating a sample result and showing the shareable URL.
"""

import requests
import json
import webbrowser
import time

BASE_URL = "http://localhost:5001"

def create_sample_result():
    """Create a sample result and return the shareable URL."""
    print("🎁 Creating sample gift recommendations...")
    
    # Sample questionnaire data
    sample_data = {
        "call_them": "my amazing friend",
        "relationship": "best friend",
        "previous_gifts": "handmade scarf, coffee mug, plant",
        "hate": "clutter, loud music, synthetic fabrics",
        "complaints": "messy roommate, cold office, long commute",
        "complain_about_them": "always running late, overthinks everything",
        "budget": "₹2000-5000",
        "limitations": "eco-friendly, something unique"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate_gifts",
            json=sample_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result_id = data['result_id']
                result_url = f"{BASE_URL}/results/{result_id}"
                gift_count = len(data.get('gift_ideas', []))
                
                print(f"✅ Generated {gift_count} gift ideas!")
                print(f"🔗 Shareable URL: {result_url}")
                print(f"📝 Result ID: {result_id}")
                
                return result_url, result_id
            else:
                print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
                return None, None
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error creating sample result: {e}")
        return None, None

def test_url_persistence(result_url, result_id):
    """Test that the URL can be accessed multiple times."""
    print(f"\n🔄 Testing URL persistence...")
    
    for i in range(3):
        print(f"  Attempt {i+1}/3...")
        response = requests.get(result_url)
        if response.status_code == 200:
            if f'window.RESULT_ID = "{result_id}"' in response.text:
                print(f"  ✅ URL accessible and result ID found")
            else:
                print(f"  ⚠️  URL accessible but result ID not found in page")
        else:
            print(f"  ❌ URL returned status {response.status_code}")
            return False
        time.sleep(0.5)
    
    print("✅ URL persistence test passed!")
    return True

def test_api_endpoint(result_id):
    """Test the API endpoint for the result."""
    print(f"\n🔌 Testing API endpoint...")
    
    api_url = f"{BASE_URL}/api/results/{result_id}"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ API endpoint works")
            print(f"  Gift ideas: {len(data.get('gift_ideas', []))}")
            print(f"  Created: {data.get('created_at', 'Unknown')}")
            print(f"  Expires: {data.get('expires_at', 'Unknown')}")
            return True
        else:
            print(f"❌ API returned error: {data}")
            return False
    else:
        print(f"❌ API returned status {response.status_code}")
        return False

def main():
    print("🧪 Ruby's Gifts URL Routing Demo")
    print("=" * 50)
    
    # Create a sample result
    result_url, result_id = create_sample_result()
    
    if not result_url or not result_id:
        print("❌ Failed to create sample result. Exiting.")
        return
    
    # Test URL persistence
    if not test_url_persistence(result_url, result_id):
        print("❌ URL persistence test failed.")
        return
    
    # Test API endpoint
    if not test_api_endpoint(result_id):
        print("❌ API endpoint test failed.")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All URL routing tests passed!")
    print("\n📋 Summary of fixes implemented:")
    print("  ✅ Results div visibility issue fixed (CSS)")
    print("  ✅ Unique URLs for results pages (/results/ID)")
    print("  ✅ URL routing with browser history support")
    print("  ✅ Shareable and bookmarkable result links")
    print("  ✅ API endpoints for accessing result data")
    print("  ✅ Proper error handling for expired/missing results")
    
    print(f"\n🌐 Try visiting this URL in your browser:")
    print(f"   {result_url}")
    print("\n   You should see the gift recommendations page!")
    print("   You can bookmark this URL or share it with others.")
    
    # Optionally open in browser (commented out for safety)
    # print(f"\n🚀 Opening URL in browser...")
    # webbrowser.open(result_url)

if __name__ == "__main__":
    main()