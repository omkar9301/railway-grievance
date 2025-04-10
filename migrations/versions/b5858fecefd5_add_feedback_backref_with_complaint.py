"""Add Feedback backref with complaint

Revision ID: b5858fecefd5
Revises: f70f6884472a
Create Date: 2024-11-07 16:25:17.184353

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5858fecefd5'
down_revision = 'f70f6884472a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        # Add the new foreign key constraint if it doesn't already exist
        batch_op.create_foreign_key('fk_feedback_complaint_id', 'complaint', ['complaint_id'], ['id'])

def downgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        # Drop the foreign key constraint if it exists
        batch_op.drop_constraint('fk_feedback_complaint_id', type_='foreignkey')
        # Recreate the old foreign key constraint if needed
        batch_op.create_foreign_key('fk_feedback_complaint_id', 'complaint', ['complaint_id'], ['unique_id'])
