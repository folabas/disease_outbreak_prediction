import pandas as pd

try:
    # Try to read the predictions file
    df = pd.read_csv('reports/production/predictions_live.csv')
    
    # Display basic info about the data
    print("\n=== Predictions File Overview ===")
    print(f"Number of rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Display the first few rows
    print("\n=== First 5 Rows ===")
    print(df.head().to_string())
    
    # Display the last few rows (most recent predictions)
    print("\n=== Last 5 Rows (Most Recent Predictions) ===")
    print(df.tail().to_string())
    
    # Basic statistics if numerical columns exist
    if len(df.select_dtypes(include=['int64', 'float64']).columns) > 0:
        print("\n=== Basic Statistics ===")
        print(df.describe().to_string())
        
except Exception as e:
    print(f"\nError reading predictions file: {e}")
