import re
from config import Config

def generate_answers(questions, source_text, question_type):
    """
    Generate answers based on question type and source text
    """
    answers = []
    config = Config.ANSWER_CONFIG.get(question_type, Config.ANSWER_CONFIG['1'])
    
    for idx, question in enumerate(questions):
        answer = find_best_answer(question, source_text, config)
        
        answers.append({
            'id': f'q_{idx + 1}',
            'question': question,
            'answer': answer['text'],
            'word_count': answer['word_count'],
            'line_count': answer['line_count'],
            'confidence': answer['confidence'],
            'source_location': answer['source_location']
        })
    
    return answers

def find_best_answer(question, source_text, config):
    """
    Find the best answer in source text based on question
    """
    # Extract keywords from question
    keywords = extract_keywords(question)
    
    # Search for keywords in source text
    best_match = None
    best_score = 0
    
    # Split source into sentences/paragraphs
    paragraphs = re.split(r'\n\s*\n', source_text)
    sentences = re.split(r'[.!?]+', source_text)
    
    # Search in paragraphs first
    for para in paragraphs:
        if len(para.strip()) < 20:
            continue
        
        score = calculate_relevance(para, keywords)
        if score > best_score:
            best_score = score
            best_match = para.strip()
    
    # If no good paragraph match, try sentences
    if best_score < 0.3:
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
            
            score = calculate_relevance(sentence, keywords)
            if score > best_score:
                best_score = score
                best_match = sentence.strip()
    
    # Format answer based on question type
    if best_match:
        formatted_answer = format_answer(best_match, config)
        word_count = len(formatted_answer.split())
        line_count = len(formatted_answer.split('\n'))
        
        return {
            'text': formatted_answer,
            'word_count': word_count,
            'line_count': line_count,
            'confidence': min(best_score, 1.0),
            'source_location': 'Found in source material'
        }
    
    # Fallback
    return {
        'text': "Answer not found in the provided source material. Please check your PDF content.",
        'word_count': 0,
        'line_count': 1,
        'confidence': 0.0,
        'source_location': 'Not found'
    }

def extract_keywords(question):
    """
    Extract important keywords from question
    """
    # Remove common words
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'how', 'why', 'when', 'where', 'which',
                  'who', 'whom', 'whose', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
    
    words = question.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

def calculate_relevance(text, keywords):
    """
    Calculate relevance score between text and keywords
    """
    if not keywords:
        return 0
    
    text_lower = text.lower()
    matches = sum(1 for keyword in keywords if keyword in text_lower)
    
    # Base score on keyword matches
    score = matches / len(keywords)
    
    # Bonus for exact phrase matches
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            score += 0.1
    
    return min(score, 1.0)

def format_answer(text, config):
    """
    Format answer according to mark allocation
    """
    # Split into words
    words = text.split()
    
    # Limit by word count
    if config['max_words'] and len(words) > config['max_words']:
        words = words[:config['max_words']]
    
    # Join and limit by lines
    answer = ' '.join(words)
    
    if config['max_lines']:
        lines = answer.split('\n')
        if len(lines) > config['max_lines']:
            lines = lines[:config['max_lines']]
            answer = '\n'.join(lines)
    
    return answer.strip()
