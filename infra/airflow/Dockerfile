FROM apache/airflow:2.10.3-python3.11

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

USER root
COPY pyproject.toml /opt/project/pyproject.toml
COPY src/ /opt/project/src/
RUN chown -R airflow: /opt/project
USER airflow

RUN pip install --no-cache-dir -e /opt/project
