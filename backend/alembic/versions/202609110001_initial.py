from alembic import op
import sqlalchemy as sa


revision = "202609110001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "brandbooks",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("primary_color", sa.String(length=7), nullable=False),
        sa.Column("secondary_color", sa.String(length=7), nullable=False),
        sa.Column("text_color", sa.String(length=7), nullable=False),
        sa.Column("background_color", sa.String(length=7), nullable=False),
        sa.Column("font_header", sa.String(length=120), nullable=False),
        sa.Column("font_body", sa.String(length=120), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_brandbooks_user_id"), "brandbooks", ["user_id"], unique=False)
    op.create_table(
        "email_verifications",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_verifications_user_id"), "email_verifications", ["user_id"], unique=False)
    op.create_table(
        "projects",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("brandbook_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brandbook_id"], ["brandbooks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_email_verifications_user_id"), table_name="email_verifications")
    op.drop_table("email_verifications")
    op.drop_index(op.f("ix_brandbooks_user_id"), table_name="brandbooks")
    op.drop_table("brandbooks")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
