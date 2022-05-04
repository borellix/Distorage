from app.main import app

if __name__ == '__main__':
    import os
    app.run(debug=os.environ.get('DEBUG', False) == 'true')
