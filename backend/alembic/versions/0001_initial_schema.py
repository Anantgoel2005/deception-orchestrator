"""Initial versioned schema for the showcase control plane."""
from alembic import op

from app.core.database import Base
from app.models.alert import Alert  # noqa: F401
from app.models.canary import CanaryToken  # noqa: F401
from app.models.event import AttackEvent  # noqa: F401
from app.models.honeypot import Honeypot  # noqa: F401

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
