import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.ml import get_population

def test_population_filter():
    print("Testing get_population filtering...")
    
    # Test 1: All Nigeria
    print("\n--- Test 1: All Nigeria ---")
    res_all = get_population(region="All")
    print(f"Region: {res_all.region}")
    print(f"Total Population: {res_all.totalPopulation:,.0f}")
    print(f"Number of States: {len(res_all.growthRates)}")
    
    if res_all.totalPopulation > 0 and len(res_all.growthRates) > 1:
        print("SUCCESS: 'All' returns aggregated data.")
    else:
        print("FAILURE: 'All' returned empty or invalid data.")

    # Test 2: Specific Region (e.g., Lagos)
    print("\n--- Test 2: Lagos ---")
    res_lagos = get_population(region="Lagos")
    print(f"Region: {res_lagos.region}")
    print(f"Total Population: {res_lagos.totalPopulation:,.0f}")
    print(f"Number of States: {len(res_all.growthRates)}") # Should be 1 or just Lagos entry
    
    # Verify filtering
    if res_lagos.totalPopulation < res_all.totalPopulation and res_lagos.totalPopulation > 0:
        print("SUCCESS: Lagos population is smaller than Total.")
    else:
        print(f"FAILURE: Lagos population ({res_lagos.totalPopulation}) seems incorrect vs Total ({res_all.totalPopulation}).")

    # Test 3: Another Region (e.g., Kano)
    print("\n--- Test 3: Kano ---")
    res_kano = get_population(region="Kano")
    print(f"Region: {res_kano.region}")
    print(f"Total Population: {res_kano.totalPopulation:,.0f}")
    
    if res_kano.totalPopulation != res_lagos.totalPopulation:
         print("SUCCESS: Kano population differs from Lagos.")
    else:
         print("FAILURE: Kano and Lagos have same population (unlikely).")

if __name__ == "__main__":
    test_population_filter()
