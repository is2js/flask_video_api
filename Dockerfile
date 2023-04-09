FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5005
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5005", "manage:app"]