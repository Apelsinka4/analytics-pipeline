# Ecommerce Analytics Pipeline

Python tool for analyzing e-commerce order data from a CSV file.

It calculates revenue, gross profit, ad spend efficiency, return rate, cancellation rate, product performance, monthly trends, and basic business recommendations.

## Features

- Loads e-commerce orders from CSV.
- Converts `order_date` to datetime.
- Adds a monthly period column.
- Separates active and cancelled orders.
- Finds profitable sales channels.
- Finds losing campaigns.
- Detects categories with high return rate.
- Analyzes cancellations by sales channel.
- Shows monthly revenue/profit trend.
- Ranks products by gross profit.
- Generates a console report.

## Required CSV Columns

```text
order_id
order_date
customer_id
is_new_customer
region
sales_channel
campaign
category
sku
product_name
quantity
unit_price_usd
discount_usd
gross_revenue_usd
cogs_usd
shipping_cost_usd
ad_spend_usd
payment_method
order_status
is_returned
return_reason
net_revenue_usd
gross_profit_usd
```

## Install

Python 3.10+ is recommended.

```bash
pip install pandas numpy
```

## Run

```bash
python analytics_pipeline.py --csv path/to/orders.csv
```

On Windows, if console output fails with `UnicodeEncodeError`, run:

```powershell
$env:PYTHONIOENCODING="utf-8"
python analytics_pipeline.py --csv path/to/orders.csv
```

## Example

```python
from analytics_pipeline import EcommercePipeline

pipeline = EcommercePipeline("path/to/orders.csv")

print(pipeline.top_profitable_channels())
print(pipeline.losing_campaigns())
print(pipeline.monthly_trend())
print(pipeline.generate_report())
```

## Main Methods

### `top_profitable_channels(top_n=5)`

Returns the most profitable sales channels.

Includes:

- order count
- gross revenue
- COGS
- ad spend
- gross profit
- margin %
- ROI %

### `losing_campaigns(min_spend=0)`

Returns campaigns where `gross_profit_usd < 0`.

Use this to find campaigns that should be stopped, rebuilt, or budget-capped.

### `high_return_categories(return_threshold=10)`

Returns categories where return rate is above the threshold.

Use this to find product quality, expectation, description, or delivery problems.

### `cancellation_analysis()`

Shows cancellation rate and lost ad spend by sales channel.

### `monthly_trend()`

Shows monthly orders, revenue, costs, ad spend, profit, and margin.

### `product_performance(top_n=10)`

Ranks products by gross profit.

Includes quantity sold, order count, returns, return rate, revenue, and profit.

### `get_recommendations()`

Returns a dictionary with practical recommendations:

- `scale_up`
- `cut`
- `optimize`

### `generate_report()`

Builds the full text report and returns it as a string.

## Business Logic

The script focuses on practical decisions:

- scale channels with strong ROI
- cut campaigns with negative gross profit
- inspect categories with high return rate
- inspect channels with high cancellation rate
- track profit trend, not only revenue

## Current Limitations

- No report export file yet.
- No charts yet.
- No automated tests yet.
- Some user-facing text in `analytics_pipeline.py` has broken encoding and should be cleaned up.

## Suggested Next Steps

1. Add `--output report.txt`.
2. Add HTML or Markdown report export.
3. Add charts for monthly revenue and profit.
4. Add tests for core metrics.
5. Clean up broken encoded text in report labels.
