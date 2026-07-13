# Ecommerce Analysis

Revenue, conversion rate, AOV, and funnel drop-off using GA4 ecommerce events.

## When to use
- You have purchase, add_to_cart, begin_checkout events in GA4
- You want to measure revenue, conversion rate, or average order value
- You want to find where users drop off in the purchase funnel

## Correct metric and dimension names
GA4 ecommerce uses specific API names — do not guess:

| Concept | GA4 API name |
|---|---|
| Revenue | `purchaseRevenue` |
| Transactions | `ecommercePurchases` |
| AOV | `averagePurchaseRevenue` |
| Add to cart | `addToCarts` |
| Checkout started | `checkouts` |
| Cart-to-view rate | `cartToViewRate` |
| Purchase-to-view rate | `purchaseToViewRate` |
| Item views | `itemsViewed` |
| Item revenue | `itemRevenue` |
| Items purchased | `itemsPurchased` |
| Product name | `itemName` |
| Product category | `itemCategory` |
| Transaction ID | `transactionId` |

## Step 1 — Revenue overview
```
dimensions: ["date"]
metrics: ["ecommercePurchases", "purchaseRevenue", "averagePurchaseRevenue"]
date_range: last 30 days
order_by: date ASC
```

## Step 2 — Funnel: views → cart → checkout → purchase
```
dimensions: ["sessionDefaultChannelGroup"]
metrics: ["itemsViewed", "addToCarts", "checkouts", "ecommercePurchases",
          "cartToViewRate", "purchaseToViewRate"]
date_range: last 30 days
order_by: ecommercePurchases DESC
```

Drop-off between stages = `1 - (next_stage / current_stage)`.
The biggest drop-off is the highest-leverage fix.

## Step 3 — Top products
```
dimensions: ["itemName", "itemCategory"]
metrics: ["itemsViewed", "addToCarts", "itemsPurchased", "itemRevenue"]
date_range: last 30 days
order_by: itemRevenue DESC
```

## Step 4 — Revenue by channel
```
dimensions: ["sessionDefaultChannelGroup"]
metrics: ["ecommercePurchases", "purchaseRevenue", "averagePurchaseRevenue"]
date_range: last 30 days
order_by: purchaseRevenue DESC
```

## Incompatible combinations to avoid
- `itemId` or `itemSku` cannot be combined with session-level metrics
- `ecommercePurchases` cannot be combined with `eventCount` in the same query
- Use separate queries for item-level and session-level analysis

## What to report
- Revenue trend over the period
- Funnel conversion rates and biggest drop-off point
- Top 10 products by revenue
- Best-performing acquisition channel by revenue and AOV
