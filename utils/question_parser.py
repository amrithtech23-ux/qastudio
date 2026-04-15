import re

def parse_questions(txt_path):
    """
    Parse questions from text file
    Supports multiple formats:
    - Numbered: 1. Question text
    - Bullet: - Question text
    - Plain: Question text (one per line)
    """
    questions = []
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Split by common question separators
        patterns = [
            r'\d+\.\s+(.+?)(?=\n\d+\.|\Z)',  # 1. Question
            r'-\s+(.+?)(?=\n-|\Z)',           # - Question
            r'Q\d+[:\s]+(.+?)(?=\nQ\d+|\Z)', # Q1: Question
        ]
        
        questions = []
        
        # Try numbered format first
        numbered = re.findall(r'\d+\.\s+(.+)', content)
        if numbered:
            questions = [q.strip() for q in numbered if q.strip()]
        
        # Try bullet format
        if not questions:
            bulleted = re.findall(r'-\s+(.+)', content)
            if bulleted:
                questions = [q.strip() for q in bulleted if q.strip()]
        
        # Try Q format
        if not questions:
            q_format = re.findall(r'Q\d+[:\s]+(.+)', content)
            if q_format:
                questions = [q.strip() for q in q_format if q.strip()]
        
        # If no pattern matched, split by lines
        if not questions:
            lines = content.split('\n')
            questions = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
        
        # Remove duplicates and empty questions
        questions = list(dict.fromkeys(questions))
        questions = [q for q in questions if len(q) > 5]
        
        return questions
        
    except Exception as e:
        print(f"Question parsing failed: {e}")
        return []

def parse_questions_with_metadata(txt_path):
    """
    Parse questions with additional metadata
    """
    questions = []
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        current_question = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new question
            if re.match(r'^\d+\.', line) or re.match(r'^Q\d+', line, re.IGNORECASE):
                if current_question:
                    questions.append(current_question)
                current_question = line
            else:
                current_question += " " + line
        
        if current_question:
            questions.append(current_question)
        
        return [q.strip() for q in questions if q.strip()]
        
    except Exception as e:
        print(f"Metadata parsing failed: {e}")
        return []
