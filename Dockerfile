FROM python:3.8
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN apt-get update && apt-get install -y netcat
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
RUN chmod 744 /code/app/entrypoint.sh
ENTRYPOINT [ "/code/app/entrypoint.sh" ]