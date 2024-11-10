from flask import Flask, jsonify
from vercel import Vercel

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello from Vercel!'

# Vercel handler
if __name__ == '__main__':
    app.run(debug=True)
