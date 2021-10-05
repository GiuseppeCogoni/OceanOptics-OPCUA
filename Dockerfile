FROM python:3.7

RUN addgroup --system --gid 1001 python\
    && adduser --system --home /home/python --shell /bin/sh --uid 1001 --gid 1001 python\
    && pip install PyYAML coloredlogs opcua cryptography numpy

USER python
RUN mkdir -p /home/python/opc-socket-relay
COPY --chown=python:python opc_ocean_optics.py opc_server.py\
     logger_conf.yml configuration.yml\
     /home/python/OceanOptics-OPCUA/
WORKDIR /home/python/OceanOptics-OPCUA

ENTRYPOINT ["python", "-m", "opc_ocean_optics"]
CMD ["--configuration_file", "configuration.yml"]