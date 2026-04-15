# Content Schema

## trip_request

- `title`
- `trip_slug`
- `departure_city`
- `destinations`
- `date_range`
- `travelers`
- `traveler_profile`
- `budget`
- `preferences`
- `sample_reference`
- `required_topics`
- `missing_core_fields`
- `missing_preference_fields`
- `research_dimensions`

## research_task

- `trip_slug`
- `place`
- `topic`
- `platform`
- `site`
- `required_sources`
- `query_hint`
- `site_query`
- `collection_method`
- `must_capture_fields`
- `evidence_level`
- `time_layer`
- `sample_target`
- `retry_policy`
- `fallback_policy`

## fact_item

- `place`
- `topic`
- `site`
- `text`
- `source_url`
- `source_title`
- `source_type`
- `platform`
- `checked_at`

## content_item

- `title`
- `summary`
- `points`
- `is_placeholder`

## source_item

- `title`
- `url`
- `type`
- `checked_at`

## normalized_research_record

- `source_type`
- `collector_mode`
- `coverage_status`
- `failure_reason`
- `failure_detail`
- `missing_fields`
- `checked_at`
- `time_layer`
- `evidence_refs`
- `knowledge_points`

## coverage_report

- `site`
- `topic`
- `sample_target`
- `actual_sample_count`
- `complete_count`
- `partial_count`
- `failed_count`
- `missing_required_fields`
- `coverage_status`
- `failure_reason_counts`

## layered_outputs

- `daily-overview`
- `recommended`
- `comprehensive`

## daily-overview sections

- `summary`
- `days`
- `wearing`
- `transport`
- `alerts`
- `sources`

## recommended and comprehensive sections

- `recommended_route`
- `route_options`
- `clothing_guide`
- `attractions`
- `transport_details`
- `food_by_city`
- `tips`
- `sources`
