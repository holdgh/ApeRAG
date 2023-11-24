FROM curlimages/curl:8.4.0 AS downloader

RUN curl -sL http://kubeblocks.oss-cn-hangzhou.aliyuncs.com/dlptool  -o /tmp/dlptool


FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

RUN apt update && \
    apt install --no-install-recommends -y build-essential

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt && pip cache purge

COPY . /app

COPY --from=builder /tmp/dlptool /bin/dlptool

WORKDIR /app

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
