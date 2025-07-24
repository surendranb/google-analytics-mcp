from fastmcp import FastMCP
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, Filter, FilterExpression, FilterExpressionList,
    OrderBy, MetricAggregation
)
import os
import sys
import json

# Configuration from environment variables
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")

# Validate required environment variables
if not CREDENTIALS_PATH:
    print("ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable not set", file=sys.stderr)
    print("Please set it to the path of your service account JSON file", file=sys.stderr)
    sys.exit(1)

if not GA4_PROPERTY_ID:
    print("ERROR: GA4_PROPERTY_ID environment variable not set", file=sys.stderr)
    print("Please set it to your GA4 property ID (e.g., 123456789)", file=sys.stderr)
    sys.exit(1)

# Validate credentials file exists
if not os.path.exists(CREDENTIALS_PATH):
    print(f"ERROR: Credentials file not found: {CREDENTIALS_PATH}", file=sys.stderr)
    print("Please check the GOOGLE_APPLICATION_CREDENTIALS path", file=sys.stderr)
    sys.exit(1)

# Initialize FastMCP
mcp = FastMCP("Google Analytics 4")

# Embedded GA4 Dimensions Data
GA4_DIMENSIONS = {
    "time": {
        "date": "The date of the event in YYYYMMDD format.",
        "dateHour": "The date and hour of the event in YYYYMMDDHH format.",
        "dateHourMinute": "The date, hour, and minute of the event in YYYYMMDDHHMM format.",
        "day": "The day of the month (01-31).",
        "dayOfWeek": "The day of the week (0-6, where Sunday is 0).",
        "hour": "The hour of the day (00-23).",
        "minute": "The minute of the hour (00-59).",
        "month": "The month of the year (01-12).",
        "week": "The week of the year (00-53).",
        "year": "The year (e.g., 2024).",
        "nthDay": "The number of days since the first visit.",
        "nthHour": "The number of hours since the first visit.",
        "nthMinute": "The number of minutes since the first visit.",
        "nthMonth": "The number of months since the first visit.",
        "nthWeek": "The number of weeks since the first visit.",
        "nthYear": "The number of years since the first visit."
    },
    "geography": {
        "city": "The city of the user.",
        "cityId": "The ID of the city.",
        "country": "The country of the user.",
        "countryId": "The ID of the country.",
        "region": "The region of the user."
    },
    "technology": {
        "browser": "The browser used by the user.",
        "deviceCategory": "The category of the device (e.g., 'desktop', 'mobile', 'tablet').",
        "deviceModel": "The model of the device.",
        "operatingSystem": "The operating system of the user's device.",
        "operatingSystemVersion": "The version of the operating system.",
        "platform": "The platform of the user's device (e.g., 'web', 'android', 'ios').",
        "platformDeviceCategory": "The platform and device category.",
        "screenResolution": "The resolution of the user's screen."
    },
    "traffic_source": {
        "campaignId": "The ID of the campaign.",
        "campaignName": "The name of the campaign.",
        "defaultChannelGroup": "The default channel grouping for the traffic source.",
        "medium": "The medium of the traffic source.",
        "source": "The source of the traffic.",
        "sourceMedium": "The source and medium of the traffic.",
        "sourcePlatform": "The source platform of the traffic.",
        "sessionCampaignId": "The campaign ID of the session.",
        "sessionCampaignName": "The campaign name of the session.",
        "sessionDefaultChannelGroup": "The default channel group of the session.",
        "sessionMedium": "The medium of the session.",
        "sessionSource": "The source of the session.",
        "sessionSourceMedium": "The source and medium of the session.",
        "sessionSourcePlatform": "The source platform of the session."
    },
    "first_user_attribution": {
        "firstUserCampaignId": "The campaign ID that first acquired the user.",
        "firstUserCampaignName": "The campaign name that first acquired the user.",
        "firstUserDefaultChannelGroup": "The default channel group that first acquired the user.",
        "firstUserMedium": "The medium that first acquired the user.",
        "firstUserSource": "The source that first acquired the user.",
        "firstUserSourceMedium": "The source and medium that first acquired the user.",
        "firstUserSourcePlatform": "The source platform that first acquired the user."
    },
    "content": {
        "contentGroup": "The content group on your site/app. Populated by the event parameter 'content_group'.",
        "contentId": "The ID of the content. Populated by the event parameter 'content_id'.",
        "contentType": "The type of content. Populated by the event parameter 'content_type'.",
        "fullPageUrl": "The full URL of the page.",
        "landingPage": "The page path of the landing page.",
        "pageLocation": "The full URL of the page.",
        "pagePath": "The path of the page (e.g., '/home').",
        "pagePathPlusQueryString": "The page path and query string.",
        "pageReferrer": "The referring URL.",
        "pageTitle": "The title of the page.",
        "unifiedScreenClass": "The class of the screen.",
        "unifiedScreenName": "The name of the screen."
    },
    "events": {
        "eventName": "The name of the event.",
        "isConversionEvent": "Whether the event is a conversion event ('true' or 'false').",
        "method": "The method of the event. Populated by the event parameter 'method'."
    },
    "ecommerce": {
        "itemBrand": "The brand of the item.",
        "itemCategory": "The category of the item.",
        "itemCategory2": "A secondary category for the item.",
        "itemCategory3": "A third category for the item.",
        "itemCategory4": "A fourth category for the item.",
        "itemCategory5": "A fifth category for the item.",
        "itemId": "The ID of the item.",
        "itemListId": "The ID of the item list.",
        "itemListName": "The name of the item list.",
        "itemName": "The name of the item.",
        "itemPromotionCreativeName": "The creative name of the item promotion.",
        "itemPromotionId": "The ID of the item promotion.",
        "itemPromotionName": "The name of the item promotion.",
        "orderCoupon": "The coupon code for the order.",
        "shippingTier": "The shipping tier for the order.",
        "transactionId": "The ID of the transaction."
    },
    "user_demographics": {
        "newVsReturning": "Whether the user is new or returning.",
        "signedInWithUserId": "Whether the user was signed in with a User-ID ('true' or 'false').",
        "userAgeBracket": "The age bracket of the user.",
        "userGender": "The gender of the user.",
        "language": "The language of the user's browser or device.",
        "languageCode": "The language code."
    },
    "google_ads": {
        "googleAdsAdGroupId": "The ID of the Google Ads ad group.",
        "googleAdsAdGroupName": "The name of the Google Ads ad group.",
        "googleAdsAdNetworkType": "The ad network type in Google Ads.",
        "googleAdsCampaignId": "The ID of the Google Ads campaign.",
        "googleAdsCampaignName": "The name of the Google Ads campaign.",
        "googleAdsCampaignType": "The type of the Google Ads campaign.",
        "googleAdsCreativeId": "The ID of the Google Ads creative.",
        "googleAdsKeyword": "The keyword from Google Ads.",
        "googleAdsQuery": "The search query from Google Ads.",
        "firstUserGoogleAdsAdGroupId": "The Google Ads ad group ID that first acquired the user.",
        "firstUserGoogleAdsAdGroupName": "The Google Ads ad group name that first acquired the user.",
        "firstUserGoogleAdsCampaignId": "The Google Ads campaign ID that first acquired the user.",
        "firstUserGoogleAdsCampaignName": "The Google Ads campaign name that first acquired the user.",
        "firstUserGoogleAdsCampaignType": "The Google Ads campaign type that first acquired the user.",
        "firstUserGoogleAdsCreativeId": "The Google Ads creative ID that first acquired the user.",
        "firstUserGoogleAdsKeyword": "The Google Ads keyword that first acquired the user.",
        "firstUserGoogleAdsNetworkType": "The Google Ads network type that first acquired the user.",
        "firstUserGoogleAdsQuery": "The Google Ads query that first acquired the user.",
        "sessionGoogleAdsAdGroupId": "The Google Ads ad group ID of the session.",
        "sessionGoogleAdsAdGroupName": "The Google Ads ad group name of the session.",
        "sessionGoogleAdsCampaignId": "The Google Ads campaign ID of the session.",
        "sessionGoogleAdsCampaignName": "The Google Ads campaign name of the session.",
        "sessionGoogleAdsCampaignType": "The Google Ads campaign type of the session.",
        "sessionGoogleAdsCreativeId": "The Google Ads creative ID of the session.",
        "sessionGoogleAdsKeyword": "The Google Ads keyword of the session.",
        "sessionGoogleAdsNetworkType": "The Google Ads network type of the session.",
        "sessionGoogleAdsQuery": "The Google Ads query of the session."
    },
    "manual_campaigns": {
        "manualAdContent": "The ad content from a manual campaign.",
        "manualTerm": "The term from a manual campaign.",
        "firstUserManualAdContent": "The manual ad content that first acquired the user.",
        "firstUserManualTerm": "The manual term that first acquired the user.",
        "sessionManualAdContent": "The manual ad content of the session.",
        "sessionManualTerm": "The manual term of the session."
    },
    "app_specific": {
        "appVersion": "The version of the app.",
        "streamId": "The ID of the data stream.",
        "streamName": "The name of the data stream."
    },
    "cohort_analysis": {
        "cohort": "The cohort the user belongs to.",
        "cohortNthDay": "The day number within the cohort.",
        "cohortNthMonth": "The month number within the cohort.",
        "cohortNthWeek": "The week number within the cohort."
    },
    "audiences": {
        "audienceId": "The ID of the audience.",
        "audienceName": "The name of the audience.",
        "brandingInterest": "The interest category associated with the user."
    },
    "enhanced_measurement": {
        "fileExtension": "The extension of the downloaded file.",
        "fileName": "The name of the downloaded file.",
        "linkClasses": "The classes of the clicked link.",
        "linkDomain": "The domain of the clicked link.",
        "linkId": "The ID of the clicked link.",
        "linkText": "The text of the clicked link.",
        "linkUrl": "The URL of the clicked link.",
        "outbound": "Whether the clicked link was outbound ('true' or 'false').",
        "percentScrolled": "The percentage of the page scrolled.",
        "searchTerm": "The term used for an internal site search.",
        "videoProvider": "The provider of the video.",
        "videoTitle": "The title of the video.",
        "videoUrl": "The URL of the video.",
        "visible": "Whether the video was visible on the screen."
    },
    "gaming": {
        "achievementId": "The achievement ID in a game for an event.",
        "character": "The character in a game.",
        "groupId": "The group ID in a game.",
        "virtualCurrencyName": "The name of the virtual currency."
    },
    "advertising": {
        "adFormat": "The format of the ad that was shown (e.g., 'Interstitial', 'Banner', 'Rewarded').",
        "adSourceName": "The name of the ad network or source that served the ad.",
        "adUnitName": "The name of the ad unit that displayed the ad."
    },
    "testing": {
        "testDataFilterName": "The name of the test data filter."
    }
}

# Embedded GA4 Metrics Data
GA4_METRICS = {
    "user_metrics": {
        "totalUsers": "The total number of unique users.",
        "newUsers": "The number of users who interacted with your site or app for the first time.",
        "activeUsers": "The number of distinct users who have logged an engaged session on your site or app.",
        "active1DayUsers": "The number of distinct users who have been active on your site or app in the last 1 day.",
        "active7DayUsers": "The number of distinct users who have been active on your site or app in the last 7 days.",
        "active28DayUsers": "The number of distinct users who have been active on your site or app in the last 28 days.",
        "userStickiness": "A measure of how frequently users return to your site or app.",
        "dauPerMau": "The ratio of daily active users to monthly active users.",
        "dauPerWau": "The ratio of daily active users to weekly active users.",
        "wauPerMau": "The ratio of weekly active users to monthly active users."
    },
    "session_metrics": {
        "sessions": "The total number of sessions.",
        "sessionsPerUser": "The average number of sessions per user.",
        "engagedSessions": "The number of sessions that lasted longer than 10 seconds, or had a conversion event, or had at least 2 pageviews or screenviews.",
        "bounceRate": "The percentage of sessions that were not engaged.",
        "engagementRate": "The percentage of sessions that were engaged.",
        "averageSessionDuration": "The average duration of a session in seconds.",
        "sessionConversionRate": "The percentage of sessions in which a conversion event occurred."
    },
    "pageview_metrics": {
        "screenPageViews": "The total number of app screens or web pages your users saw.",
        "screenPageViewsPerSession": "The average number of screens or pages viewed per session.",
        "screenPageViewsPerUser": "The average number of screens or pages viewed per user."
    },
    "event_metrics": {
        "eventCount": "The total number of events.",
        "eventCountPerUser": "The average number of events per user.",
        "eventsPerSession": "The average number of events per session.",
        "eventValue": "The total value of all 'value' event parameters.",
        "conversions": "The total number of conversion events.",
        "userConversionRate": "The percentage of active users who triggered a conversion event."
    },
    "engagement_metrics": {
        "userEngagementDuration": "The average time your app was in the foreground or your website was in focus in the browser.",
        "scrolledUsers": "The number of users who scrolled at least 90% of the page."
    },
    "ecommerce_metrics": {
        "totalRevenue": "The total revenue from all sources.",
        "purchaseRevenue": "The total revenue from purchases.",
        "grossPurchaseRevenue": "The total purchase revenue, before refunds.",
        "itemRevenue": "The total revenue from items.",
        "grossItemRevenue": "The total revenue from items, before refunds.",
        "averageRevenue": "The average revenue per user.",
        "averagePurchaseRevenue": "The average purchase revenue per user.",
        "averagePurchaseRevenuePerPayingUser": "The average purchase revenue per paying user.",
        "transactions": "The total number of transactions.",
        "ecommercePurchases": "The total number of ecommerce purchases.",
        "purchasers": "The number of users who made a purchase.",
        "totalPurchasers": "The total number of unique purchasers.",
        "purchaserConversionRate": "The percentage of active users who made a purchase.",
        "firstTimePurchasers": "The number of users who made their first purchase.",
        "firstTimePurchaserConversionRate": "The percentage of active users who made their first purchase.",
        "firstTimePurchasersPerNewUser": "The number of first-time purchasers per new user.",
        "transactionsPerPurchaser": "The average number of transactions per purchaser.",
        "checkouts": "The number of times users started the checkout process.",
        "refunds": "The total number of refunds.",
        "refundAmount": "The total amount of refunds.",
        "shippingAmount": "The total shipping cost.",
        "taxAmount": "The total tax amount."
    },
    "item_metrics": {
        "itemViews": "The number of times users viewed items.",
        "itemsAddedToCart": "The number of units of items added to the cart.",
        "itemsCheckedOut": "The number of units of items in the checkout process.",
        "itemPurchaseQuantity": "The total number of units of items purchased.",
        "itemViewToPurchaseRate": "The rate at which users who viewed items also purchased them.",
        "purchaseToViewRate": "The rate at which users who viewed items also purchased them.",
        "itemListViews": "The number of times users viewed item lists.",
        "itemListClicks": "The number of times users clicked on items in a list.",
        "itemListClickThroughRate": "The rate at which users clicked on items in a list.",
        "itemsClickedInList": "The number of units of items clicked in a list.",
        "itemsViewedInList": "The number of units of items viewed in a list.",
        "itemPromotionViews": "The number of times users viewed item promotions.",
        "itemPromotionClicks": "The number of times users clicked on item promotions.",
        "itemPromotionClickThroughRate": "The rate at which users clicked on item promotions.",
        "itemsClickedInPromotion": "The number of units of items clicked in a promotion.",
        "itemsViewedInPromotion": "The number of units of items viewed in a promotion."
    },
    "advertising_metrics": {
        "totalAdRevenue": "The total revenue from all ad sources.",
        "adRevenue": "The total revenue from ads.",
        "adImpressions": "The total number of ad impressions.",
        "publisherAdRevenue": "The total revenue from publisher ads.",
        "publisherAdImpressions": "The total number of publisher ad impressions.",
        "publisherAdClicks": "The total number of clicks on publisher ads.",
        "returnOnAdSpend": "The return on investment from your advertising."
    },
    "search_console_metrics": {
        "organicGoogleSearchClicks": "The number of clicks your website received from organic Google Search.",
        "organicGoogleSearchImpressions": "The number of times your website appeared in organic Google Search results.",
        "organicGoogleSearchClickThroughRate": "The click-through rate for your website in organic Google Search results.",
        "organicGoogleSearchAveragePosition": "The average ranking of your website URLs for the queries reported in Search Console."
    },
    "cohort_metrics": {
        "cohortActiveUsers": "The number of active users in a cohort.",
        "cohortTotalUsers": "The total number of users in a cohort."
    },
    "app_crash_metrics": {
        "crashAffectedUsers": "The number of users who experienced a crash.",
        "crashFreeUsersRate": "The percentage of users who did not experience a crash."
    }
}

# Load functions now use embedded data
def load_dimensions():
    """Load available dimensions from embedded data"""
    return GA4_DIMENSIONS

def load_metrics():
    """Load available metrics from embedded data"""
    return GA4_METRICS

def _get_smart_sorting(dimensions, metrics):
    """Determine optimal sorting strategy for relevance"""
    order_bys = []
    
    # If date dimension exists, sort by date descending (most recent first)
    if "date" in dimensions:
        order_bys.append(OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=True))
    
    # Sort by first metric descending to get highest values first
    if metrics:
        order_bys.append(OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True))
    
    return order_bys

def _should_aggregate(dimensions, metrics):
    """Detect when server-side aggregation would be beneficial"""
    # Aggregate when no dimensions (total summary) or no date dimension (period totals)
    return len(dimensions) == 0 or "date" not in dimensions

@mcp.tool()
def list_dimension_categories():
    """
    List all available GA4 dimension categories with descriptions.
    
    Returns:
        Dictionary of dimension categories and their available dimensions.
    """
    dimensions = load_dimensions()
    result = {}
    for category, dims in dimensions.items():
        result[category] = {
            "count": len(dims),
            "dimensions": list(dims.keys())
        }
    return result

@mcp.tool()
def list_metric_categories():
    """
    List all available GA4 metric categories with descriptions.
    
    Returns:
        Dictionary of metric categories and their available metrics.
    """
    metrics = load_metrics()
    result = {}
    for category, mets in metrics.items():
        result[category] = {
            "count": len(mets),
            "metrics": list(mets.keys())
        }
    return result

@mcp.tool()
def get_dimensions_by_category(category):
    """
    Get all dimensions in a specific category with their descriptions.
    
    Args:
        category: Category name (e.g., 'time', 'geography', 'ecommerce')
        
    Returns:
        Dictionary of dimensions and their descriptions for the category.
    """
    dimensions = load_dimensions()
    if category in dimensions:
        return dimensions[category]
    else:
        available_categories = list(dimensions.keys())
        return {"error": f"Category '{category}' not found. Available categories: {available_categories}"}

@mcp.tool()
def get_metrics_by_category(category):
    """
    Get all metrics in a specific category with their descriptions.
    
    Args:
        category: Category name (e.g., 'user_metrics', 'ecommerce_metrics', 'session_metrics')
        
    Returns:
        Dictionary of metrics and their descriptions for the category.
    """
    metrics = load_metrics()
    if category in metrics:
        return metrics[category]
    else:
        available_categories = list(metrics.keys())
        return {"error": f"Category '{category}' not found. Available categories: {available_categories}"}

@mcp.tool()
def get_ga4_data(
    dimensions=["date"],
    metrics=["totalUsers", "newUsers", "bounceRate", "screenPageViewsPerSession", "averageSessionDuration"],
    date_range_start="7daysAgo",
    date_range_end="yesterday",
    dimension_filter=None,
    # Enhanced functionality parameters
    estimate_only=False,
    proceed_with_large_dataset=False,
    limit=None,
    enable_aggregation=True
):
    """
    Retrieve GA4 metrics data broken down by the specified dimensions.
    
    Args:
        dimensions: List of GA4 dimensions (e.g., ["date", "city"]) or a string 
                    representation (e.g., "[\"date\", \"city\"]" or "date,city").
        metrics: List of GA4 metrics (e.g., ["totalUsers", "newUsers"]) or a string
                 representation (e.g., "[\"totalUsers\"]" or "totalUsers,newUsers").
        date_range_start: Start date in YYYY-MM-DD format or relative date like '7daysAgo'.
        date_range_end: End date in YYYY-MM-DD format or relative date like 'yesterday'.
        dimension_filter: (Optional) JSON string or dict representing a GA4 FilterExpression. See GA4 API docs for structure.
        estimate_only: (Optional) If True, returns only the estimated row count without fetching data.
        proceed_with_large_dataset: (Optional) Set to True to proceed with queries that would return >1000 rows.
        limit: (Optional) Maximum number of rows to return. If None, returns all available data.
        enable_aggregation: (Optional) If True, uses server-side aggregation when beneficial for performance.
        
    Returns:
        List of dictionaries containing the requested data, warning dictionary for large datasets, or an error dictionary.
    """
    try:
        # Handle cases where dimensions might be passed as a string from the MCP client
        parsed_dimensions = dimensions
        if isinstance(dimensions, str):
            try:
                parsed_dimensions = json.loads(dimensions)
                if not isinstance(parsed_dimensions, list):
                    parsed_dimensions = [str(parsed_dimensions)]
            except json.JSONDecodeError:
                parsed_dimensions = [d.strip() for d in dimensions.split(',')]
        parsed_dimensions = [str(d).strip() for d in parsed_dimensions if str(d).strip()]

        # Handle cases where metrics might be passed as a string
        parsed_metrics = metrics
        if isinstance(metrics, str):
            try:
                parsed_metrics = json.loads(metrics)
                if not isinstance(parsed_metrics, list):
                    parsed_metrics = [str(parsed_metrics)]
            except json.JSONDecodeError:
                parsed_metrics = [m.strip() for m in metrics.split(',')]
        parsed_metrics = [str(m).strip() for m in parsed_metrics if str(m).strip()]

        # Proceed if we have valid dimensions and metrics after parsing
        if not parsed_dimensions:
            return {"error": "Dimensions list cannot be empty after parsing."}
        if not parsed_metrics:
            return {"error": "Metrics list cannot be empty after parsing."}

        # Validate dimension_filter and build FilterExpression if provided
        filter_expression = None
        if dimension_filter:
            print(f"DEBUG: Processing dimension_filter: {dimension_filter}", file=sys.stderr)
            
            # Load valid dimensions from embedded data
            valid_dimensions = set()
            dims_json = load_dimensions()
            for cat in dims_json.values():
                valid_dimensions.update(cat.keys())
            
            # Parse filter input
            if isinstance(dimension_filter, str):
                try:
                    filter_dict = json.loads(dimension_filter)
                except Exception as e:
                    return {"error": f"Failed to parse dimension_filter JSON: {e}"}
            elif isinstance(dimension_filter, dict):
                filter_dict = dimension_filter
            else:
                return {"error": "dimension_filter must be a JSON string or dict."}

            # Recursive helper to build FilterExpression from dict
            def build_filter_expr(expr):
                try:
                    if 'andGroup' in expr:
                        expressions = []
                        for e in expr['andGroup']['expressions']:
                            built_expr = build_filter_expr(e)
                            if built_expr is None:
                                return None
                            expressions.append(built_expr)
                        return FilterExpression(and_group=FilterExpressionList(expressions=expressions))
                    
                    if 'orGroup' in expr:
                        expressions = []
                        for e in expr['orGroup']['expressions']:
                            built_expr = build_filter_expr(e)
                            if built_expr is None:
                                return None
                            expressions.append(built_expr)
                        return FilterExpression(or_group=FilterExpressionList(expressions=expressions))
                    
                    if 'notExpression' in expr:
                        built_expr = build_filter_expr(expr['notExpression'])
                        if built_expr is None:
                            return None
                        return FilterExpression(not_expression=built_expr)
                    
                    if 'filter' in expr:
                        f = expr['filter']
                        field = f.get('fieldName')
                        if not field:
                            print(f"DEBUG: Missing fieldName in filter: {f}", file=sys.stderr)
                            return None
                        if field not in valid_dimensions:
                            print(f"DEBUG: Invalid dimension '{field}'. Valid: {sorted(list(valid_dimensions))[:10]}...", file=sys.stderr)
                            return None
                        
                        if 'stringFilter' in f:
                            sf = f['stringFilter']
                            # Map string match types to API enum values
                            match_type_map = {
                                'EXACT': Filter.StringFilter.MatchType.EXACT,
                                'BEGINS_WITH': Filter.StringFilter.MatchType.BEGINS_WITH,
                                'ENDS_WITH': Filter.StringFilter.MatchType.ENDS_WITH,
                                'CONTAINS': Filter.StringFilter.MatchType.CONTAINS,
                                'FULL_REGEXP': Filter.StringFilter.MatchType.FULL_REGEXP,
                                'PARTIAL_REGEXP': Filter.StringFilter.MatchType.PARTIAL_REGEXP
                            }
                            match_type = match_type_map.get(sf.get('matchType', 'EXACT'), Filter.StringFilter.MatchType.EXACT)
                            
                            return FilterExpression(filter=Filter(
                                field_name=field,
                                string_filter=Filter.StringFilter(
                                    value=sf.get('value', ''),
                                    match_type=match_type,
                                    case_sensitive=sf.get('caseSensitive', False)
                                )
                            ))
                        
                        if 'inListFilter' in f:
                            ilf = f['inListFilter']
                            return FilterExpression(filter=Filter(
                                field_name=field,
                                in_list_filter=Filter.InListFilter(
                                    values=ilf.get('values', []),
                                    case_sensitive=ilf.get('caseSensitive', False)
                                )
                            ))
                    
                    print(f"DEBUG: Unrecognized filter structure: {expr}", file=sys.stderr)
                    return None
                    
                except Exception as e:
                    print(f"DEBUG: Exception in build_filter_expr: {e}", file=sys.stderr)
                    return None
            
            filter_expression = build_filter_expr(filter_dict)
            if filter_expression is None:
                return {"error": "Invalid or unsupported dimension_filter structure, or invalid dimension name."}

        # Row Count Estimation
        client = BetaAnalyticsDataClient()
        dimension_objects = [Dimension(name=d) for d in parsed_dimensions]
        metric_objects = [Metric(name=m) for m in parsed_metrics]
        
        # Estimate row count if needed (for warnings or estimate_only requests)
        if not proceed_with_large_dataset or estimate_only:
            try:
                estimation_request = RunReportRequest(
                    property=f"properties/{GA4_PROPERTY_ID}",
                    dimensions=dimension_objects,
                    metrics=metric_objects,
                    date_ranges=[DateRange(start_date=date_range_start, end_date=date_range_end)],
                    dimension_filter=filter_expression if filter_expression else None,
                    limit="1"  # Only get 1 row to get rowCount
                )
                estimation_response = client.run_report(estimation_request)
                estimated_rows = estimation_response.row_count
                
                # Return estimation only if requested
                if estimate_only:
                    return {"estimated_rows": estimated_rows}
                
                # Check if warning is needed
                if estimated_rows > 2500:
                    return {
                        "warning": True,
                        "estimated_rows": estimated_rows,
                        "suggestions": [
                            "Reduce date range to get fewer rows",
                            "Add dimension filters to narrow results", 
                            "Consider using fewer dimensions",
                            "Use limit parameter to restrict number of rows"
                        ],
                        "proceed_instructions": "Add proceed_with_large_dataset=True to continue with this query"
                    }
            except Exception as e:
                # If estimation fails, continue with normal execution
                print(f"DEBUG: Estimation failed, continuing with normal execution: {e}", file=sys.stderr)

        # GA4 API Call
        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[DateRange(start_date=date_range_start, end_date=date_range_end)],
            dimension_filter=filter_expression if filter_expression else None,
            limit=str(limit) if limit else None,
            order_bys=_get_smart_sorting(parsed_dimensions, parsed_metrics),
            metric_aggregations=[MetricAggregation.TOTAL] if enable_aggregation and _should_aggregate(parsed_dimensions, parsed_metrics) else None
        )
        response = client.run_report(request)
        result = []
        for row_idx, row in enumerate(response.rows):
            data_row = {}
            for i, dimension_header in enumerate(response.dimension_headers):
                if i < len(row.dimension_values):
                    data_row[dimension_header.name] = row.dimension_values[i].value
                else:
                    data_row[dimension_header.name] = None
            for i, metric_header in enumerate(response.metric_headers):
                if i < len(row.metric_values):
                    data_row[metric_header.name] = row.metric_values[i].value
                else:
                    data_row[metric_header.name] = None
            result.append(data_row)
        
        # For backward compatibility, return just the result list by default
        # Only add metadata if optimizations were applied or user requested it
        applied_optimizations = []
        
        if limit:
            applied_optimizations.append(f"Limited to {limit} rows")
        if enable_aggregation and _should_aggregate(parsed_dimensions, parsed_metrics):
            applied_optimizations.append("Server-side aggregation applied")
        if _get_smart_sorting(parsed_dimensions, parsed_metrics):
            applied_optimizations.append("Intelligent sorting applied")
        
        # If no optimizations were applied, return simple result for backward compatibility
        if not applied_optimizations:
            return result
        
        # If optimizations were applied, include metadata for transparency
        return {
            "data": result,
            "metadata": {
                "total_rows": response.row_count,
                "returned_rows": len(result),
                "applied_optimizations": applied_optimizations
            }
        }
    except Exception as e:
        error_message = f"Error fetching GA4 data: {str(e)}"
        print(error_message, file=sys.stderr)
        if hasattr(e, 'details'):
            error_message += f" Details: {e.details()}"
        return {"error": error_message}

def main():
    """Main entry point for the MCP server"""
    print("Starting GA4 MCP server...", file=sys.stderr)
    mcp.run(transport="stdio")

# Start the server when run directly
if __name__ == "__main__":
    main()