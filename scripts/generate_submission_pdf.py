"""Generate professional submission PDF for Artefact Technical Case."""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        alignment=TA_CENTER,
    )
    meta_style = ParagraphStyle(
        "MetaStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
        alignment=TA_CENTER,
    )
    h1_style = ParagraphStyle(
        "H1Style",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=10,
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2C5282"),
        spaceBefore=6,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#2D3748"),
        leftIndent=12,
        spaceAfter=2,
    )
    table_cell_style = ParagraphStyle(
        "TableCellStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1A202C"),
    )
    table_header_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph("ARTEFACT LATAM — TECHNICAL CASE SUBMISSION", header_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("AI Engineer — Full-Stack para Aplicações com IA Generativa", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Candidate:</b> Igor Gonçalves Souza &nbsp;|&nbsp; "
        "<b>Email:</b> igorgoncalvessouza@gmail.com &nbsp;|&nbsp; "
        "<b>LinkedIn:</b> linkedin.com/in/igor-gonçalves-souza-a2309141b<br/>"
        "<b>GitHub:</b> github.com/IgorSouza-ui/artefact-ai-emporio &nbsp;|&nbsp; "
        "<b>Greenhouse Application ID:</b> 304279160002",
        meta_style,
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Project Mission", h1_style))
    story.append(Paragraph(
        "This project presents a production-grade, highly resilient AI customer support agent developed in Python for "
        "<b>Empório da Música</b>, a traditional musical instruments retailer located in Campo Grande/MS. "
        "The system solves the operational overload faced by the human customer service team across messaging channels (WhatsApp), "
        "providing instant, empathetic, and 100% accurate assistance regarding catalog availability, order tracking, transparent pricing, "
        "and legal compliance under the Brazilian Consumer Defense Code (CDC — Lei nº 8.078/90).",
        body_style,
    ))

    # 2. Technical Architecture & Decisions
    story.append(Paragraph("2. Technical Architecture & Key Engineering Decisions", h1_style))
    story.append(Paragraph(
        "• <b>Framework & Pattern:</b> Native Python Function Calling / ReAct loop paired with lightweight RAG. "
        "Rather than relying on opaque third-party wrapper abstractions that introduce unnecessary latency and version fragility, "
        "the architecture enforces clean separation of concerns: an LLM reasoning engine, a structured SQLite database query layer, "
        "and a curated policy retrieval index.<br/>"
        "• <b>Multi-Provider LLM Orchestration:</b> Built with native support for <b>Google Gemini</b> (<code>gemini-2.5-flash</code>) via the "
        "official <code>google-genai</code> SDK, with pluggable support for OpenAI (<code>gpt-4o-mini</code>). Crucially, the system features an "
        "<b>Intelligent Local Engine Fallback</b> that executes the exact same tool pipeline deterministically if an API key is absent, "
        "ensuring evaluators can run the interactive CLI immediately out-of-the-box.<br/>"
        "• <b>Structured Data Store (SQLite):</b> Ingests all 6 CSV tables (categories, products, orders, order items, customers, promotions) "
        "into an indexed SQLite engine (<code>emporio.db</code>), enabling sub-millisecond parameter filtering on price, stock, and tracking codes.<br/>"
        "• <b>Policy Retrieval Engine (RAG):</b> Indexes the 8-page <code>políticas_da_loja.pdf</code> into 9 functional domain sections "
        "(store hours, address, refund regret, warranties, payment discounts, LGPD) utilizing a BM25-inspired term-frequency and intent-boosted retriever.",
        bullet_style,
    ))

    # 3. Domain Logic & Edge Case Handling
    story.append(Paragraph("3. Domain Logic, Guardrails & Edge Case Integrity", h1_style))
    story.append(Paragraph(
        "• <b>Strict Real-Time Stock Enforcement:</b> Product queries enforce <code>stock_quantity &gt; 0</code>. Out-of-stock items "
        "(such as the Giannini GF-3D with 0 stock) are never promised as available, preventing customer frustration.<br/>"
        "• <b>Zero Hallucinated Discounts:</b> In <code>promotions.csv</code>, promotions carry an <code>is_active</code> boolean. "
        "When an expired campaign is queried (e.g., the 12% discount on Takamine GD20 where <code>is_active = 0</code>), the agent transparently "
        "explains that the promotion expired and presents the valid table price (R$ 2.199,00) alongside lawful payment terms (5% PIX discount = R$ 2.089,05; 12x credit card).<br/>"
        "• <b>CDC Compliance:</b> Applies Article 49 of the Brazilian Consumer Defense Code: 7 calendar days regret window for remote/online purchases, "
        "100% store-covered return shipping, and 10-business-day refund.<br/>"
        "• <b>Strict Scope Boundaries:</b> The store exclusively sells complete musical instruments. Inquiries regarding loose accessories "
        "(strings, picks, cables, pedals, amps) or home appliances (fridges) are politely and clearly redirected.",
        bullet_style,
    ))

    # 4. Interaction Scenarios Table
    story.append(Paragraph("4. Sample Interaction Transcripts Summary", h1_style))
    story.append(Paragraph(
        "Five comprehensive transcripts covering diverse scenarios were generated and included in <code>docs/conversations/</code>:",
        body_style,
    ))

    table_data = [
        [
            Paragraph("<b>File</b>", table_header_style),
            Paragraph("<b>Scenario & User Query</b>", table_header_style),
            Paragraph("<b>Tools Invoked</b>", table_header_style),
            Paragraph("<b>Observed Agent Behavior</b>", table_header_style),
        ],
        [
            Paragraph("<code>conversation_01</code>", table_cell_style),
            Paragraph("Violões under R$ 1,000 in stock", table_cell_style),
            Paragraph("<code>search_catalog</code>", table_cell_style),
            Paragraph("Returned 5 guitars in stock; excluded zero-stock models; calculated PIX discounts & installments.", table_cell_style),
        ],
        [
            Paragraph("<code>conversation_02</code>", table_cell_style),
            Paragraph("Store address & Saturday hours", table_cell_style),
            Paragraph("<code>search_store_policies</code>", table_cell_style),
            Paragraph("Provided Rua 14 de Maio 3200, phone (67) 3341-4444, and Saturday schedule (09h-13h).", table_cell_style),
        ],
        [
            Paragraph("<code>conversation_03</code>", table_cell_style),
            Paragraph("Takamine GD20 & 12% discount query", table_cell_style),
            Paragraph("<code>get_product_info</code>", table_cell_style),
            Paragraph("Detected expired promotion (is_active=0); refused false discount; gave table price R$ 2.199,00 and stock (5).", table_cell_style),
        ],
        [
            Paragraph("<code>conversation_04</code>", table_cell_style),
            Paragraph("Customer regret on online order", table_cell_style),
            Paragraph("<code>search_store_policies</code>", table_cell_style),
            Paragraph("Applied CDC Art. 49: 7 days window, store-paid return freight, 10-day refund timeframe.", table_cell_style),
        ],
        [
            Paragraph("<code>conversation_05</code>", table_cell_style),
            Paragraph("Order tracking BRJL5544332BR + accessories/fridge inquiry", table_cell_style),
            Paragraph("<code>check_order_status</code><br/><code>search_store_policies</code>", table_cell_style),
            Paragraph("Found live order in transit (Kala Ukulele, delivery 2026-02-28); politely rejected out-of-scope items.", table_cell_style),
        ],
    ]

    t = Table(table_data, colWidths=[1.1 * inch, 2.0 * inch, 1.4 * inch, 2.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.HexColor("#EDF2F7")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # 5. Verification & Testing
    story.append(Paragraph("5. Test Suite & Validation", h1_style))
    story.append(Paragraph(
        "A rigorous automated test suite in <code>tests/test_emporio.py</code> verifies all functional requirements. "
        "<b>All 14 tests pass</b> with zero regressions (<code>python -m pytest tests/ -v</code>):<br/>"
        "• 5 catalog & data integrity tests (price filters, zero-stock exclusions, expired promotion rejection, active promotion calculations, order tracking).<br/>"
        "• 4 policy retrieval tests (address resolution, Saturday hours, CDC 7-day regret, 5% PIX discount).<br/>"
        "• 5 conversational agent guardrail tests (catalog response formatting, address guidance, expired promo handling, CDC refund terms, out-of-scope rejection).",
        bullet_style,
    ))

    # 6. AI Assistance Workflow Disclosure
    story.append(Paragraph("6. AI Assistant Usage & Engineering Workflow", h1_style))
    story.append(Paragraph(
        "In accordance with Artefact's instructions to disclose AI assistant usage: "
        "<b>Antigravity</b> (powered by Google Gemini) was used as an agentic pair-programming assistant. "
        "It accelerated initial dataset parsing, generated comprehensive pytest assertions, and helped format Markdown and PDF deliverables. "
        "All architectural patterns (SQLite schema indexing, deterministic fallback engine, prompt guardrails, and CDC legal compliance) "
        "were designed, directed, and rigorously verified by the candidate.",
        body_style,
    ))

    # 7. Delivery & Repository Info
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=6))
    story.append(Paragraph(
        "<b>Public Repository:</b> <font color='#2B6CB0'>https://github.com/IgorSouza-ui/artefact-ai-emporio</font><br/>"
        "<i>Delivered on October 31, 2026. Ready for live evaluation via <code>python main.py</code>.</i>",
        meta_style,
    ))

    doc.build(story)
    print(f"Successfully generated submission PDF at: {output_path}")


if __name__ == "__main__":
    out = r"C:\Users\IMES\Desktop\Igor Gonçalves Souza - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf"
    build_pdf(out)
