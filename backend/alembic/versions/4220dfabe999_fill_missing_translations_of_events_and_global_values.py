"""fill missing translations of events and global values

Revision ID: 4220dfabe999
Revises: 635db786448b
Create Date: 2026-11-14 14:47:17.496403

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4220dfabe999"
down_revision: str | Sequence[str] | None = "635db786448b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The languages that the website's user interface was translated into when this migration was written.
SUPPORTED_DISPLAY_LANGUAGES = ["de", "en"]

# A missing translation is copied from the translation in this language. If the content has none in this language, it
# is copied from the translation in the first language in alphabetical order.
SOURCE_LANGUAGE = "en"


def upgrade() -> None:
    """Upgrade schema."""
    # The copied text is not translated, but a visitor sees the content instead of a gap. Content without any
    # translation has nothing to copy and stays as it is.
    op.execute(
        sa.text(
            """
            INSERT INTO event_translations (
                created_at,
                updated_at,
                event_id,
                language_tag,
                title,
                subtitle,
                presskit_url,
                trailer_url,
                trailer_poster_url,
                trailer_subtitles_url,
                description_headline,
                description
            )
            SELECT
                now(),
                now(),
                source.event_id,
                supported.tag,
                source.title,
                source.subtitle,
                source.presskit_url,
                source.trailer_url,
                source.trailer_poster_url,
                source.trailer_subtitles_url,
                source.description_headline,
                source.description
            FROM unnest(CAST(:supported_languages AS text[])) AS supported (tag)
            CROSS JOIN (SELECT DISTINCT event_id FROM event_translations) AS translated_event
            CROSS JOIN LATERAL (
                SELECT existing.*
                FROM event_translations AS existing
                WHERE existing.event_id = translated_event.event_id
                ORDER BY existing.language_tag = :source_language DESC, existing.language_tag
                LIMIT 1
            ) AS source
            WHERE NOT EXISTS (
                SELECT 1
                FROM event_translations AS present
                WHERE present.event_id = translated_event.event_id AND present.language_tag = supported.tag
            )
            """,
        ).bindparams(
            supported_languages=SUPPORTED_DISPLAY_LANGUAGES,
            source_language=SOURCE_LANGUAGE,
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO global_translations (key, language_tag, value)
            SELECT source.key, supported.tag, source.value
            FROM unnest(CAST(:supported_languages AS text[])) AS supported (tag)
            CROSS JOIN (SELECT DISTINCT key FROM global_translations) AS translated_global
            CROSS JOIN LATERAL (
                SELECT existing.*
                FROM global_translations AS existing
                WHERE existing.key = translated_global.key
                ORDER BY existing.language_tag = :source_language DESC, existing.language_tag
                LIMIT 1
            ) AS source
            WHERE NOT EXISTS (
                SELECT 1
                FROM global_translations AS present
                WHERE present.key = translated_global.key AND present.language_tag = supported.tag
            )
            """,
        ).bindparams(
            supported_languages=SUPPORTED_DISPLAY_LANGUAGES,
            source_language=SOURCE_LANGUAGE,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # The copied rows can't be told apart from the ones that existed before, so they stay.
