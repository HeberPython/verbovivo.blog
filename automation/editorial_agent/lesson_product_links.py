from __future__ import annotations

LEGACY_PRODUCT_URL = "https://www.editorakaleo.com/product-page/revista-escola-b%C3%ADblica-jesus-aluno"
PRODUCT_URLS: dict[tuple[int, int], str] = {
    (2026, 3): LEGACY_PRODUCT_URL,
    (2026, 4): "https://www.editorakaleo.com/product-page/revista-ebd-o-deserto-e-a-igreja-aluno",
}


def product_url_for_cycle(year: int, quarter: int) -> str:
    """Return the official Kaleo magazine URL for a lesson cycle.

    Unknown cycles deliberately fall back to the legacy URL until a new
    quarterly magazine is explicitly configured, preventing guessed links.
    """
    return PRODUCT_URLS.get((year, quarter), LEGACY_PRODUCT_URL)


def install(lessons) -> None:
    """Make lesson rendering select the official product by year/quarter."""
    original_render = lessons.render_lesson_page

    def render_lesson_page(lesson):
        year = lesson.year or lessons.settings.lesson_year
        quarter = lesson.quarter or lessons.settings.lesson_quarter
        previous = lessons.LESSON_PRODUCT_URL
        lessons.LESSON_PRODUCT_URL = product_url_for_cycle(year, quarter)
        try:
            return original_render(lesson)
        finally:
            lessons.LESSON_PRODUCT_URL = previous

    lessons.product_url_for_cycle = product_url_for_cycle
    lessons.render_lesson_page = render_lesson_page
