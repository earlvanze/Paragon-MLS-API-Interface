import multiprocessing
from main import app

workers = multiprocessing.cpu_count() * 2 + 1

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)