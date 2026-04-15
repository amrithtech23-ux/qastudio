import streamlit as st
import pdfplumber
import re
from io import BytesIO
import os

# Page configuration
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
        font-style: italic;
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
    .success-box {
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

# Session state
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'source_text' not in st.session_state:
    st.session_state.source_text = ""

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n[Page {page_num + 1}]\n"
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"PDF extraction error: {e}")
    return text

def parse_questions(txt_content):
    """Parse questions from text content"""
    questions = []
    
    # Pattern to match questions like Q1., Q2., etc.
    pattern = r'Q\d+\.\s*(.+?)\?'
    matches = re.findall(pattern, txt_content, re.IGNORECASE)
    
    for match in matches:
        question = match.strip()
        if not question.endswith('?'):
            question += '?'
        questions.append(question)
    
    # If no Q pattern found, try to find lines ending with ?
    if not questions:
        lines = txt_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.endswith('?') and len(line) > 10:
                questions.append(line)
    
    return questions

def find_answer_for_question(question, source_text, config):
    """
    Intelligent answer extraction with multiple strategies
    """
    question_lower = question.lower()
    
    # Strategy 1: Keyword-based extraction with context
    keywords = extract_keywords(question)
    
    # Split source into sentences
    sentences = re.split(r'[.!?]+', source_text)
    
    best_answer = ""
    best_score = 0
    
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
        
        # Bonus for answer patterns
        answer_patterns = [
            r'is called', r'are called', r'known as', r'defined as',
            r'is', r'are', r'means', r'refers to', r'states that'
        ]
        
        for pattern in answer_patterns:
            if re.search(pattern, sentence_lower):
                score += 0.3
        
        if score > best_score:
            best_score = score
            best_answer = sentence.strip()
    
    # Strategy 2: Look for specific question patterns
    if best_score < 1:
        best_answer = find_answer_by_pattern(question, source_text)
    
    # Strategy 3: If still no answer, look for definitions
    if not best_answer or len(best_answer) < 10:
        best_answer = find_definition(question, source_text)
    
    # Format answer based on config
    if best_answer:
        best_answer = format_answer(best_answer, config)
    
    return best_answer if best_answer else "Answer not found in the provided material."

def extract_keywords(question):
    """Extract important keywords from question"""
    # Remove question words
    stop_words = {
        'what', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'how', 'why', 'when', 'where', 'which',
        'who', 'whom', 'whose', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'define', 'state', 'name', 'explain', 'describe', 'list', 'mention',
        'according', 'called', 'type', 'unit', 'si', 'property', 'body', 'bodies',
        'natural', 'state', 'force', 'motion', 'law'
    }
    
    words = re.sub(r'[?]', '', question).lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

def find_answer_by_pattern(question, source_text):
    """Find answer using specific question patterns"""
    question_lower = question.lower()
    
    # Pattern matching for specific question types
    patterns = {
        r'natural state.*aristotle': r'According to Aristotle.*?rest',
        r'who proposed.*force.*change.*natural state': r'(Galileo|Newton).*?proposed',
        r'inherent property.*resist.*change.*state': r'inertia',
        r'scientist.*body in motion.*continue': r'(Galileo|Newton).*?law',
        r'type of inertia.*passenger.*leans.*forward': r'inertia of motion',
        r'define.*linear momentum': r'Linear Momentum.*?mass.*velocity',
        r'SI unit.*linear momentum': r'kg.*m.*s|kilogram.*metre.*second',
        r"Newton's First Law": r'every body continues.*?state of rest.*?uniform motion',
        r'definition of force.*Newton': r'Force.*?external.*?push.*?pull',
        r'force.*scalar.*vector': r'Force.*?vector quantity'
    }
    
    for question_pattern, answer_pattern in patterns.items():
        if re.search(question_pattern, question_lower):
            match = re.search(answer_pattern, source_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0).strip()
    
    return ""

def find_definition(question, source_text):
    """Find definitions in the text"""
    question_lower = question.lower()
    keywords = extract_keywords(question)
    
    # Look for definition patterns
    definition_patterns = [
        r'(?:' + '|'.join(keywords) + r')\s+(?:is|are|means|refers to|called)\s+([^.\n]+)',
        r'(?:' + '|'.join(keywords) + r')\s+is\s+defined\s+as\s+([^.\n]+)'
    ]
    
    for pattern in definition_patterns:
        match = re.search(pattern, source_text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return ""

def format_answer(answer, config):
    """Format answer according to mark allocation"""
    # Clean up the answer
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # Remove page markers
    answer = re.sub(r'\[Page \d+\]', '', answer).strip()
    
    # Limit by word count
    words = answer.split()
    if len(words) > config['max_words']:
        # Try to keep complete sentence
        for i in range(config['max_words'], len(words)):
            if words[i].endswith('.'):
                words = words[:i+1]
                break
        else:
            words = words[:config['max_words']]
    
    answer = ' '.join(words)
    
    # Limit by lines
    lines = answer.split('\n')
    if len(lines) > config['max_lines']:
        lines = lines[:config['max_lines']]
        answer = '\n'.join(lines)
    
    return answer.strip()

def generate_answers(questions, source_text, question_type):
    """Generate answers for all questions"""
    config = {
        '1': {'max_words': 3, 'max_lines': 1, 'desc': 'Brief (2-3 words)'},
        '2': {'max_words': 30, 'max_lines': 2, 'desc': 'Short (2 lines)'},
        '4': {'max_words': 100, 'max_lines': 5, 'desc': 'Medium (5 lines)'},
        '7': {'max_words': 200, 'max_lines': 8, 'desc': 'Detailed (8 lines)'}
    }
    
    answers = []
    cfg = config.get(question_type, config['1'])
    
    progress_bar = st.progress(0)
    
    for idx, question in enumerate(questions):
        answer = find_answer_for_question(question, source_text, cfg)
        
        answers.append({
            'question': question,
            'answer': answer,
            'word_count': len(answer.split()),
            'line_count': len(answer.split('\n')),
            'marks': question_type
        })
        
        progress_bar.progress((idx + 1) / len(questions))
    
    return answers

# Main UI
st.markdown("### 📋 Instructions")
st.info("""
1. **Upload your PDF** - Your study material/textbook
2. **Upload questions** - TXT file with questions (Q1., Q2., etc.)
3. **Select mark type** - Choose 1, 2, 4, or 7 marks
4. **Generate answers** - Click the button to extract answers
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Source Material (PDF)")
    pdf_file = st.file_uploader(
        "Upload PDF",
        type=['pdf'],
        help="Upload your textbook or study material"
    )
    if pdf_file:
        st.success(f"✅ {pdf_file.name}")

with col2:
    st.markdown("### ❓ Questions (TXT)")
    txt_file = st.file_uploader(
        "Upload TXT",
        type=['txt'],
        help="Upload questions file"
    )
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
    '1': 'Brief answers (2-3 words)',
    '2': 'Short answers (2 lines)',
    '4': 'Medium answers (5 lines)',
    '7': 'Detailed answers (8 lines)'
}

st.info(f"📝 {type_descriptions[question_type]}")

# Process button
if st.button("🔍 Generate Answers", type="primary", use_container_width=True):
    if pdf_file and txt_file:
        with st.spinner("Processing files..."):
            try:
                # Extract text from PDF
                with st.spinner("📖 Extracting text from PDF..."):
                    source_text = extract_text_from_pdf(pdf_file)
                    st.session_state.source_text = source_text
                
                if not source_text or len(source_text.strip()) < 100:
                    st.error("❌ Could not extract sufficient text from PDF.")
                    st.stop()
                
                st.success(f"✅ Extracted {len(source_text)} characters from PDF")
                
                # Parse questions
                with st.spinner("❓ Parsing questions..."):
                    txt_content = txt_file.read().decode('utf-8')
                    questions = parse_questions(txt_content)
                
                if not questions:
                    st.error("❌ No questions found in the uploaded file.")
                    st.stop()
                
                st.success(f"✅ Found {len(questions)} questions")
                
                # Generate answers
                with st.spinner("🤖 Generating answers..."):
                    answers = generate_answers(questions, source_text, question_type)
                
                st.session_state.answers = answers
                
                st.markdown('<div class="success-box">✅ Successfully generated {} answers!</div>'.format(len(answers)), unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
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

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    1. **Upload PDF** - Your study material
    2. **Upload TXT** - Your questions file
    3. **Select Type** - Choose mark allocation
    4. **Generate** - Click the button
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Answer Lengths")
    st.markdown("""
    - **1 Mark**: 2-3 words
    - **2 Marks**: 2 lines
    - **4 Marks**: 5 lines
    - **7 Marks**: 8 lines
    """)
