from prometheus_client import Counter, Histogram

POST_GENERATION_COUNTER = Counter(
    "social_ai_post_generation_total",
    "Total number of generated posts",
    ["platform", "status"],
)

PUBLISH_COUNTER = Counter(
    "social_ai_publish_total",
    "Total publish attempts",
    ["platform", "status"],
)

WORKFLOW_DURATION = Histogram(
    "social_ai_workflow_duration_seconds",
    "Duration of workflow execution",
    ["workflow"],
)
