from connexion import App
import config

app = connexion_app = App(__name__)

app.add_api('schema.yml')

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=True)
