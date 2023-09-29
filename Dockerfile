FROM python:3.11-slim as build

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN pip install --no-cache-dir --upgrade pip setuptools build wheel

COPY . /galactory

RUN pip install ./galactory


FROM python:3.11-slim as final

LABEL org.opencontainers.image.title="galactory"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
LABEL org.opencontainers.image.description="galactory: Ansible Galaxy proxy using Artifactory as a backend."

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

ENTRYPOINT [ "python", "-m", "galactory" ]
