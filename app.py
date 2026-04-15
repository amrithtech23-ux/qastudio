from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
from config import Config
from utils.pdf_extractor import extract_text_from_pdf
from utils.question_parser import parse_questions
from utils.answer_generator import generate_answers
from utils.export_utils import export_to_pdf, export_to_html
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Ensure directories exist
def create_directories():
    dirs = [
        app.config['UPLOAD_FOLDER'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'questions'),
        app.config['EXPORT_FOLDER'],
        os.path.join(app.config['EXPORT_FOLDER'], 'pdf'),
        os.path.join(app.config['EXPORT_FOLDER'], 'html')
    ]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

create_directories()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files():
    try:
        if 'source_pdf' not in request.files or 'questions_txt' not in request.files:
            return jsonify({'error': 'Both PDF and TXT files are required'}), 400
        
        pdf_file = request.files['source_pdf']
        question_file = request.files['questions_txt']
        question_type = request.form.get('question_type')
        
        if pdf_file.filename == '' or question_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(pdf_file.filename) or not allowed_file(question_file.filename):
            return jsonify({'error': 'Invalid file type. Use PDF and TXT files only'}), 400
        
        # Generate unique session folder
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        # Save files
        pdf_filename = secure_filename(f"{session_id}_source.pdf")
        txt_filename = secure_filename(f"{session_id}_questions.txt")
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', pdf_filename)
        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], 'questions', txt_filename)
        
        pdf_file.save(pdf_path)
        question_file.save(txt_path)
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Parse questions
        questions = parse_questions(txt_path)
        
        if not questions:
            return jsonify({'error': 'No questions found in the uploaded file'}), 400
        
        # Generate answers
        answers = generate_answers(questions, pdf_text, question_type)
        
        # Store in session for export
        session['answers'] = answers
        session['question_type'] = question_type
        
        return jsonify({
            'success': True,
            'answers': answers,
            'question_type': question_type,
            'question_count': len(questions)
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/export', methods=['POST'])
def export_answers():
    try:
        data = request.json
        export_format = data.get('format')
        
        answers = session.get('answers', [])
        question_type = session.get('question_type', '1')
        
        if not answers:
            return jsonify({'error': 'No answers to export. Process files first.'}), 400
        
        if export_format not in ['pdf', 'html']:
            return jsonify({'error': 'Invalid export format'}), 400
        
        # Generate export file
        session_id = session.get('session_id', 'default')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == 'pdf':
            filename = f"QA_Studio_Answers_{timestamp}.pdf"
            filepath = export_to_pdf(answers, question_type, filename)
            return send_file(filepath, as_attachment=True, download_name=filename)
        else:
            filename = f"QA_Studio_Answers_{timestamp}.html"
            filepath = export_to_html(answers, question_type, filename)
            return send_file(filepath, as_attachment=True, download_name=filename)
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/preview/<question_id>')
def get_question_preview(question_id):
    answers = session.get('answers', [])
    for answer in answers:
        if answer.get('id') == question_id:
            return jsonify(answer)
    return jsonify({'error': 'Question not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
