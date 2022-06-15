import json
import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, session, render_template, flash
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY=os.environ.get('SECRET_KEY', 'development key')
))

strings = {
    
    "Gender": ["Female", "Male"],
    
}

# min, max, default value
floats = {
    "Weight": [10, 110, 50],
    "TSH": [1,100, 1],
    "Cholestrol": [80, 300, 125],
    "Hb": [1, 20, 14]
}

# min, max, default value
ints = {
    "Age": [10, 100, 45],
    "BP_Upper": [50, 300, 122],
    "BP_Lower": [10,200, 85],
    "Glucose_Fasting": [50, 300, 80],
    "Glucose_PP": [50, 600,120 ]
}

health_status = ["Unhealthy", "Healthy"]


def generate_input_lines():
    result = f'<table>'

    counter = 0
    for k in floats.keys():
        minn, maxx, vall = floats[k]
        if (counter % 2 == 0):
            result += f'<tr>'
        result += f'<td>{k}'
        result += f'<input type="number" class="form-control" min="{minn}" max="{maxx}" step="1" name="{k}" id="{k}" value="{vall}" required (this.value)">'
        result += f'</td>'
        if (counter % 2 == 1):
            result +=f'</tr>'
        counter = counter + 1

    counter = 0
    for k in ints.keys():
        minn, maxx, vall = ints[k]
        if (counter % 2 == 0):
            result += f'<tr>'
        result += f'<td>{k}'
        result += f'<input type="number" class="form-control" min="{minn}" max="{maxx}" step="1" name="{k}" id="{k}" value="{vall}" required (this.value)">'
        result += f'</td>'
        if (counter % 2 == 1):
            result += f'</tr>'
        counter = counter + 1

    counter = 0
    for k in strings.keys():
        if (counter % 2 == 0):
            result += f'<tr>'
        result += f'<td>{k}'
        result += f'<select class="form-control" name="{k}">'
        for value in strings[k]:
            result += f'<option value="{value}" selected>{value}</option>'
        result += f'</select>'
        result += f'</td>'
        if (counter % 2 == 1):
            result += f'</tr>'
        counter = counter + 1

    result += f'</table>'

    return result


app.jinja_env.globals.update(generate_input_lines=generate_input_lines)


def get_token():
    auth_token = os.environ.get('AUTH_TOKEN')
    api_token = os.environ.get("API_TOKEN")
    token_request_url = os.environ.get("TOKEN_REQUEST_URL")

    if (auth_token):
        # All three are set. bad bad!
        if (api_token and auth_token):
            raise EnvironmentError('[ENV VARIABLES] please set either "AUTH_TOKEN" or "API_TOKEN". Not both.')
        # Only TOKEN is set. good.
        else:
            return auth_token
    else:
        # Nothing is set. bad!
        if not (api_token and token_request_url):
            raise EnvironmentError('[ENV VARIABLES] Please set "API_TOKEN" as "AUTH_TOKEN" is not set.')
        # Only USERNAME, PASSWORD are set. good.
        else:
            token_response = requests.post(token_request_url, data={"apikey": api_token, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
            if token_response.status_code == 200:
                return token_response.json()["access_token"]
            else:
                raise Exception(f"Authentication returned {token_response.status_code}: {token_response.text}")


class riskForm():

    @app.route('/', methods=['GET', 'POST'])
    def index():
        

        if request.method == 'POST':
            ID = 999

            session['ID'] = ID
            data = {}

            for k, v in request.form.items():
                data[k] = v
                session[k] = v

            scoring_href = os.environ.get('MODEL_URL')

            if not (scoring_href):
                raise EnvironmentError('[ENV VARIABLES] Please set "URL".')

            for field in ints.keys():
                data[field] = int(data[field])
            for field in floats.keys():
                data[field] = float(data[field])

            input_data = list(data.keys())
            input_values = list(data.values())

            # Inject fields into payload to match model input schema
            extra_fields = os.environ.get('EXTRA_FIELDS').split(',')
            #print(extra_fields)
            i = 0
            for f in extra_fields:
                if f:
                    input_data.insert(i, f)
                    input_values.insert(i, None)
                    i += 1

            payload_scoring = {"input_data": [
                {"fields": input_data, "values": [input_values]}
            ]}
            # print("Payload is: ")
            # print(payload_scoring)
        
            header_online = {
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + get_token()
            }
            response_scoring = requests.post(
                scoring_href,
                verify=True,
                json=payload_scoring,
                headers=header_online)
            result = response_scoring.text
            # print("Result is ", result)
            result_json = json.loads(result)
          
            result_keys = result_json['predictions'][0]['fields']
            result_vals = result_json['predictions'][0]['values']
        
            result_dict = dict(zip(result_keys, result_vals[0]))
        
           
                
            health_risk = ''
            # if "predictedLabel" in result_dict:
            #     health_risk = result_dict["predictedLabel"]
            if "health_status" in result_dict:
                health_risk = result_dict["health_status"]
                if health_risk=="Unhealthy":
                    health_status_risk = float(result_dict["Probability"])* 100
                    # healthy_percent=100-unhealthy_percent
                    health_risk_percent="{:.2f}".format(health_status_risk)
                
                elif health_risk=="Healthy":  
                    healthy_percent = float(result_dict["Probability"])* 100
                    health_status_risk=100-healthy_percent
                    health_risk_percent="{:.2f}".format(health_status_risk)
                #     flash('Percentage of this health representing risk is: %.2f%%'
                # % health_risk_percent)
            
            return render_template(
                'results.html', 
                status=health_risk,
                health_risk_percent=health_risk_percent)
                
        else:
            return render_template('input.html')


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
port = os.environ.get('PORT', '5000')
host = os.environ.get('HOST', '0.0.0.0')
if __name__ == "__main__":
    app.run(host=host, port=int(port))
