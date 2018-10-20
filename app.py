from connexion import App

app = connexion_app = App(__name__)

app.add_api('schema.yml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
