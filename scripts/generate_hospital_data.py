import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# List of states from outbreak_dataset.csv
STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", 
    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "FCT", "Gombe", "Imo", 
    "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", 
    "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", 
    "Yobe", "Zamfara"
]

# Approximate coordinates for states (Center Lat, Center Lon)
STATE_COORDS = {
    "Abia": (5.45, 7.50), "Adamawa": (9.33, 12.50), "Akwa Ibom": (5.05, 7.93), "Anambra": (6.20, 7.00),
    "Bauchi": (10.63, 10.08), "Bayelsa": (4.75, 6.08), "Benue": (7.33, 8.75), "Borno": (11.83, 13.15),
    "Cross River": (5.87, 8.50), "Delta": (5.70, 6.00), "Ebonyi": (6.25, 8.08), "Edo": (6.50, 6.00),
    "Ekiti": (7.63, 5.22), "Enugu": (6.50, 7.50), "FCT": (9.08, 7.40), "Gombe": (10.28, 11.17),
    "Imo": (5.48, 7.03), "Jigawa": (12.00, 9.75), "Kaduna": (10.52, 7.43), "Kano": (11.50, 8.50),
    "Katsina": (12.25, 7.50), "Kebbi": (11.50, 4.00), "Kogi": (7.75, 6.75), "Kwara": (8.50, 4.55),
    "Lagos": (6.52, 3.38), "Nasarawa": (8.50, 8.50), "Niger": (10.00, 6.00), "Ogun": (7.00, 3.58),
    "Ondo": (7.17, 5.08), "Osun": (7.50, 4.50), "Oyo": (8.00, 4.00), "Plateau": (9.17, 9.75),
    "Rivers": (4.75, 6.83), "Sokoto": (13.00, 5.25), "Taraba": (8.00, 10.50), "Yobe": (12.00, 11.50),
    "Zamfara": (12.17, 6.25)
}

def generate_hospital_data():
    print("Generating synthetic hospital data...")
    
    records = []
    
    # Generate data for the last 52 weeks
    current_year = 2025
    weeks = list(range(1, 53))
    
    hospital_counter = 1
    
    for state in STATES:
        # Number of hospitals in this state (random between 5 and 15)
        num_hospitals = random.randint(5, 15)
        
        # Base coordinates for the state
        base_lat, base_lon = STATE_COORDS.get(state, (9.0, 8.0))
        
        for _ in range(num_hospitals):
            hosp_id = f"HOSP_{hospital_counter:03d}"
            hosp_name = f"{state} {random.choice(['General Hospital', 'Medical Centre', 'Specialist Hospital', 'Clinic'])} {random.randint(1, 99)}"
            hospital_counter += 1
            
            # Static attributes for this hospital
            total_beds = random.randint(20, 200)
            icu_beds = max(0, int(total_beds * random.uniform(0.05, 0.15)))
            staff = int(total_beds * random.uniform(0.5, 1.5))
            
            # Location jitter
            lat = base_lat + random.uniform(-0.3, 0.3)
            lon = base_lon + random.uniform(-0.3, 0.3)
            
            # Generate weekly data
            for week in weeks:
                # Time-varying attributes
                admissions = random.randint(int(total_beds * 0.1), int(total_beds * 0.8))
                cases = int(admissions * random.uniform(0.1, 0.4))
                ppe_score = random.uniform(0.5, 1.0)
                
                # Calculate beds available (inverse of occupancy roughly)
                # Note: The CSV format in the example had 'beds', 'icu_beds', 'beds_per_10k'
                # It didn't explicitly have 'beds_available', but get_hospital_capacity_trends calculates it from 'beds' - 'beds_available'?
                # Wait, let's check the code reading it.
                # get_hospital_capacity_trends reads: beds_available = row["beds_available"]
                # But the sample CSV I saw earlier had: beds, icu_beds, beds_per_10k, ppe..., staff..., admissions, recorded_cases
                # It DID NOT have beds_available in the header I saw!
                # Let's verify the header again.
                # The header was: hospital_id,facility,year,week,state,beds,icu_beds,beds_per_10k,ppe_availability_score,staff_count,admissions,recorded_cases,latitude,longitude
                # So 'beds_available' is missing?
                # If the backend expects it, I should add it.
                # Let's add 'beds_available' to be safe.
                
                beds_available = max(0, total_beds - admissions)
                
                records.append({
                    "hospital_id": hosp_id,
                    "facility": hosp_name,
                    "year": current_year,
                    "week": week,
                    "state": state,
                    "beds": total_beds,
                    "icu_beds": icu_beds,
                    "beds_available": beds_available, # Adding this column
                    "beds_per_10k": round(total_beds / 100, 2), # Dummy metric
                    "ppe_availability_score": round(ppe_score, 3),
                    "staff_count": staff,
                    "admissions": admissions,
                    "recorded_cases": cases,
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6)
                })
                
    df = pd.DataFrame(records)
    output_path = "data/hospital/hospitals.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} records for {hospital_counter-1} hospitals across {len(STATES)} states.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    generate_hospital_data()
