import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.ml import get_hospital_capacity_trends

def test_trends():
    print("Testing get_hospital_capacity_trends...")
    
    # Test for Abia
    print("\n--- Test 1: Abia ---")
    trends_abia = get_hospital_capacity_trends(region="Abia")
    print(f"Number of trend points: {len(trends_abia)}")
    if trends_abia:
        print(f"First trend: {trends_abia[0]}")
        print(f"Last trend: {trends_abia[-1]}")
    else:
        print("No trends returned!")
    
    # Test for All
    print("\n--- Test 2: All ---")
    trends_all = get_hospital_capacity_trends(region="All")
    print(f"Number of trend points: {len(trends_all)}")
    if trends_all:
        print(f"First trend: {trends_all[0]}")
        print(f"Last trend: {trends_all[-1]}")

if __name__ == "__main__":
    test_trends()
