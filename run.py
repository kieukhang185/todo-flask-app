from dotenv import load_dotenv
from app import create_app

load_dotenv()  # loads variables from .env into environment
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
