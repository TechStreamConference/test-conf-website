"""add name to content_languages table

Revision ID: eafe415ff317
Revises: 2da5dbb8e2bc
Create Date: 2026-11-01 17:37:34.839657

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eafe415ff317"
down_revision: str | Sequence[str] | None = "2da5dbb8e2bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Reviewed snapshot of the name of each content language in the language
# itself, as spelled in CLDR 48.2.0. Reproduce it from the
# `cldr-localenames-full@48.2.0` npm package with:
#
#   for tag in <content language tags>; do
#     jq -r --arg tag "$tag" '"\($tag)\t\(.main[$tag].localeDisplayNames.languages[$tag])"' \
#       "main/$tag/languages.json"
#   done
CONTENT_LANGUAGE_NAMES = {
    "af": "Afrikaans",
    "ak": "Akan",
    "am": "አማርኛ",
    "ar": "العربية",
    "as": "অসমীয়া",
    "ast": "asturianu",
    "az": "azərbaycan",
    "ba": "башҡорт",
    "bal": "بلۆچی",
    "be": "беларуская",
    "bg": "български",
    "bgc": "हरियाणवी",
    "bho": "भोजपुरी",
    "blo": "anii kagɩja",
    "bn": "বাংলা",
    "br": "brezhoneg",
    "brx": "बर’",
    "bs": "bosanski",
    "bua": "буряад",
    "ca": "català",
    "ceb": "Cebuano",
    "chr": "ᏣᎳᎩ",
    "cs": "čeština",
    "csw": "ᓀᐦᐃᓇᐍᐏᐣ",
    "cv": "чӑваш чӗлхи",
    "cy": "Cymraeg",
    "da": "dansk",
    "de": "Deutsch",
    "doi": "डोगरी",
    "dsb": "dolnoserbšćina",
    "ee": "eʋegbe",
    "el": "Ελληνικά",
    "en": "English",
    "eo": "Esperanto",
    "es": "español",
    "et": "eesti",
    "eu": "euskara",
    "fa": "فارسی",
    "ff": "Pulaar",
    "fi": "suomi",
    "fil": "Filipino",
    "fo": "føroyskt",
    "fr": "français",
    "fy": "Frysk",
    "ga": "Gaeilge",
    "gaa": "Gã",
    "gd": "Gàidhlig",
    "gl": "galego",
    "gu": "ગુજરાતી",
    "ha": "Hausa",
    "he": "עברית",
    "hi": "हिन्दी",
    "hr": "hrvatski",
    "hsb": "hornjoserbšćina",
    "ht": "Kreyòl Ayisyen",
    "hu": "magyar",
    "hy": "հայերեն",
    "ia": "interlingua",
    "id": "Indonesia",
    "ie": "Interlingue",
    "ig": "Igbo",
    "ii": "ꆈꌠꉙ",
    "is": "íslenska",
    "it": "italiano",
    "ja": "日本語",
    "jv": "Jawa",
    "ka": "ქართული",
    "kea": "kabuverdianu",
    "kgp": "kanhgág",
    "kk": "қазақ тілі",
    "km": "ខ្មែរ",
    "kn": "ಕನ್ನಡ",
    "ko": "한국어",
    "kok": "कोंकणी",
    "ks": "کٲشُر",
    "ku": "kurdî (kurmancî)",
    "kxv": "kuvi",
    "ky": "кыргызча",
    "lb": "Lëtzebuergesch",
    "lij": "ligure",
    "lmo": "Lombard",
    "lo": "ລາວ",
    "lt": "lietuvių",
    "lv": "latviešu",
    "mai": "मैथिली",
    "mi": "Māori",
    "mk": "македонски",
    "ml": "മലയാളം",
    "mn": "монгол",
    "mni": "মৈতৈলোন্",
    "mr": "मराठी",
    "ms": "Melayu",
    "mt": "Malti",
    "my": "မြန်မာ",
    "nb": "norsk bokmål",
    "nds": "Neddersass’sch",
    "ne": "नेपाली",
    "nl": "Nederlands",
    "nn": "norsk nynorsk",
    "no": "norsk",
    "nqo": "ߒߞߏ",
    "nso": "Sesotho sa Leboa",
    "oc": "occitan",
    "om": "Oromoo",
    "or": "ଓଡ଼ିଆ",
    "pa": "ਪੰਜਾਬੀ",
    "pcm": "Naijíriá Píjin",
    "pl": "polski",
    "pms": "piemontèis",
    "ps": "پښتو",
    "pt": "português",
    "qu": "Runasimi",
    "raj": "राजस्थानी",
    "rm": "rumantsch",
    "ro": "română",
    "ru": "русский",
    "rw": "Ikinyarwanda",
    "sa": "संस्कृत भाषा",
    "sah": "саха тыла",
    "sat": "ᱥᱟᱱᱛᱟᱲᱤ",
    "sc": "sardu",
    "scn": "sicilianu",
    "sd": "سنڌي",
    "shn": "တႆး",
    "si": "සිංහල",
    "sk": "slovenčina",
    "sl": "slovenščina",
    "so": "Soomaali",
    "sq": "shqip",
    "sr": "српски",
    "st": "Sesotho",
    "su": "Basa Sunda",
    "sv": "svenska",
    "sw": "Kiswahili",
    "syr": "ܣܘܪܝܝܐ",
    "szl": "ślōnski",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "tg": "тоҷикӣ",
    "th": "ไทย",
    "ti": "ትግርኛ",
    "tk": "türkmen dili",
    "tn": "Setswana",
    "to": "lea fakatonga",
    "tr": "Türkçe",
    "tt": "татар",
    "tyv": "Тыва",
    "ug": "ئۇيغۇرچە",
    "uk": "українська",
    "ur": "اردو",
    "uz": "o‘zbek",
    "vec": "veneto",
    "vi": "Tiếng Việt",
    "vmw": "emakhuwa",
    "wo": "Wolof",
    "xh": "IsiXhosa",
    "xnr": "कांगड़ी",
    "yo": "Èdè Yorùbá",
    "yrl": "nheẽgatu",
    "yue": "粵語",
    "za": "Vahcuengh",
    "zh": "中文",
    "zu": "isiZulu",
}


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "content_languages",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    for tag, name in CONTENT_LANGUAGE_NAMES.items():
        op.execute(
            sa.text("UPDATE content_languages SET name = :name WHERE tag = :tag").bindparams(
                name=name,
                tag=tag,
            ),
        )
    op.alter_column("content_languages", "name", nullable=False)
    op.create_check_constraint(
        "ck_content_languages_name_not_empty",
        "content_languages",
        "name <> ''",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("content_languages", "name")
