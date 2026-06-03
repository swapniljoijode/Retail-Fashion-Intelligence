FROM apache/airflow:2.9.3-python3.11

USER root
# git is needed for dbt deps to clone package repositories
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install project and orchestration dependencies.
# The --user flag places packages in ~/.local which the Airflow
# entrypoint adds to PATH automatically.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt
