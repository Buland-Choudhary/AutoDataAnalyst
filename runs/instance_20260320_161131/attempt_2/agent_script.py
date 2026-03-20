import pandas as pd
import matplotlib.pyplot as plt

# Load the dataset
data = pd.read_csv('/home/buland/Downloads/ACADEMICS/AutoDataAnalyst/datasets/customer_churn.csv')

# Handle non-standard missing values (if any)
data.replace({'': pd.NA, 'N/A': pd.NA, 'NULL': pd.NA}, inplace=True)

# Check for any remaining missing values
assert data.isnull().sum().sum() == 0, "There are still missing values in the dataset."

# Select only numerical columns for correlation
numerical_data = data.select_dtypes(include=['float64', 'int64'])

# Calculate the correlation matrix
correlation_matrix = numerical_data.corr()

# Plot the correlation heatmap
plt.figure(figsize=(10, 6))
plt.imshow(correlation_matrix, cmap='coolwarm', interpolation='nearest')
plt.colorbar()
plt.xticks(range(len(correlation_matrix.columns)), correlation_matrix.columns, rotation=45)
plt.yticks(range(len(correlation_matrix.columns)), correlation_matrix.columns)
plt.title('Correlation Heatmap of Numerical Features')
plt.savefig('correlation_heatmap.png')