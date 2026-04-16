TIME_LAYERS = ("recent", "last_year_same_period")

HEAVY_SAMPLE_TARGETS = {
    "official": 1,
    "xiaohongshu": 20,
    "douyin": 10,
    "bilibili": 10,
    "dianping": 15,
    "meituan": 15,
}

FAILURE_REASONS = {
    "login_required",
    "anti_bot_blocked",
    "page_unreachable",
    "content_removed",
    "comment_not_loaded",
    "insufficient_sample_size",
    "video_download_failed",
    "audio_transcription_failed",
    "keyframe_extraction_failed",
    "schema_validation_failed",
    "time_layer_not_determined",
}

SITE_REQUIRED_FIELDS = {
    "xiaohongshu": [
        "title",
        "summary",
        "author",
        "publish_time",
        "source_url",
        "comment_highlights",
        "comment_sample_size",
        "image_candidates",
        "coverage_status",
        "failure_reason",
        "missing_fields",
        "time_layer",
    ],
    "douyin": [
        "title",
        "summary",
        "author",
        "publish_time",
        "source_url",
        "comment_highlights",
        "transcript_segments",
        "visual_segments",
        "timeline",
        "shot_candidates",
        "coverage_status",
        "failure_reason",
        "missing_fields",
        "time_layer",
    ],
    "bilibili": [
        "title",
        "summary",
        "author",
        "publish_time",
        "source_url",
        "comment_highlights",
        "transcript_segments",
        "visual_segments",
        "timeline",
        "shot_candidates",
        "coverage_status",
        "failure_reason",
        "missing_fields",
        "time_layer",
    ],
    "dianping": [
        "shop_name",
        "address",
        "per_capita_range",
        "recommended_dishes",
        "queue_pattern",
        "review_themes",
        "pitfalls",
        "coverage_status",
        "failure_reason",
        "missing_fields",
        "time_layer",
    ],
    "meituan": [
        "shop_name",
        "address",
        "per_capita_range",
        "recommended_dishes",
        "queue_pattern",
        "review_themes",
        "pitfalls",
        "coverage_status",
        "failure_reason",
        "missing_fields",
        "time_layer",
    ],
}

TIME_LAYER_TOPICS = {
    "weather",
    "clothing",
    "packing",
    "attractions",
    "food",
    "seasonality",
    "risks",
}

RESEARCH_RECORD_FIELDS = [
    "place",
    "topic",
    "platform",
    "site",
    "source_url",
    "source_title",
    "collector_mode",
    "coverage_status",
    "failure_reason",
    "failure_detail",
    "missing_fields",
    "time_layer",
    "page_body_full",
    "comment_threads_full",
    "comment_sample_size",
    "transcript_full",
    "image_candidates",
    "shot_candidates",
    "media_artifacts",
]

VIDEO_MEDIA_BUNDLE_FIELDS = [
    "video",
    "audio",
    "transcript",
    "all_keyframes",
    "frame_scores",
    "selected_frames",
    "selection_rationale",
    "scene_tags",
]

IMAGE_CANDIDATE_FIELDS = [
    "section",
    "candidate_type",
    "source_ref",
    "selected_for_publish",
    "publish_state",
    "evidence_score",
    "visual_score",
    "travel_signal_tags",
]


def site_required_fields(site: str) -> list[str]:
    return list(SITE_REQUIRED_FIELDS.get(site, []))
