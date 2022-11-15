FROM python:3.10-slim-bullseye AS runtime

COPY hieroglyphics-1.0.12.0 /opt/hieroglyphics-1.0.12.0

WORKDIR /opt/hieroglyphics-1.0.12.0

RUN apt-get update -y
RUN pip install -r requirements.txt
RUN pip install hieroglyphics-1.0.12-py3-none-any.whl

ENTRYPOINT [ "python" ]
CMD [ "-m", "hieroglyphics", "production" ]
