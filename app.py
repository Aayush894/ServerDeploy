from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle as pkl
import numpy as np
import logging
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Apply CORS settings globally to allow requests from any origin
CORS(app, origins=["*"])

# Load models
with open(r"Random_Forest_Model.sav", 'rb') as file:
    quiz_model = pkl.load(file)

def get_result(lang_vocab, memory, speed, visual, audio, survey):
    array = np.array([[lang_vocab, memory, speed, visual, audio, survey]])
    label = int(quiz_model.predict(array))
    if label == 0:
        output = "There is a high chance of the applicant to have dyslexia."
    elif label == 1:
        output = "There is a moderate chance of the applicant to have dyslexia."
    else:
        output = "There is a low chance of the applicant to have dyslexia."
    return output

@app.route("/") 
def home_view():
    return "<h1>Welcome to our server !!</h1>"

@app.route('/api/submitquiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json  
        extracted_object = data.get('quiz')
        time_value = data.get('time')

        lang_vocab = (extracted_object['q1'] + extracted_object['q2'] + extracted_object['q3'] + extracted_object['q4'] + extracted_object['q5'] + extracted_object['q6'] + extracted_object['q8'])/28
        memory = (extracted_object['q2']+ extracted_object['q9'])/8
        speed = 1 - (time_value / 60000)
        visual = (extracted_object['q1'] + extracted_object['q3'] + extracted_object['q4'] + extracted_object['q6'])/16
        audio = (extracted_object['q7']+extracted_object['q10'])/8
        survey = (lang_vocab + memory + speed + visual + audio)/80
        
        result = get_result(lang_vocab, memory, speed, visual, audio, survey)

        response = {
            "ok": True,
            "message": "Score Available",
            "result": result
        }
        return jsonify(response)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"ok": False, "message": "Internal Server Error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"An error occurred: {e}")
    return jsonify({"ok": False, "message": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run()
