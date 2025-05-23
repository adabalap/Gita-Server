export GEMINI_API_KEY="AIzaSyAnp0lHEZnajMbDavNPrrTUhSGareRwFp0"
gunicorn --bind 0.0.0.0:5000 --certfile cert.pem --keyfile key.pem app:app >> app.log 2>&1 &
#gunicorn --bind 0.0.0.0:5000 app:app 
