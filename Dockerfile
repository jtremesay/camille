FROM python:3.13
WORKDIR /opt/camille
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-install-project
COPY camille.py ./
RUN uv sync
CMD [ ".venv/bin/camille" ]