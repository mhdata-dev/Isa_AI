FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements.lock.txt \
 && useradd --uid 10001 --create-home isa \
 && mkdir /session && chown isa:isa /session
COPY *.py ./
COPY tests ./tests
USER isa
EXPOSE 8000
CMD ["python", "collector.py"]
