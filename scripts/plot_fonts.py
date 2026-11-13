"""Register Arial when present; use Matplotlib's bundled fallback otherwise."""
from pathlib import Path
from matplotlib import font_manager


def configure_plot_font():
    candidate = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    if candidate.is_file():
        font_manager.fontManager.addfont(str(candidate))
    else:
        # Some source plots request Arial explicitly for math text. Register the
        # portable bundled font as a fallback without requiring a system font.
        font_manager.fontManager.addfont(
            font_manager.findfont('DejaVu Sans', fallback_to_default=True)
        )
