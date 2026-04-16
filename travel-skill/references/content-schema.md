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
- `raw_capture_policy`
- `media_policy`
- `normalized_schema`

## web_research_run

- `run_id`
- `batch_id`
- `skill`
- `result_schema`
- `postprocess_script`
- `expected_bundle_path`
- `expected_coverage_path`
- `task`
- `prompt`

## web_research_batch_manifest

- `trip_slug`
- `batch_id`
- `aggregator_script`
- `bundle_paths`
- `runs`

## web_access_batch_request

- `trip_slug`
- `batch_id`
- `requests`

## web_access_batch_request_item

- `run_id`
- `batch_id`
- `prompt`
- `task`
- `skill`
- `result_schema`
- `response_path`

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
- `normalized_schema`
- `collector_mode`
- `coverage_status`
- `failure_reason`
- `failure_detail`
- `missing_fields`
- `checked_at`
- `time_layer`
- `evidence_refs`
- `knowledge_points`

## site_record_bundle

- `records`
- `source_record_id`

## merged_topic_knowledge

- `topics`
- `claim`
- `evidence_refs`

## page_evidence_record

- `page_body_full`
- `comment_threads_full`
- `comment_sample_size`
- `image_candidates`

## video_media_bundle

- `all_keyframes`
- `frame_scores`
- `selected_frames`
- `selection_rationale`
- `scene_tags`

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
