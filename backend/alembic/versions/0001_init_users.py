from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# Alembic identifiers
revision = "0001_init_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create enum type 'user_role' once (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('simple','admin');
            END IF;
        END
        $$;
        """
    )

    # 2) Use dialect enum object, but do NOT (re)create the type during table creation
    role_enum = postgresql.ENUM(
        "simple", "admin",
        name="user_role",
        create_type=False,  # critical: avoid duplicate CREATE TYPE
    )

    # 3) Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("employee_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False, server_default="simple"),
    )
    op.create_index("ix_users_employee_id", "users", ["employee_id"], unique=True)

    # Optional: drop default for cleanliness (no rows yet)
    op.alter_column("users", "role", server_default=None)


def downgrade():
    # Drop table first
    op.drop_index("ix_users_employee_id", table_name="users")
    op.drop_table("users")

    # Drop enum only if no dependencies remain (safety)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_depend d
                    JOIN pg_type t ON d.refobjid = t.oid
                    WHERE t.typname = 'user_role'
                ) THEN
                    DROP TYPE user_role;
                END IF;
            END IF;
        END
        $$;
        """
    )
