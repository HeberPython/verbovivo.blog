from pathlib import Path
from io import BytesIO

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    KeepTogether,
    Paragraph,
    PageTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "verbovivo-frontpage-revisado-v2.pdf"
IMG_DIR = ROOT / "public" / "images" / "articles"

W, H = A4
INK = colors.HexColor("#17201b")
MUTED = colors.HexColor("#59645c")
PAPER = colors.HexColor("#fbfaf6")
CREAM = colors.HexColor("#efe6d4")
LINE = colors.HexColor("#d8d0bf")
SAGE = colors.HexColor("#4f7059")
GOLD = colors.HexColor("#a9792e")
WHITE = colors.HexColor("#fffdf8")


def register_fonts() -> None:
    font_dir = Path(r"C:\Windows\Fonts")
    pdfmetrics.registerFont(TTFont("Georgia", str(font_dir / "georgia.ttf")))
    pdfmetrics.registerFont(TTFont("Georgia-Bold", str(font_dir / "georgiab.ttf")))
    pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(font_dir / "arialbd.ttf")))


def cropped_image(image_path: Path, width: float, height: float) -> RLImage:
    img = Image.open(image_path).convert("RGB")
    iw, ih = img.size
    target_ratio = width / height
    source_ratio = iw / ih
    if source_ratio > target_ratio:
        new_w = int(ih * target_ratio)
        left = (iw - new_w) // 2
        img = img.crop((left, 0, left + new_w, ih))
    else:
        new_h = int(iw / target_ratio)
        top = (ih - new_h) // 2
        img = img.crop((0, top, iw, top + new_h))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return RLImage(buffer, width=width, height=height)


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def draw_page(c, _doc) -> None:
    c.saveState()
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(SAGE)
    c.rect(0, H - 5 * mm, W * 0.55, 5 * mm, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(W * 0.55, H - 5 * mm, W * 0.45, 5 * mm, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.line(18 * mm, 15 * mm, W - 18 * mm, 15 * mm)
    c.setFont("Arial", 7.5)
    c.setFillColor(MUTED)
    c.drawString(18 * mm, 8 * mm, "Protótipo visual - Verbo Vivo")
    c.drawRightString(W - 18 * mm, 8 * mm, "Frontpage fictícia para validação editorial")
    c.restoreState()


def styles() -> dict[str, ParagraphStyle]:
    return {
        "domain": ParagraphStyle(
            "domain",
            fontName="Arial-Bold",
            fontSize=7.4,
            leading=8.4,
            textColor=SAGE,
            spaceAfter=2,
            uppercase=True,
        ),
        "brand": ParagraphStyle(
            "brand",
            fontName="Georgia-Bold",
            fontSize=30,
            leading=32,
            textColor=INK,
        ),
        "tagline": ParagraphStyle(
            "tagline",
            fontName="Arial",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Arial-Bold",
            fontSize=7.2,
            leading=8.2,
            textColor=SAGE,
        ),
        "hero_title": ParagraphStyle(
            "hero_title",
            fontName="Georgia-Bold",
            fontSize=20,
            leading=23,
            textColor=INK,
            spaceBefore=7,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="Georgia-Bold",
            fontSize=17,
            leading=20,
            textColor=INK,
            spaceBefore=3,
            spaceAfter=5,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            fontName="Georgia-Bold",
            fontSize=12.2,
            leading=14.5,
            textColor=INK,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Arial",
            fontSize=8.5,
            leading=11.5,
            textColor=MUTED,
        ),
        "small": ParagraphStyle(
            "small",
            fontName="Arial-Bold",
            fontSize=7.7,
            leading=9.2,
            textColor=GOLD,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Arial",
            fontSize=8.2,
            leading=11,
            textColor=MUTED,
            leftIndent=8,
            firstLineIndent=-8,
        ),
    }


def masthead(s: dict[str, ParagraphStyle]) -> Table:
    mark = Table(
        [[Paragraph("VV", ParagraphStyle("mark", fontName="Arial-Bold", fontSize=11, leading=12, textColor=PAPER))]],
        colWidths=[14 * mm],
        rowHeights=[14 * mm],
    )
    mark.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), INK),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    brand = [paragraph("VERBOVIVO.BLOG", s["domain"]), paragraph("Verbo Vivo", s["brand"])]
    table = Table(
        [[mark, brand, paragraph("Reflexões cristãs para fortalecer a fé e iluminar a caminhada.", s["tagline"])]],
        colWidths=[18 * mm, 90 * mm, 66 * mm],
        rowHeights=[24 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, LINE),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def hero(s: dict[str, ParagraphStyle]) -> Table:
    copy = [
        paragraph("ARTIGO EM DESTAQUE", s["label"]),
        paragraph("Depois da Festa:<br/>onde ficou Jesus?", s["hero_title"]),
        paragraph(
            "Uma reflexão sobre o Cristo que é celebrado em público, mas que também deseja permanecer conosco quando a multidão se dispersa e a vida comum recomeça.",
            s["body"],
        ),
        Spacer(1, 7 * mm),
        paragraph("Vida Cristã - Mateus 21:17 - Leitura profunda", s["small"]),
    ]
    box = Table([[copy]], colWidths=[70 * mm], rowHeights=[59 * mm])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 6 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    table = Table(
        [[cropped_image(IMG_DIR / "depois-da-festa.png", 96 * mm, 59 * mm), box]],
        colWidths=[96 * mm, 76 * mm],
        rowHeights=[59 * mm],
    )
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 6 * mm)]))
    return table


def card(s: dict[str, ParagraphStyle], image: str, category: str, title: str, desc: str) -> Table:
    content = [
        cropped_image(IMG_DIR / image, 83 * mm, 33 * mm),
        Spacer(1, 4 * mm),
        paragraph(category.upper(), s["small"]),
        paragraph(title, s["card_title"]),
        paragraph(desc, s["body"]),
    ]
    t = Table([[content]], colWidths=[83 * mm], rowHeights=[77 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4.5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def recent_cards(s: dict[str, ParagraphStyle]) -> Table:
    cards = [
        card(
            s,
            "feitos-para-brilhar.png",
            "Estudo Bíblico",
            "Feitos para brilhar pela Palavra da Vida",
            "Um estudo em Filipenses 2 sobre murmuração, pureza, testemunho e apego firme à Palavra em uma geração escura.",
        ),
        card(
            s,
            "coracao-desordenado.png",
            "Formação Interior",
            "O coração desordenado",
            "Quando o interior perde a ordem diante de Deus, a vida externa revela a fragmentação da alma.",
        ),
    ]
    table = Table([cards], colWidths=[84 * mm, 84 * mm])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 6 * mm)]))
    return table


def editorial(s: dict[str, ParagraphStyle]) -> Table:
    left = [
        paragraph("LINHA EDITORIAL", s["label"]),
        paragraph("Uma casa digital para Palavra, fé e vida cristã.", s["h3"]),
    ]
    bullets = [
        paragraph("- O artigo nasce de autoria humana.", s["bullet"]),
        paragraph("- A automação apoia imagem, resumo, metadados e organização.", s["bullet"]),
        paragraph("- A publicação final passa por aprovação antes de ir ao ar.", s["bullet"]),
    ]
    table = Table([[left, bullets]], colWidths=[70 * mm, 96 * mm], rowHeights=[42 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CREAM),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def main() -> None:
    register_fonts()
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        title="Verbo Vivo - Frontpage fictícia",
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="frontpage", showBoundary=0)
    doc.addPageTemplates([PageTemplate(id="frontpage", frames=[frame], onPage=draw_page)])

    s = styles()
    story = [
        masthead(s),
        Spacer(1, 8 * mm),
        hero(s),
        Spacer(1, 8 * mm),
        paragraph("PUBLICAÇÕES RECENTES", s["label"]),
        paragraph("Textos humanos, preparados com cuidado editorial", s["h3"]),
        paragraph(
            "Este modelo mostra como a página inicial pode apresentar artigos escritos por fonte humana, com imagens contextuais, resumos, categorias e organização pronta para SEO.",
            s["body"],
        ),
        Spacer(1, 6 * mm),
        recent_cards(s),
        Spacer(1, 7 * mm),
        KeepTogether(editorial(s)),
    ]
    doc.build(story)
    print(OUT.resolve())


if __name__ == "__main__":
    main()
