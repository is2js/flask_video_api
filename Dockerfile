FROM python:3.9
COPY . /app
WORKDIR /app
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt --root-user-action=ignore
EXPOSE 5005
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5005", "manage:app"]