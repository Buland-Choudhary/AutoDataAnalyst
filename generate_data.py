import pandas as pd
import numpy as np
import os

def create_churn_dataset():
    np.random.seed(42)
    n = 1000
    
    data = {
        'CustomerID': range(1, n + 1),
        'Age': np.random.randint(18, 70, n),
        'MonthlyCharge': np.random.uniform(20.0, 120.0, n),
        'TenureMonths': np.random.randint(1, 72, n),
        'SupportTickets': np.random.randint(0, 10, n),
        # Introduce a non-standard missing value for the agent to catch
        'PlanType': np.random.choice(['Basic', 'Premium', 'NULL_VAL'], n, p=[0.6, 0.35, 0.05])
    }
    
    df = pd.DataFrame(data)
    
    # Complex non-linear churn logic for future tree-based models
    churn_prob = (
        (df['SupportTickets'] > 5).astype(float) * 0.4 +
        (df['TenureMonths'] < 6).astype(float) * 0.3 +
        (df['MonthlyCharge'] > 90).astype(float) * 0.2
    )
    df['Churn'] = (np.random.rand(n) < churn_prob).astype(int)
    
    os.makedirs('datasets', exist_ok=True)
    df.to_csv('datasets/customer_churn.csv', index=False)
    print("✅ datasets/customer_churn.csv generated successfully.")

if __name__ == "__main__":
    create_churn_dataset()