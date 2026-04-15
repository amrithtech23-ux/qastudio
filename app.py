import streamlit as st
import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
import re
from io import BytesIO

# Page config
st.set_page_config(
    page_title="QA Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for academic theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    .answer-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .question-text {
        font-weight: bold;
        color: #1e3a8a;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .answer-text {
        background: #f0f9ff;
        padding: 1rem;
        border-radius: 4px;
        border-left: 3px solid #10b981;
        margin: 0.5rem 0;
    }
    .mark-badge {
        display: inline-block;
        background: #f59e0b;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📚 QA Studio</h1>
    <p>Intelligent Question-Answer Generator for Academic Excellence</p>
</div>
""", unsafe_allow_html=True)

# Session state initialization
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'question_type' not in st.session_state:
    st.session_state.question_type = '1'

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"PDF extraction error: {e}")
    return text

def parse_questions(txt_file):
    """Parse questions from text file"""
    content = txt_file.read().decode('utf-8')
    
    # Try different question patterns
    patterns = [
        r'\d+\.\s+(.+?)(?=\n\d+\.|\Z)',  # 1. Question
        r'-\s+(.+?)(?=\n-|\Z)',           # - Question
        r'Q\d+[:\s]+(.+?)(?=\nQ\d+|\Z)', # Q1: Question
    ]
    
    questions = []
    for pattern in patterns:
        questions = re.findall(pattern, content, re.DOTALL)
        if questions:
            questions = [q.strip() for q in questions if q.strip()]
            break
    
    # Fallback: split by lines
    if not questions:
        lines = content.split('\n')
        questions = [line.strip() for line in lines 
                    if line.strip() and len(line.strip()) > 10]
    
    # Remove duplicates
    return list(dict.fromkeys(questions))

def generate_answers(questions, source_text, question_type):
    """Generate answers based on question type"""
    config = {
        '1': {'max_words': 2, 'max_lines': 1, 'desc': 'Brief (2 words)'},
        '2': {'max_words': 20, 'max_lines': 2, 'desc': 'Short (2 lines)'},
        '4': {'max_words': 80, 'max_lines': 5, 'desc': 'Medium (5 lines)'},
        '7': {'max_words': 150, 'max_lines': 8, 'desc': 'Detailed (8 lines)'}
    }
    
    answers = []
    cfg = config.get(question_type, config['1'])
    
    for question in questions:
        answer = find_best_answer(question, source_text, cfg)
        answers.append({
            'question': question,
            'answer': answer,
            'word_count': len(answer.split()),
            'line_count': len(answer.split('\n')),
            'marks': question_type
        })
    
    return answers

def find_best_answer(question, source_text, config):
    """Find the best answer in source text"""
    # Extract keywords (words longer than 3 chars)
    keywords = [w.lower() for w in question.split() if len(w) > 3]
    
    # Split source into paragraphs
    paragraphs = re.split(r'\n\s*\n', source_text)
    
    best_answer = ""
    best_score = 0
    
    for para in paragraphs:
        if len(para.strip()) < 20:
            continue
        
        # Calculate relevance score
        matches = sum(1 for kw in keywords if kw in para.lower())
        score = matches / len(keywords) if keywords else 0
        
        if score > best_score:
            best_score = score
            best_answer = para.strip()
    
    # If no good match found
    if best_score < 0.3:
        return "Answer not found in the provided source material."
    
    # Format answer according to config
    words = best_answer.split()
    if len(words) > config['max_words']:
        words = words[:config['max_words']]
    
    answer = ' '.join(words)
    
    # Limit lines
    lines = answer.split('\n')
    if len(lines) > config['max_lines']:
        lines = lines[:config['max_lines']]
        answer = '\n'.join(lines)
    
    return answer.strip()

def export_to_pdf(answers):
    """Export answers to PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=1
    )
    
    story = []
    story.append(Paragraph('QA Studio - Generated Answers', title_style))
    story.append(Spacer(1, 20))
    
    for idx, item in enumerate(answers, 1):
        q_text = f"Q{idx}. {item['question']}"
        story.append(Paragraph(q_text, styles['Normal']))
        story.append(Paragraph(item['answer'], styles['Normal']))
        story.append(Spacer(1, 10))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Main UI
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Source Material")
    pdf_file = st.file_uploader(
        "Upload PDF",
        type=['pdf'],
        help="Upload your study material or textbook"
    )
    if pdf_file:
        st.success(f"✅ {pdf_file.name}")

with col2:
    st.markdown("### ❓ Questions File")
    txt_file = st.file_uploader(
        "Upload TXT",
        type=['txt'],
        help="Upload your questions in text format"
    )
    if txt_file:
        st.success(f"✅ {txt_file.name}")

# Question type selection
st.markdown("### 📊 Question Type")
question_type = st.radio(
    "Select mark allocation:",
    ["1", "2", "4", "7"],
    horizontal=True,
    help="Choose the type of questions to generate answers for"
)

type_descriptions = {
    '1': 'Brief answers (max 2 words)',
    '2': 'Short answers (max 2 lines)',
    '4': 'Medium answers (max 5 lines)',
    '7': 'Detailed answers (max 8 lines)'
}

st.info(f"📝 {type_descriptions[question_type]}")

# Process button
if st.button("🔍 Generate Answers", type="primary", use_container_width=True):
    if pdf_file and txt_file:
        with st.spinner("Processing your files... This may take a moment."):
            try:
                # Extract text from PDF
                source_text = extract_text_from_pdf(pdf_file)
                
                if not source_text:
                    st.error("Could not extract text from PDF. Please check the file.")
                    st.stop()
                
                # Parse questions
                txt_file.seek(0)  # Reset file pointer
                questions = parse_questions(txt_file)
                
                if not questions:
                    st.error("No questions found in the uploaded file.")
                    st.stop()
                
                # Generate answers
                answers = generate_answers(questions, source_text, question_type)
                
                st.session_state.answers = answers
                st.session_state.question_type = question_type
                
                st.success(f"✅ Successfully generated {len(answers)} answers!")
                
            except Exception as e:
                st.error(f"Error processing files: {e}")
    else:
        st.error("⚠️ Please upload both PDF and TXT files")

# Display answers
if st.session_state.answers:
    st.markdown("---")
    st.markdown("### 📋 Generated Answers Preview")
    
    for idx, item in enumerate(st.session_state.answers, 1):
        with st.expander(f"❓ Q{idx}: {item['question'][:100]}...", expanded=False):
            st.markdown(f"""
            <div class="answer-card">
                <div class="question-text">Q{idx}. {item['question']}</div>
                <div class="answer-text">
                    <strong>Answer:</strong><br>
                    {item['answer']}
                </div>
                <div style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
                    📝 {item['word_count']} words | 
                    📄 {item['line_count']} lines | 
                    <span class="mark-badge">{item['marks']} Mark</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Export section
    st.markdown("---")
    st.markdown("### 📥 Export Answers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export as PDF", use_container_width=True):
            try:
                pdf_buffer = export_to_pdf(st.session_state.answers)
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_buffer,
                    file_name=f"QA_Studio_Answers_{question_type}_marks.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export error: {e}")
    
    with col2:
        st.info("HTML export coming soon!")

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    1. **Upload PDF** - Your study material
    2. **Upload TXT** - Your questions file
    3. **Select Type** - Choose mark allocation
    4. **Generate** - Click the button
    5. **Export** - Download your answers
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Answer Lengths")
    st.markdown("""
    - **1 Mark**: Max 2 words
    - **2 Marks**: Max 2 lines
    - **4 Marks**: Max 5 lines
    - **7 Marks**: Max 8 lines
    """)
    
    st.markdown("---")
    st.caption("QA Studio v1.0 | Built for Academic Excellence")
