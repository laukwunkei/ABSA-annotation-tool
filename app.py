# Flask packages
from flask import Flask, render_template, request, session, redirect, flash, send_file
from flask_bootstrap import Bootstrap 
from flask_uploads import UploadSet,configure_uploads,IMAGES,DATA,ALL

# Systems
import os 
import sys
import json
from werkzeug.utils import secure_filename
import spacy

# Flask app settings
app = Flask(__name__)
Bootstrap(app)
app.config['UPLOAD_data'] = 'data'
app.config['UPLOAD_output'] = 'output'
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'
ALLOWED_EXTENSIONS = set(['txt', 'json'])

# Spacy packages and dependancy algorithms
nlp = spacy.load("en_core_web_sm")
from static.dependancy import apply_extraction

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def count_uploadfile(dir):
    list = os.listdir(dir) 
    number_files = len(list)
    return number_files

def findfilebyformat(dir, format):
    for file in os.listdir(dir):
        if file.endswith(format):
            return file

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

def deleteDir(dirPath):
    deleteFiles = []
    deleteDirs = []
    for root, dirs, files in os.walk(dirPath):
        for f in files:
            deleteFiles.append(os.path.join(root, f))
        for d in dirs:
            deleteDirs.append(os.path.join(root, d))
    for f in deleteFiles:
        os.remove(f)
    for d in deleteDirs:
        os.rmdir(d)
    os.rmdir(dirPath)

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
            session['filename_data'] = filename_data
            # Create a file under data -> filename as datasetname
            foldername = filename_data.split('.tx')[0]
            path = './data/' + foldername +  '/'
            # Flash error: File exists already
            if os.path.exists(path):
                flash("Dataset {} has already exist. Rename your file to procceed.".format(foldername))
                return redirect('/')
            session['foldername'] = foldername
            path = './data/' + foldername +  '/'
            session['folderpath'] = path 
            createFolder(path)
            file.save('data/' + foldername + '/' + filename_data)
            flash('File ({}) successfully uploaded'.format(filename_data))
            return redirect('/')
        else:
            flash("You should upload valid file")
            return redirect('/')

@app.route('/upload_output', methods=['POST'])
def upload_output():
    if request.method == 'POST':
        foldername = request.form['dataset']
        path = 'data/' + foldername + '/'
        if not os.path.exists(path):
            flash('Database "{}" not found'.format(foldername))
            return redirect('/')
        session['folderpath'] = path
        session['filename_data'] = foldername + '.txt'
        flash('Your previous annotation {} is found'.format(foldername))
        return redirect('/')

@app.route('/start_annotation', methods=['POST','GET'])
def start_annotation():
    # Retrieving current annotation foldername 
    folderpath = session.get("folderpath", None)
    print("path is {}".format(folderpath))
    # Going back to index page and flash warning
    if folderpath == None:
        flash('Please upload data file before annotation')
        return redirect('/')

    # Existing annotation
    if count_uploadfile(folderpath) == 2:
        filename = findfilebyformat(folderpath, '.txt')
        text_file = open(folderpath + filename, "r").read()
        nlp_file_doc = nlp(text_file)
        all_sentences = list(nlp_file_doc.sents)
        list_size = len(all_sentences)
        session["list_size"] = list_size
        output_file = findfilebyformat(folderpath, '.json')
        output_path = folderpath + output_file
        session['output_path'] = output_path
        with open(output_path, 'r') as myfile:
            data=myfile.read()
        data = json.loads(data)
        num_sentences = len(data)
        # When you have finished annotation
        if num_sentences == list_size:
            flash("You have done with annotation for {}.".format(filename))
            return render_template('index.html')
        session["num_sentences"] = num_sentences
        all_sentences = all_sentences[num_sentences:]
        first_sentence = all_sentences[0].text
        data[first_sentence] = []
        with open(output_path, 'w') as f:
            f.write(json.dumps(data))

    # New annotation
    if count_uploadfile(folderpath) == 1:
        num_sentences = 0
        filename = session.get("filename_data", None)
        text_file = open((folderpath + filename), "r").read()
        nlp_file_doc = nlp(text_file)
        all_sentences = list(nlp_file_doc.sents)
        list_size = len(all_sentences)
        session["list_size"] = list_size
        first_sentence = all_sentences[0].text
        session["num_sentences"] = num_sentences
        data = {first_sentence:[]}
        output_path = folderpath + filename.split('.tx')[0] + "_output.json"
        session['output_path'] = output_path
        with open(output_path, "w") as write_file:
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
        output_path = session.get("output_path", None)
        with open(output_path, 'r') as myfile:
            data=myfile.read()
        data = json.loads(data)
        #update output files with new dependency
        pair = {auto_dependency: auto_polarity}
        last_sentence = list(data.keys())[-1]
        data[last_sentence].append(pair)
        with open(output_path, "w") as write_file:
            json.dump(data, write_file)
        return ('', 204)

@app.route('/add_manual', methods=['POST','GET'])
def add_manual():
    if request.method == 'POST':
        manual_aspect_term = request.form['manual_aspect_term']
        manual_polarity_term = request.form['manual_polarity_term']
        manual_polarity = request.form['manual_polarity']
        output_path = session.get("output_path", None)
        with open(output_path, 'r') as myfile:
            data=myfile.read()
        data = json.loads(data)
        #update output files with new dependency
        dependacy = "({}, {})".format(manual_aspect_term, manual_polarity_term)
        pair = {dependacy: manual_polarity}
        last_sentence = list(data.keys())[-1]
        data[last_sentence].append(pair)
        with open(output_path, "w") as write_file:
            json.dump(data, write_file)
        return ('', 204)

@app.route('/next', methods=['POST','GET'])
def next():
    # Retrieve file name and update num of edited sentence
    dataname = session.get("filename_data", None)
    foldername = session.get("folderpath")
    num_sentences = int(session.get("num_sentences", None))
    list_size = int(session.get("list_size", None))
    #When you have finished with editing
    num_sentences += 1
    print("num size is {} list_s is {}".format(num_sentences, list_size))
    if (num_sentences == list_size):
        flash("You have done with {} annotation! congratulations!".format(dataname))
        return render_template('success.html')
    session["num_sentences"] = num_sentences

    # Update output with next sentence
    text_file = open(foldername + dataname, "r").read()
    nlp_file_doc = nlp(text_file)
    all_sentences = list(nlp_file_doc.sents)
    all_sentences = all_sentences[num_sentences:]
    first_sentence = all_sentences[0].text

    output_path = session.get("output_path", None)
    with open(output_path, 'r') as f:
        json_data = json.load(f)
        json_data[first_sentence] = []

    with open(output_path, 'w') as f:
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
    output_path = session.get("output_path", None)
    return send_file(output_path, as_attachment=True)

@app.route('/restart', methods=['POST','GET'])
def restart():
    session.clear()
    return render_template('index.html')

@app.route('/clear', methods=['POST','GET'])
def clear():
    folderpath = session.get("folderpath", None)
    deleteDir(folderpath)
    return render_template('index.html')

if __name__ == '__main__': 
    app.run(debug=True, threaded=True)

