FROM python:3.13-slim-bullseye AS runtime

ARG APP_VERSION
ARG RELEASE_VERSION

COPY hieroglyphics-${RELEASE_VERSION} /opt/hieroglyphics

WORKDIR /opt/hieroglyphics

RUN apt-get update -y
RUN pip install hieroglyphics-${APP_VERSION}-py3-none-any.whl

ENTRYPOINT [ "python" ]
CMD [ "-m", "hieroglyphics", "production" ]
