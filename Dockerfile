FROM python:3.9.6-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python3", "./main.py"]
