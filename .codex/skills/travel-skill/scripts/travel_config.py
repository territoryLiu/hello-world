SITE_COVERAGE_TARGETS = {
    "food": ["meituan", "dianping", "xiaohongshu"],
    "attractions": ["official", "xiaohongshu", "douyin", "bilibili"],
    "risks": ["xiaohongshu", "douyin", "bilibili"],
}

FLIGHT_HYBRID_THRESHOLD_KM = 600
LONG_DISTANCE_RULE_OVER = f"over-{FLIGHT_HYBRID_THRESHOLD_KM}km"
LONG_DISTANCE_RULE_WITHIN = f"within-{FLIGHT_HYBRID_THRESHOLD_KM}km"
FLIGHT_HYBRID_THRESHOLD_LABEL = f"{FLIGHT_HYBRID_THRESHOLD_KM}km"

GUIDE_OUTPUT_KEYS = ["daily-overview", "recommended", "comprehensive"]

TEMPLATE_IDS = [
    "route-first",
    "decision-first",
    "destination-first",
    "transport-first",
    "lifestyle-first",
]
SORTED_TEMPLATE_IDS = sorted(TEMPLATE_IDS)

TEMPLATE_LABELS = {
    "route-first": "路线优先",
    "decision-first": "决策优先",
    "destination-first": "目的地优先",
    "transport-first": "交通优先",
    "lifestyle-first": "生活方式优先",
}

TEMPLATE_SECTIONS = {
    "route-first": ["days", "recommended_route", "route_options", "attractions", "transport_details", "food_by_city", "clothing_guide", "tips", "sources"],
    "decision-first": ["recommended_route", "route_options", "days", "transport_details", "tips", "sources"],
    "destination-first": ["attractions", "food_by_city", "days", "transport_details", "clothing_guide", "sources"],
    "transport-first": ["transport_details", "route_options", "days", "attractions", "food_by_city", "sources"],
    "lifestyle-first": ["food_by_city", "attractions", "tips", "days", "transport_details", "clothing_guide", "sources"],
}

PUBLISH_ARTIFACTS = {
    "portal": "portal.html",
    "recommended": "recommended.html",
    "share": "share.html",
    "summary": "trip-summary.txt",
    "sources_markdown": "notes/sources.md",
    "sources_html": "notes/sources.html",
}
