from research_contracts import HEAVY_SAMPLE_TARGETS, TIME_LAYER_TOPICS


SITE_COVERAGE_TARGETS = {
    "food": ["meituan", "dianping", "xiaohongshu"],
    "attractions": ["official", "xiaohongshu", "douyin", "bilibili"],
    "risks": ["xiaohongshu", "douyin", "bilibili"],
}

FLIGHT_HYBRID_THRESHOLD_KM = 1000
LONG_DISTANCE_RULE_OVER = f"over-{FLIGHT_HYBRID_THRESHOLD_KM}km"
LONG_DISTANCE_RULE_WITHIN = f"within-{FLIGHT_HYBRID_THRESHOLD_KM}km"
FLIGHT_HYBRID_THRESHOLD_LABEL = f"{FLIGHT_HYBRID_THRESHOLD_KM}km"

GUIDE_OUTPUT_KEYS = ["daily-overview", "recommended", "comprehensive"]

TEMPLATE_IDS = [
    "editorial",
]
SORTED_TEMPLATE_IDS = sorted(TEMPLATE_IDS)

TEMPLATE_LABELS = {
    "editorial": "杂志版",
}

TEMPLATE_SECTIONS = {
    "editorial": [
        "recommended_route",
        "route_options",
        "clothing_guide",
        "attractions",
        "transport_details",
        "food_by_city",
        "tips",
        "sources",
    ],
}

PUBLISH_ARTIFACTS = {
    "portal": "portal.html",
    "recommended": "recommended.html",
    "share": "share.html",
    "summary": "trip-summary.txt",
    "sources_markdown": "notes/sources.md",
    "sources_html": "notes/sources.html",
}
