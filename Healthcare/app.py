from flask import Flask , render_template , request
import pickle
from flask_cors import CORS , cross_origin

app = Flask(__name__)
CORS(app)

@app.route('/',methods=['GET'])
@cross_origin()

def homePage():
    return render_template("index.html")

@app.route('/predict' , methods=['POST'])
def index():
    if request.method == "POST":
        weight = float(request.form['weight'])
        age = float(request.form['age'])
        BP_Upper = float(request.form['BP_Upper'])
        BP_Lower = float(request.form['BP_Lower'])
        TSH = float(request.form['TSH'])
        Glucose_Fasting = float(request.form['Glucose_Fasting'])
        Glucose_PP = float(request.form['Glucose_PP'])
        Cholestrol = float(request.form['Cholestrol'])
        Hb = float(request.form['Hb'])
        gender = request.form['gender']
        if(gender == 'Male'):
            gender = 0
        else:
            gender = 1
        sc_file = 'healthcare_scalar.pickle'
        model_file = 'healthcare_model.pickle'
        sc_model = pickle.load(open(sc_file, "rb"))
        model = pickle.load(open(model_file, "rb"))
        input_arr = sc_model.transform([[weight,age,BP_Upper,BP_Lower,TSH,Glucose_Fasting,Glucose_PP,Cholestrol,Hb,gender]])
        prediction = model.predict(input_arr)[0]
        if prediction == 1:
            health_condition = 'Oops! Sorry you are Unhealthy :('
        else:
            health_condition = 'Congratulations. You are prefectly Healthy!!'
        return render_template('results.html', status = health_condition)

if __name__ == "__main__" :
    app.run()