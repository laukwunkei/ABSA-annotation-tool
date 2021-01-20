#flask packages
from flask import Flask, render_template, request, session, redirect, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap 
from flask_uploads import UploadSet,configure_uploads,IMAGES,DATA,ALL

#systems
import os 
import sys
import json
from werkzeug.utils import secure_filename
import spacy

app = Flask(__name__)
Bootstrap(app)
app.config['UPLOAD_PATH'] = 'uploads'
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'
ALLOWED_EXTENSIONS = set(['txt', 'json'])

# Spacy packages and dependancy algorithms
nlp = spacy.load("en_core_web_sm")
from static.dependancy import apply_extraction

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def count_uploadfile(dir):
    list = os.listdir(dir) # dir is your directory path
    number_files = len(list)
    return number_files

def findtxtfile(dir):
    for file in os.listdir(dir):
        if file.endswith(".txt"):
            return file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_data', methods=['POST'])
def upload_data():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'data' not in request.files:
            flash('No file part')
        file = request.files['data']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename_data = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_PATH'], filename_data))
            flash('File ({}) successfully uploaded'.format(filename_data))
        return redirect('/')

@app.route('/upload_output', methods=['POST'])
def upload_output():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'output' not in request.files:
            flash('No file part')
        file = request.files['output']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename_output = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_PATH'], filename_output))
            flash('File ({}) successfully uploaded'.format(filename_output))
        return redirect('/')

@app.route('/start_annotation', methods=['POST','GET'])
def start_annotation():
    # Going back to index page and flash warning
    if count_uploadfile('uploads') == 0:
        flash('Please upload data file before annotation')
        return redirect('/')
    # find file end with txt and Store filename 
    num_sentences = 0
    filename = findtxtfile('uploads')
    text_file = open(os.path.join('uploads', filename), "r").read()
    nlp_file_doc = nlp(text_file)
    all_sentences = list(nlp_file_doc.sents)
    list_size = len(all_sentences)
    session["list_size"] = list_size
    first_sentence = all_sentences[0].text

    if count_uploadfile('uploads') == 2:
        with open('uploads/output.json', 'r') as myfile:
            data=myfile.read()
        data = json.loads(data)
        num_sentences = len(data)
        session["num_sentences"] = num_sentences
        all_sentences = all_sentences[num_sentences:]
        first_sentence = all_sentences[0].text
        data[first_sentence] = []
        with open('uploads/output.json', 'w') as f:
            f.write(json.dumps(data))
        
    if count_uploadfile('uploads') == 1:
        session["num_sentences"] = num_sentences
        data = {first_sentence:[]}
        with open("uploads/output.json", "w") as write_file:
            json.dump(data, write_file)

    #Test out the first sentence
    extraction = apply_extraction(first_sentence, nlp)
    return render_template('annotation.html', 
                            all_sentences = all_sentences, 
                            extraction = extraction, num_sentences = num_sentences, list_size = list_size)
    
        
@app.route('/add_auto', methods=['POST','GET'])
def add_auto():
    if request.method == 'POST':
        auto_dependency = request.form['auto_dependency']
        auto_polarity = request.form['auto_polarity']
        with open('uploads/output.json', 'r') as myfile:
            data=myfile.read()
        data = json.loads(data)
        #update output files with new dependency
        pair = {auto_dependency: auto_polarity}
        last_sentence = list(data.keys())[-1]
        data[last_sentence].append(pair)
        with open("uploads/output.json", "w") as write_file:
            json.dump(data, write_file)
        return ('', 204)

@app.route('/add_manual', methods=['POST','GET'])
def add_manual():
    if request.method == 'POST':
        manual_aspect_term = request.form['manual_aspect_term']
        manual_polarity_term = request.form['manual_polarity_term']
        manual_polarity = request.form['manual_polarity']
        with open('uploads/output.json', 'r') as myfile:
            data=myfile.read()
        data = json.loads(data)
        #update output files with new dependency
        dependacy = "({}, {})".format(manual_aspect_term, manual_polarity_term)
        pair = {dependacy: manual_polarity}
        last_sentence = list(data.keys())[-1]
        data[last_sentence].append(pair)
        with open("uploads/output.json", "w") as write_file:
            json.dump(data, write_file)
        return ('', 204)

@app.route('/next', methods=['POST','GET'])
def next():
    # Retrieve file name and update num of edited sentence
    filename = findtxtfile('uploads')
    num_sentences = int(session.get("num_sentences", None))
    list_size = int(session.get("list_size", None))
    #When you have finished with editing
    num_sentences += 1
    print("num size is {} list_s is {}".format(num_sentences, list_size))
    if (num_sentences == list_size):
        flash("You have done with {} annotation! congratulations!".format(filename))
        return render_template('success.html')
    session["num_sentences"] = num_sentences

    # Update output with next sentence
    text_file = open(os.path.join('uploads',filename), "r").read()
    nlp_file_doc = nlp(text_file)
    all_sentences = list(nlp_file_doc.sents)
    all_sentences = all_sentences[num_sentences:]
    first_sentence = all_sentences[0].text

    with open('uploads/output.json', 'r') as f:
        json_data = json.load(f)
        json_data[first_sentence] = []

    with open('uploads/output.json', 'w') as f:
        f.write(json.dumps(json_data))

    extraction = apply_extraction(first_sentence, nlp)
    return (render_template('annotation.html', 
                                num_sentences = num_sentences, 
                                extraction = extraction, all_sentences = all_sentences, list_size = list_size))

@app.route('/exit', methods=['POST','GET'])
def exit():
    return render_template('success.html')

@app.route('/download', methods=['POST','GET'])
def download():
    path = "uploads/output.json"
    return send_file(path, as_attachment=True)

@app.route('/restart', methods=['POST','GET'])
def restart():
    # Clear all uploads and outputs
    print(len(os.listdir('uploads')))
    if (len(os.listdir('uploads'))!=0):
        for filename in os.listdir('uploads'):
            os.remove(os.path.join(app.config['UPLOAD_PATH'], filename))
    return render_template('index.html')

if __name__ == '__main__': 
    app.run(debug=True)

