"""initial schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260325_0001"
down_revision = None
branch_labels = None
depends_on = None


platform_enum = sa.Enum("LINKEDIN", "X", name="platform")
post_status_enum = sa.Enum(
    "DRAFT_CREATED",
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "SCHEDULED",
    "POSTED",
    name="poststatus",
)
approval_action_enum = sa.Enum("APPROVED", "REJECTED", "EDITED", name="approvalaction")
publish_status_enum = sa.Enum("PENDING", "SUCCESS", "FAILED", name="publishstatus")


def upgrade() -> None:
    bind = op.get_bind()
    platform_enum.create(bind, checkfirst=True)
    post_status_enum.create(bind, checkfirst=True)
    approval_action_enum.create(bind, checkfirst=True)
    publish_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "social_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("account_identifier", sa.String(length=255), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_social_accounts_user_id", "social_accounts", ["user_id"], unique=False)

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("tone", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", post_status_enum, nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=True),
        sa.Column("llm_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_posts_user_id", "posts", ["user_id"], unique=False)
    op.create_index("ix_posts_platform", "posts", ["platform"], unique=False)
    op.create_index("ix_posts_status", "posts", ["status"], unique=False)

    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", approval_action_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("edited_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_approvals_post_id", "approvals", ["post_id"], unique=False)
    op.create_index("ix_approvals_reviewer_id", "approvals", ["reviewer_id"], unique=False)

    op.create_table(
        "publish_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("status", publish_status_enum, nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_publish_logs_post_id", "publish_logs", ["post_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_publish_logs_post_id", table_name="publish_logs")
    op.drop_table("publish_logs")
    op.drop_index("ix_approvals_reviewer_id", table_name="approvals")
    op.drop_index("ix_approvals_post_id", table_name="approvals")
    op.drop_table("approvals")
    op.drop_index("ix_posts_status", table_name="posts")
    op.drop_index("ix_posts_platform", table_name="posts")
    op.drop_index("ix_posts_user_id", table_name="posts")
    op.drop_table("posts")
    op.drop_index("ix_social_accounts_user_id", table_name="social_accounts")
    op.drop_table("social_accounts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    publish_status_enum.drop(op.get_bind(), checkfirst=True)
    approval_action_enum.drop(op.get_bind(), checkfirst=True)
    post_status_enum.drop(op.get_bind(), checkfirst=True)
    platform_enum.drop(op.get_bind(), checkfirst=True)
