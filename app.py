import streamlit as st
import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import re
from io import BytesIO

# Page config
st.set_page_config(
    page_title="QA Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .answer-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #10b981;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .question-text {
        font-weight: bold;
        color: #1e3a8a;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .answer-text {
        background: #f0fdf4;
        padding: 1rem;
        border-radius: 4px;
        border-left: 3px solid #10b981;
        margin: 0.5rem 0;
        line-height: 1.6;
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

# Session state
if 'answers' not in st.session_state:
    st.session_state.answers = []

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
    questions = []
    
    # Find all questions starting with Q followed by number
    pattern = r'Q\d+\.\s*(.+?)\?'
    matches = re.findall(pattern, content, re.IGNORECASE)
    questions = [match.strip() + '?' for match in matches]
    
    if not questions:
        # Fallback: split by lines
        lines = content.split('\n')
        questions = [line.strip() for line in lines if line.strip() and '?' in line]
    
    return questions

def find_answer(question, source_text, config):
    """Find answer for a specific question"""
    question_lower = question.lower()
    
    # Extract keywords from question (remove common words)
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'how', 'why', 'when', 'where', 'which',
                  'who', 'whom', 'whose', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                  'define', 'state', 'name', 'explain', 'describe', 'list', 'mention',
                  'according', 'called', 'type', 'unit', 'si', 'property', 'body', 'bodies'}
    
    keywords = [w for w in question_lower.split() if w not in stop_words and len(w) > 2]
    
    # Split source text into sentences
    sentences = re.split(r'[.!?]+', source_text)
    
    best_answer = ""
    best_score = 0
    
    # Search for the best matching sentence
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        
        sentence_lower = sentence.lower()
        
        # Count keyword matches
        score = sum(1 for kw in keywords if kw in sentence_lower)
        
        # Bonus for exact phrase matches
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', sentence_lower):
                score += 0.5
        
        # Check for answer patterns
        if any(pattern in sentence_lower for pattern in ['is called', 'are called', 'known as', 'defined as', 'is', 'are']):
            score += 1
        
        if score > best_score:
            best_score = score
            best_answer = sentence.strip()
    
    # If we found a good match, format it
    if best_score > 0 and best_answer:
        # Clean up the answer
        best_answer = re.sub(r'\s+', ' ', best_answer).strip()
        
        # Remove figure references and page numbers
        best_answer = re.sub(r'Figure\s*\d+\.?\d*', '', best_answer, flags=re.IGNORECASE)
        best_answer = re.sub(r'\d+\s*th\s*Standard', '', best_answer, flags=re.IGNORECASE)
        
        # Limit by word count
        words = best_answer.split()
        if len(words) > config['max_words']:
            # Try to find the most important part
            for kw in keywords:
                if kw in best_answer.lower():
                    # Find the position of the keyword
                    idx = best_answer.lower().find(kw)
                    # Get context around the keyword
                    start = max(0, idx - 20)
                    end = min(len(best_answer), idx + len(kw) + 50)
                    best_answer = best_answer[start:end].strip()
                    break
            
            # If still too long, just truncate
            words = best_answer.split()
            if len(words) > config['max_words']:
                best_answer = ' '.join(words[:config['max_words']])
        
        # Limit by lines
        lines = best_answer.split('\n')
        if len(lines) > config['max_lines']:
            lines = lines[:config['max_lines']]
            best_answer = '\n'.join(lines)
        
        return best_answer.strip()
    
    return "Answer not found in the provided source material."

def generate_answers(questions, source_text, question_type):
    """Generate answers based on question type"""
    config = {
        '1': {'max_words': 2, 'max_lines': 1, 'desc': 'Brief (2 words)'},
        '2': {'max_words': 30, 'max_lines': 2, 'desc': 'Short (2 lines)'},
        '4': {'max_words': 100, 'max_lines': 5, 'desc': 'Medium (5 lines)'},
        '7': {'max_words': 200, 'max_lines': 8, 'desc': 'Detailed (8 lines)'}
    }
    
    answers = []
    cfg = config.get(question_type, config['1'])
    
    progress_bar = st.progress(0)
    
    for idx, question in enumerate(questions):
        answer = find_answer(question, source_text, cfg)
        
        answers.append({
            'question': question,
            'answer': answer,
            'word_count': len(answer.split()),
            'line_count': len(answer.split('\n')),
            'marks': question_type
        })
        
        progress_bar.progress((idx + 1) / len(questions))
    
    return answers

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
    pdf_file = st.file_uploader("Upload PDF", type=['pdf'])
    if pdf_file:
        st.success(f"✅ {pdf_file.name}")

with col2:
    st.markdown("### ❓ Questions File")
    txt_file = st.file_uploader("Upload TXT", type=['txt'])
    if txt_file:
        st.success(f"✅ {txt_file.name}")

# Question type selection
st.markdown("### 📊 Question Type")
question_type = st.radio(
    "Select mark allocation:",
    ["1", "2", "4", "7"],
    horizontal=True
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
        with st.spinner("Processing your files..."):
            try:
                # Extract text
                source_text = extract_text_from_pdf(pdf_file)
                
                if not source_text or len(source_text.strip()) < 100:
                    st.error("❌ Could not extract sufficient text from PDF.")
                    st.stop()
                
                # Parse questions
                txt_file.seek(0)
                questions = parse_questions(txt_file)
                
                if not questions:
                    st.error("❌ No questions found in the uploaded file.")
                    st.stop()
                
                # Generate answers
                answers = generate_answers(questions, source_text, question_type)
                
                st.session_state.answers = answers
                
                st.success(f"✅ Successfully generated {len(answers)} answers!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.error("⚠️ Please upload both PDF and TXT files")

# Display answers
if st.session_state.answers:
    st.markdown("---")
    st.markdown("### 📋 Generated Answers Preview")
    
    for idx, item in enumerate(st.session_state.answers, 1):
        st.markdown(f"""
        <div class="answer-card">
            <div class="question-text">❓ Q{idx}. {item['question']}</div>
            <div class="answer-text">
                <strong>✅ Answer:</strong><br>
                {item['answer']}
            </div>
            <div style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">
                📝 {item['word_count']} words | 
                📄 {item['line_count']} lines | 
                <span class="mark-badge">{item['marks']} Mark</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Export
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
