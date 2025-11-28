import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.routers.hospitals import get_capacity_trends

def test_trends_endpoint():
    print("Testing get_capacity_trends endpoint...")
    
    # Simulate what the frontend sends
    print("\n--- Test 1: With ISO datetime params (like frontend sends) ---")
    result = get_capacity_trends(
        region="Abia",
        startDate="2025-05-01T00:00:00Z",  # ISO datetime
        endDate="2025-12-31T23:59:59Z"     # ISO datetime
    )
    print(f"Region: {result['region']}")
    print(f"Number of trends: {len(result['trends'])}")
    if result['trends']:
        print(f"First trend: {result['trends'][0]}")
        print(f"Last trend: {result['trends'][-1]}")
    
    print("\n--- Test 2: Without date params ---")
    result2 = get_capacity_trends(region="Abia")
    print(f"Number of trends: {len(result2['trends'])}")

if __name__ == "__main__":
    test_trends_endpoint()
