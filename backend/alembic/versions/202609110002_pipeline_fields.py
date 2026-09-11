from alembic import op
import sqlalchemy as sa


revision = "202609110002"
down_revision = "202609110001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("brandbooks", sa.Column("font_family", sa.String(length=120), nullable=False, server_default="Inter"))
    op.add_column("projects", sa.Column("image_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "image_url")
    op.drop_column("brandbooks", "font_family")