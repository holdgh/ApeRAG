FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

RUN apt update && \
    apt install --no-install-recommends -y build-essential

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt && pip cache purge

COPY . /app

WORKDIR /app

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
