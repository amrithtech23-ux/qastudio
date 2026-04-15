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
    .success-msg {
        background: #d1fae5;
        color: #065f46;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
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
if 'source_text' not in st.session_state:
    st.session_state.source_text = ''

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"PDF extraction error: {e}")
    return text

def parse_questions(txt_file):
    """Parse questions from text file"""
    content = txt_file.read().decode('utf-8')
    
    # Try different question patterns
    patterns = [
        r'Q\d+[:\.\s]+(.+?)(?=\nQ\d+|\n\n|\Z)',  # Q1. or Q1:
        r'\d+\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)',     # 1. Question
        r'^(.+?\?)\s*$'                          # Lines ending with ?
    ]
    
    questions = []
    for pattern in patterns:
        questions = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        if questions:
            questions = [q.strip() for q in questions if q.strip() and '?' in q]
            break
    
    # Fallback: split by lines and find questions
    if not questions:
        lines = content.split('\n')
        questions = [line.strip() for line in lines 
                    if line.strip() and ('?' in line or line.strip().startswith('Q'))]
    
    # Remove duplicates and clean up
    questions = list(dict.fromkeys(questions))
    questions = [q for q in questions if len(q) > 5]
    
    return questions

def extract_keywords(question):
    """Extract important keywords from question"""
    # Remove question words and common words
    stop_words = {
        'what', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'how', 'why', 'when', 'where', 'which',
        'who', 'whom', 'whose', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'define', 'state', 'name', 'explain', 'describe', 'list', 'mention'
    }
    
    # Remove question mark and split
    words = re.sub(r'[?]', '', question).lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

def find_answer_in_text(question, source_text, config):
    """Find answer for the question in source text"""
    keywords = extract_keywords(question)
    
    if not keywords:
        return "Unable to find answer - insufficient keywords"
    
    # Split source into sections (by double newlines or page breaks)
    sections = re.split(r'\n\s*\n|--- Page \d+ ---', source_text)
    
    best_answer = ""
    best_score = 0
    best_context = ""
    
    # Search in each section
    for section in sections:
        section = section.strip()
        if len(section) < 50:  # Skip very short sections
            continue
        
        section_lower = section.lower()
        question_lower = question.lower()
        
        # Count keyword matches
        keyword_matches = sum(1 for kw in keywords if kw in section_lower)
        score = keyword_matches / len(keywords) if keywords else 0
        
        # Check for exact phrase matches
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', section_lower):
                score += 0.2
        
        # Bonus for sections that contain answer-like patterns
        answer_patterns = [
            r'is\s+\w+',
            r'are\s+\w+',
            r'called\s+\w+',
            r'defined\s+as',
            r'means\s+',
            r'refers\s+to',
        ]
        
        for pattern in answer_patterns:
            if re.search(pattern, section_lower):
                score += 0.1
        
        if score > best_score:
            best_score = score
            best_context = section
    
    # If we found a relevant section, extract the answer
    if best_score > 0.3 and best_context:
        # Try to find the most relevant sentence
        sentences = re.split(r'[.!?]+', best_context)
        
        best_sentence = ""
        best_sentence_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            sentence_lower = sentence.lower()
            sent_score = sum(1 for kw in keywords if kw in sentence_lower)
            
            if sent_score > best_sentence_score:
                best_sentence_score = sent_score
                best_sentence = sentence
        
        # Use the best sentence or the whole context
        if best_sentence and len(best_sentence) > 20:
            best_answer = best_sentence.strip()
        else:
            # Extract first few lines from context
            lines = best_context.split('\n')
            relevant_lines = []
            for line in lines:
                line = line.strip()
                if any(kw in line.lower() for kw in keywords):
                    relevant_lines.append(line)
                    if len(relevant_lines) >= config['max_lines']:
                        break
            
            if relevant_lines:
                best_answer = ' '.join(relevant_lines)
            else:
                best_answer = best_context.split('\n')[0] if best_context.split('\n') else best_context
    
    # If no good answer found
    if not best_answer or best_score < 0.3:
        # Try a different approach - look for definitions
        definition_pattern = r'(?:' + '|'.join(keywords) + r')\s+(?:is|are|means|refers to|called)\s+([^.\n]+)'
        match = re.search(definition_pattern, source_text, re.IGNORECASE)
        
        if match:
            best_answer = match.group(0).strip()
        else:
            return "Answer not found in the provided source material. Please check if the PDF contains relevant content."
    
    # Format answer according to config
    words = best_answer.split()
    
    # Limit by word count
    if config['max_words'] and len(words) > config['max_words']:
        words = words[:config['max_words']]
        best_answer = ' '.join(words)
    
    # Limit by lines
    lines = best_answer.split('\n')
    if config['max_lines'] and len(lines) > config['max_lines']:
        lines = lines[:config['max_lines']]
        best_answer = '\n'.join(lines)
    
    return best_answer.strip()

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
        answer = find_answer_in_text(question, source_text, cfg)
        
        answers.append({
            'question': question,
            'answer': answer,
            'word_count': len(answer.split()),
            'line_count': len(answer.split('\n')),
            'marks': question_type
        })
        
        # Update progress
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
                with st.spinner("📖 Extracting text from PDF..."):
                    source_text = extract_text_from_pdf(pdf_file)
                    st.session_state.source_text = source_text
                
                if not source_text or len(source_text.strip()) < 100:
                    st.error("❌ Could not extract sufficient text from PDF. Please check the file.")
                    st.stop()
                
                st.success(f"✅ Extracted {len(source_text)} characters from PDF")
                
                # Parse questions
                with st.spinner("❓ Parsing questions..."):
                    txt_file.seek(0)  # Reset file pointer
                    questions = parse_questions(txt_file)
                
                if not questions:
                    st.error("❌ No questions found in the uploaded file.")
                    st.stop()
                
                st.success(f"✅ Found {len(questions)} questions")
                
                # Generate answers
                with st.spinner("🤖 Generating answers..."):
                    answers = generate_answers(questions, source_text, question_type)
                
                st.session_state.answers = answers
                st.session_state.question_type = question_type
                
                st.markdown('<div class="success-msg">✅ Successfully generated {} answers!</div>'.format(len(answers)), unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error processing files: {e}")
                import traceback
                st.code(traceback.format_exc())
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
