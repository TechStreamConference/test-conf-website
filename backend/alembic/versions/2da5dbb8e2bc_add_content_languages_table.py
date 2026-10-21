"""add content_languages table

Revision ID: 2da5dbb8e2bc
Revises: 0f7cecbb7aa0
Create Date: 2026-10-21 18:46:38.406958

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2da5dbb8e2bc"
down_revision: str | Sequence[str] | None = "0f7cecbb7aa0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EVENT_TRANSLATIONS_FOREIGN_KEY_NAME = "event_translations_language_tag_fkey"
STATIC_PAGES_FOREIGN_KEY_NAME = "static_pages_language_tag_fkey"

# Reviewed snapshot of the permitted content languages: the primary language
# subtags of all locales with at least Basic coverage in CLDR 48.2.0, without
# `und`. Reproduce it from the `cldr-core@48.2.0` npm package with:
#
#   jq -r '.effectiveCoverageLevels | to_entries[]
#          | select(.value == "basic" or .value == "moderate" or .value == "modern")
#          | .key | split("-")[0]' coverageLevels.json | sort -u | grep -vx und
#
# The snapshot doesn't follow CLDR automatically. Languages are added by later
# migrations and never removed just because their CLDR coverage drops.
CONTENT_LANGUAGES = """
af ak am ar as ast az ba bal be bg bgc bho blo bn br brx bs bua ca ceb chr cs csw cv cy da de
doi dsb ee el en eo es et eu fa ff fi fil fo fr fy ga gaa gd gl gu ha he hi hr hsb ht hu hy ia
id ie ig ii is it ja jv ka kea kgp kk km kn ko kok ks ku kxv ky lb lij lmo lo lt lv mai mi mk
ml mn mni mr ms mt my nb nds ne nl nn no nqo nso oc om or pa pcm pl pms ps pt qu raj rm ro ru
rw sa sah sat sc scn sd shn si sk sl so sq sr st su sv sw syr szl ta te tg th ti tk tn to tr
tt tyv ug uk ur uz vec vi vmw wo xh xnr yo yrl yue za zh zu
""".split()


def upgrade() -> None:
    """Upgrade schema."""
    content_languages = op.create_table(
        "content_languages",
        sa.Column("tag", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.CheckConstraint("tag ~ '^[a-z]{2,3}$'", name="ck_content_languages_tag_format"),
        sa.PrimaryKeyConstraint("tag"),
    )
    op.bulk_insert(content_languages, [{"tag": tag} for tag in CONTENT_LANGUAGES])

    op.create_foreign_key(
        EVENT_TRANSLATIONS_FOREIGN_KEY_NAME,
        "event_translations",
        "content_languages",
        ["language_tag"],
        ["tag"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        STATIC_PAGES_FOREIGN_KEY_NAME,
        "static_pages",
        "content_languages",
        ["language_tag"],
        ["tag"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(STATIC_PAGES_FOREIGN_KEY_NAME, "static_pages", type_="foreignkey")
    op.drop_constraint(EVENT_TRANSLATIONS_FOREIGN_KEY_NAME, "event_translations", type_="foreignkey")
    op.drop_table("content_languages")
