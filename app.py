from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pickle as pkl
import numpy as np
from textblob import TextBlob
import language_tool_python
import requests
from abydos.phonetic import Soundex, Metaphone, Caverphone, NYSIIS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

quiz_model = None
with open(r"Random_Forest_Model.sav", 'rb') as file:
  quiz_model = pkl.load(file)


loaded_model = None
with open(r"Decision_tree_model.sav", 'rb') as file:
  loaded_model = pkl.load(file)

# code for test.py starts here 
# **********************
def levenshtein(s1, s2):
    # Initialize a matrix to store the Levenshtein distances
    matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]

    # Initialize the first row and column of the matrix
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    for j in range(len(s2) + 1):
        matrix[0][j] = j

    # Compute Levenshtein distance for each pair of substrings
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(matrix[i - 1][j] + 1,      # Deletion
                               matrix[i][j - 1] + 1,      # Insertion
                               matrix[i - 1][j - 1] + cost)  # Substitution

    # Return the Levenshtein distance between the last elements of s1 and s2
    return matrix[len(s1)][len(s2)]

# *****************
def spelling_accuracy(extracted_text):
  spell_corrected = TextBlob(extracted_text).correct()
  return ((len(extracted_text) - (levenshtein(extracted_text, spell_corrected)))/(len(extracted_text)+1))*100


# *****************
my_tool = language_tool_python.LanguageTool('en-US')

# *****************
def gramatical_accuracy(extracted_text):
  spell_corrected = TextBlob(extracted_text).correct()
  correct_text = my_tool.correct(spell_corrected)
  extracted_text_set = set(spell_corrected.split(" "))
  correct_text_set = set(correct_text.split(" "))
  n = max(len(extracted_text_set - correct_text_set),
          len(correct_text_set - extracted_text_set))
  return ((len(spell_corrected) - n)/(len(spell_corrected)+1))*100

# ******************

# text correction API authentication
api_key_textcorrection = os.getenv('api_key_textcorrection')
endpoint_textcorrection = "https://api.bing.microsoft.com/"


# ******************
def percentage_of_corrections(extracted_text):
  data = {'text': extracted_text}
  params = {
    'mkt': 'en-us',
    'mode': 'proof'
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Ocp-Apim-Subscription-Key': api_key_textcorrection,
  }
  response = requests.post(endpoint_textcorrection, headers=headers, params=params, data=data)
  json_response = response.json()
  flagged_tokens_count = len(json_response.get('flaggedTokens', []))
  extracted_word_count = len(extracted_text.split(" "))
  if extracted_word_count > 0:
    percentage_corrected = (flagged_tokens_count / extracted_word_count) * 100
  else:
    percentage_corrected = 0
  return percentage_corrected

# ******************
def percentage_of_phonetic_accuraccy(extracted_text: str):
  soundex = Soundex()
  metaphone = Metaphone()
  caverphone = Caverphone()
  nysiis = NYSIIS()
  spell_corrected = TextBlob(extracted_text).correct()

  extracted_text_list = extracted_text.split(" ")
  extracted_phonetics_soundex = [soundex.encode(string) for string in extracted_text_list]
  extracted_phonetics_metaphone = [metaphone.encode(string) for string in extracted_text_list]
  extracted_phonetics_caverphone = [caverphone.encode(string) for string in extracted_text_list]
  extracted_phonetics_nysiis = [nysiis.encode(string) for string in extracted_text_list]

  extracted_soundex_string = " ".join(extracted_phonetics_soundex)
  extracted_metaphone_string = " ".join(extracted_phonetics_metaphone)
  extracted_caverphone_string = " ".join(extracted_phonetics_caverphone)
  extracted_nysiis_string = " ".join(extracted_phonetics_nysiis)

  spell_corrected_list = spell_corrected.split(" ")
  spell_corrected_phonetics_soundex = [soundex.encode(string) for string in spell_corrected_list]
  spell_corrected_phonetics_metaphone = [metaphone.encode(string) for string in spell_corrected_list]
  spell_corrected_phonetics_caverphone = [caverphone.encode(string) for string in spell_corrected_list]
  spell_corrected_phonetics_nysiis = [nysiis.encode(string) for string in spell_corrected_list]

  spell_corrected_soundex_string = " ".join(spell_corrected_phonetics_soundex)
  spell_corrected_metaphone_string = " ".join(spell_corrected_phonetics_metaphone)
  spell_corrected_caverphone_string = " ".join(spell_corrected_phonetics_caverphone)
  spell_corrected_nysiis_string = " ".join(spell_corrected_phonetics_nysiis)

  soundex_score = (len(extracted_soundex_string)-(levenshtein(extracted_soundex_string,spell_corrected_soundex_string)))/(len(extracted_soundex_string)+1)
  # print(spell_corrected_soundex_string)
  # print(extracted_soundex_string)
  # print(soundex_score)
  metaphone_score = (len(extracted_metaphone_string)-(levenshtein(extracted_metaphone_string,spell_corrected_metaphone_string)))/(len(extracted_metaphone_string)+1)
  # print(metaphone_score)
  caverphone_score = (len(extracted_caverphone_string)-(levenshtein(extracted_caverphone_string,spell_corrected_caverphone_string)))/(len(extracted_caverphone_string)+1)
  # print(caverphone_score)
  nysiis_score = (len(extracted_nysiis_string)-(levenshtein(extracted_nysiis_string,spell_corrected_nysiis_string)))/(len(extracted_nysiis_string)+1)
  # print(nysiis_score)
  return ((0.5*caverphone_score + 0.2*soundex_score + 0.2*metaphone_score + 0.1 * nysiis_score))*100


# **********************
def calculate_score(extracted_phonetics, spell_corrected_phonetics):
    total_distance = sum(levenshtein(extracted, corrected) for extracted, corrected in zip(extracted_phonetics, spell_corrected_phonetics))
    return (1 - total_distance / len(extracted_phonetics)) if extracted_phonetics else 0


# **********************
def get_feature_array(extracted_text):
  # path is the path of image, but i am using text.
  feature_array = []

  # *******************************
  feature_array.append(spelling_accuracy(extracted_text))
  feature_array.append(gramatical_accuracy(extracted_text))
  feature_array.append(percentage_of_corrections(extracted_text))
  feature_array.append(percentage_of_phonetic_accuraccy(extracted_text))
  return feature_array


# **********************
@app.route('/api/submit_text', methods=['GET','POST'])
@cross_origin(origin='*')  # Allow requests from all origins
def submit_text():
    # text extracted will be here
    print(request)
    request_data = request.json  
    extracted_text = request_data.get('text')

    features = get_feature_array(extracted_text)
    features_array = np.array([features])
    prediction = loaded_model.predict(features_array)

    result = "" 

    if prediction[0] == 0:
        result = "There's a very slim chance that this person is suffering from dyslexia or dysgraphia."
    else:
        result = "There's a high chance that this person is suffering from dyslexia or dysgraphia"


    response = {
        "ok": True,
        "message": "Score Available",
        "result": result,
    }

    return jsonify(response)


# **********************
@app.route('/api/submit_quiz', methods=['GET','POST'])
@cross_origin(origin='*')  # Allow requests from all origins
def submit_quiz():
  data = request.json  
  extracted_object = data.get('quiz')
  time_value = data.get('time')

  lang_vocab = (extracted_object['q1'] + extracted_object['q2'] + extracted_object['q3'] + extracted_object['q4'] + extracted_object['q5'] + extracted_object['q6'] + extracted_object['q8'])/28
  memory = (extracted_object['q2']+ extracted_object['q9'])/8
  speed = 1 - (time_value / 60000) ; 
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

# **********************
def get_result(lang_vocab, memory, speed, visual, audio, survey):
  #2D numpy array created with the values input by the user.
  array = np.array([[lang_vocab, memory, speed, visual, audio, survey]])
  #The output given by model is converted into an int and stored in label.
  label = int(quiz_model.predict(array))
  #Giving final output to user depending upon the model prediction.
  if(label == 0):
    output = "There is a high chance of the applicant to have dyslexia."
  elif(label == 1):
    output = "There is a moderate chance of the applicant to have dyslexia."
  else:
    output = "There is a low chance of the applicant to have dyslexia."
  return output

# **********************
if __name__ == '__main__':
  port = int(os.getenv('PORT', 8000))
  print(f"server is running on port {port}")
  app.run(debug=True, port=port, host='0.0.0.0')
