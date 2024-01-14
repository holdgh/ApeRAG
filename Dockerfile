FROM curlimages/curl:8.4.0 AS downloader

RUN curl -sL http://kubeblocks.oss-cn-hangzhou.aliyuncs.com/dlptool  -o /tmp/dlptool


FROM python:3.11.1-slim

RUN apt update && \
    apt install --no-install-recommends -y build-essential

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt && pip cache purge

COPY . /app

COPY --from=downloader /tmp/dlptool /bin/dlptool

RUN chmod +x /bin/dlptool

WORKDIR /app

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
