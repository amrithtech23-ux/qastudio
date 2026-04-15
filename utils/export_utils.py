from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from config import Config

def export_to_pdf(answers, question_type, filename):
    """
    Export answers to PDF format
    """
    filepath = os.path.join(Config.EXPORT_FOLDER, 'pdf', filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1  # Center
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.HexColor('#64748b'),
        alignment=1
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=5,
        textColor=colors.HexColor('#0f172a')
    )
    
    answer_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        leftIndent=20,
        textColor=colors.HexColor('#374151')
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph('QA Studio - Generated Answers', title_style))
    story.append(Paragraph(f'Question Type: {question_type} Marks', subtitle_style))
    story.append(Spacer(1, 20))
    
    # Answers
    for idx, item in enumerate(answers, 1):
        # Question
        story.append(Paragraph(f'Q{idx}. {item["question"]}', question_style))
        
        # Answer
        story.append(Paragraph(item['answer'], answer_style))
        
        # Metadata
        meta_text = f"Words: {item['word_count']} | Lines: {item['line_count']} | Confidence: {item['confidence']:.0%}"
        story.append(Paragraph(meta_text, styles['Italic']))
        
        story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    return filepath

def export_to_html(answers, question_type, filename):
    """
    Export answers to HTML format
    """
    filepath = os.path.join(Config.EXPORT_FOLDER, 'html', filename)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QA Studio - Answers</title>
        <style>
            body {
                font-family: 'Georgia', serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                background: #f8fafc;
                color: #1e293b;
            }
            .header {
                text-align: center;
                margin-bottom: 3rem;
                padding-bottom: 2rem;
                border-bottom: 3px solid #1e3a8a;
            }
            .header h1 {
                color: #1e3a8a;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .header p {
                color: #64748b;
                font-size: 1.1rem;
            }
            .answer-card {
                background: white;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #3b82f6;
            }
            .question {
                font-weight: bold;
                color: #0f172a;
                font-size: 1.1rem;
                margin-bottom: 0.75rem;
            }
            .answer {
                background: #f0f9ff;
                padding: 1rem;
                border-radius: 4px;
                line-height: 1.6;
                margin-bottom: 0.75rem;
            }
            .meta {
                font-size: 0.85rem;
                color: #64748b;
                display: flex;
                gap: 1rem;
            }
            .footer {
                text-align: center;
                margin-top: 3rem;
                padding-top: 2rem;
                border-top: 1px solid #e2e8f0;
                color: #64748b;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 QA Studio</h1>
            <p>Generated Answers - {} Mark Questions</p>
        </div>
    """.format(question_type)
    
    for idx, item in enumerate(answers, 1):
        html_content += """
        <div class="answer-card">
            <div class="question">Q{}. {}</div>
            <div class="answer">{}</div>
            <div class="meta">
                <span>📝 {} words</span>
                <span>📄 {} lines</span>
                <span>✓ {:.0%} confidence</span>
            </div>
        </div>
        """.format(idx, item['question'], item['answer'], 
                   item['word_count'], item['line_count'], item['confidence'])
    
    html_content += """
        <div class="footer">
            <p>Generated by QA Studio | Academic Excellence Tool</p>
        </div>
    </body>
    </html>
    """
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filepath
