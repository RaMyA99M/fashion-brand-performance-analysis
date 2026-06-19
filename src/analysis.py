import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('products_asos.csv', on_bad_lines='skip')
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df = df.dropna(subset=['price'])

print(f"Data Loaded: {len(df)} rows")
df.head()

df['description'] = df['description'].astype(str)

def get_brand(text):
  if 'by' in text:
    try:
      return text.split('by ')[1].split(' ')[0]
    except:
      return "Unknown"
  return "Unknown"
df['brand_raw'] = df['description'].apply(get_brand)

df.head(3)


brand_map = {

    'New': 'New Look',
    'River': 'River Island',
    'Miss': 'Miss Selfridge',
    'TopshopWelcome': 'Topshop'
}

df['Brand'] = df['brand_raw'].map(brand_map).fillna(df['brand_raw'])

brand_counts = df['Brand'].value_counts()
valid_brands = brand_counts[brand_counts > 5].index
df_clean = df[df['Brand']. isin(valid_brands)].copy()

print(df_clean['Brand'].value_counts().head(5))

# Function to analyze stockouts
def calculate_phantom_revenue(size_str):
  if not isinstance(size_str, str):
      return 0, 0.0

  # Split "UK 6, UK 8 - Out of stock" into list
  sizes = size_str.split(',')
  total_sizes = len(sizes)

  # Count how many items are out of stock
  out_of_stock_count = size_str.count('Out of stock')

  # Calculate Rate (0.0 to 1.0)
  rate = out_of_stock_count / total_sizes if total_sizes > 0 else 0.0

  return out_of_stock_count, rate

metrics = df_clean['size'].apply(lambda x: calculate_phantom_revenue(x))
df_clean['Stockout_Count'] = [x[0] for x in metrics]
df_clean['Stockout_Rate'] = [x[1] for x in metrics]

df_clean['Lost_Revenue'] = df_clean['price'] * df_clean['Stockout_Count']

cols = ['Brand', 'name', 'price', 'Stockout_Count', 'Lost_Revenue']
print(df_clean.sort_values(by='Lost_Revenue', ascending=False).head(5)[cols])

brand_strategy = df_clean.groupby('Brand').agg({
    'price': 'mean',
    'Stockout_Rate': 'mean',
    'Lost_Revenue': 'sum',
    'name': 'count'
}).reset_index()

brand_strategy = brand_strategy[brand_strategy['name'] > 10]

plt.figure(figsize= (12, 8))
sns.scatterplot(
    data = brand_strategy,
    x = 'price',
    y = 'Stockout_Rate',
    size = 'Lost_Revenue',
    sizes = (50, 500),
    alpha = 0.7,
    palette ='viridis'
)

winners = brand_strategy[
    (brand_strategy['price'] > 40) &
    (brand_strategy['Stockout_Rate'] > 0.4)
]

for i in range(len(winners)):
  plt.text(
      winners.iloc[i]['price'] + 1,
      winners.iloc[i]['Stockout_Rate'],
      winners.iloc[i]['Brand'],
  )

plt.title('Brand Strategy Analysis')
plt.xlabel('Average Price')
plt.ylabel('Stockout Rate')
plt.axvline(x=40, color='red', linestyle='--')
plt.axhline(y=0.4, color='red', linestyle='--')
plt.show()
