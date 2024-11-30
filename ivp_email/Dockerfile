FROM python:3.11

WORKDIR /

COPY ./requirements.txt /requirements.txt
RUN apt-get update 
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /requirements.txt


COPY ./ /

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]