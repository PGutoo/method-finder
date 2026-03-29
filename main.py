import json
import ast

from flask import Flask, request, render_template
from service.openrouter_service import open_router

app = Flask(__name__)

@app.route('/openrouter', methods=['POST'])
def open_router_test():
    try:
        response = open_router(request.json['prompt'])
        # response = json.loads(response)
        # response = ast.literal_eval(response)

        return response
    except Exception as e:
        print(e)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
