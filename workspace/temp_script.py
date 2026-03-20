import pandas as pd
import matplotlib.pyplot as plt

# Load the dataset
df = pd.read_csv('breast-cancer-wisconsin.csv')

# Handle non-standard missing values
df.replace('?', pd.NA, inplace=True)
df.dropna(inplace=True)

# Group by 'Class' and calculate the average of 'F1'
f1_avg_by_class = df.groupby('Class')['F1'].mean().reset_index()

# Assert that the resulting dataframe is not empty
assert not f1_avg_by_class.empty, "The grouped DataFrame is empty."

# Plotting the bar chart
plt.bar(f1_avg_by_class['Class'].astype(str), f1_avg_by_class['F1'])
plt.xlabel('Class')
plt.ylabel('Average F1')
plt.title('Average F1 by Class')
plt.savefig('f1_avg_by_class.png')