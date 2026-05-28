import sys

sys.stdout.reconfigure(encoding='utf-8')

# Definition of the raw text containing parsing anomalies
clean_legal_text = """MASTER FRAMEWORK AGREEMENT
DOCUMENT REFERENCE: MFA-2026-NX9
STATUS: [PENDING REVISION - 28/05/26] -> Marginal Scribble: "Verify cross-border data clause before routing to executive committee."

-------------------------------------------------------------------------------
THIS MASTER FRAMEWORK AGREEMENT (the "Agreement") is executed and made effective as of the 28th day of May, 2026 (the "Effective Date").

BY AND BETWEEN:
1. APEX GLOBAL TECHNOLOGIES PRIVATE LIMITED, a corporate entity registered under the prevailing commercial statutes, having its principal place of business at Mumbai, Maharashtra, India (hereinafter referred to as the "Discloser" or "Company");
AND
2. THE INDEPENDENT OPERATOR / CONSULTANT, acting as an external counterparty engaged in data classification and algorithmic validation sequences (hereinafter referred to as the "Recipient" or "Contractor").

WHEREAS, the Company owns highly confidential structural systems, document processing models, and proprietary corporate architectures; and the Recipient wishes to provide validation services.

NOW, THEREFORE, IT IS MUTUALLY COVENANTED AND AGREED AS FOLLOWS:

1. INTELLECTUAL PROPERTY & DATA PRIVACY CONSTRAINTS
1.1. The Recipient acknowledges that all ingestion methodologies, system-generated schemas, and structural node exports mapped from target files are the sole proprietary equity of the Company.
[Handwritten Margin Annotation: "Confirm if this covers markdown artifacts exported via custom layout parsers. - Legal Dept."]

1.2. The system performance thresholds, including precision indices, recall matrices, and structured field extractions, are internal estimations. The Company explicitly disclaims absolute liability for minor data omission thresholds under standard operational loads.
[Ink Stamp Override: PROVISIONAL CLEARANCE GRANTED - SUBJECT TO PARSER AUDIT]

1.3. *CONFLICT MATRIX SECTION 1.3*: "Notwithstanding any prior oral declarations or documentation to the contrary, the standard liability cap for any algorithmic or structural omission under this framework is strictly limited to $5,000 USD."
[Scrawled Marker Note over text: "Wait, the main service SLA explicitly mandates a liability limit of $50,000 USD for document data leaks! This is a severe mismatch—flag for downstream retrieval verification!"]

2. JURISDICTION AND DISPUTE RESOLUTION
2.1. This Agreement, its interpretation, and any breach thereof shall be governed exclusively by the commercial codes of the local jurisdiction, without giving effect to conflict of laws principles.

2.2. All disputes arising from or correlated with this agreement shall be settled through binding corporate arbitration conducted at the primary corporate registry hub.

-------------------------------------------------------------------------------
[FOOTER SYSTEM TRAILING MARK: LOW-RESOLUTION SCAN CHANNELS ACTIVE - 150 DPI COMPRESSION EMULATED - NOISE INJECTED ON SUB-CLAUSES 1.2 THROUGH 1.4]
"""

def generate_pdf_asset():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        doc = SimpleDocTemplate("legal_test_document.pdf", pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Mimic formal, high-density corporate text alignment
        legal_layout_style = ParagraphStyle(
            'LegalStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            spaceAfter=12
        )
        
        story = []
        for line in clean_legal_text.split('\n'):
            if line.strip() == "":
                story.append(Spacer(1, 8))
            else:
                # Basic XML character escaping for Reportlab compatibility
                safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(safe_line, legal_layout_style))
                
        doc.build(story)
        print("✓ Successfully generated 'legal_test_document.pdf' in the local working path.")
        
    except ImportError:
        print("ReportLab package not found. Run 'pip install reportlab' to compile the layout natively.")

if __name__ == "__main__":
    generate_pdf_asset()
