"""Languages that translated content is delivered in."""

# Delivered if the requested language is not available.
ENGLISH_LANGUAGE_TAG = "en"

# The languages that the website's user interface is translated into, i.e. the only ones that a user can explicitly
# choose as the display language. Content may exist in further languages of the content language registry.
SUPPORTED_DISPLAY_LANGUAGES = frozenset({"de", "en"})
