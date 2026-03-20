import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
data = pd.read_csv('/home/buland/Downloads/ACADEMICS/AutoDataAnalyst/datasets/customer_churn.csv')

# Handle non-standard missing values (if any)
# Assuming non-standard missing values could be represented as empty strings or specific placeholders
data.replace({'': pd.NA, 'N/A': pd.NA, 'NULL': pd.NA}, inplace=True)

# Check for any remaining missing values
assert data.isnull().sum().sum() == 0, "There are still missing values in the dataset."

# Calculate the correlation matrix
correlation_matrix = data.corr()

# Plot the correlation heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap='coolwarm', square=True, cbar_kws={"shrink": .8})
plt.title('Correlation Heatmap of Numerical Features')
plt.savefig('correlation_heatmap.png')