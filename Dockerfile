FROM python:3.7

RUN apt-get update && apt-get install git-all build-essential libusb-dev -y
RUN addgroup --system --gid 1001 python
RUN adduser --system --home /home/python --shell /bin/sh --uid 1001 --gid 1001 python
RUN usermod -a -G dialout python
RUN pip install PyYAML coloredlogs opcua cryptography==3.3.2 seabreeze

USER python
RUN mkdir -p /home/python/OceanOptics-OPCUA
RUN mkdir -p /home/python/OceanOptics-OPCUA/configs
RUN mkdir -p /home/python/OceanOptics-OPCUA/logs
COPY --chown=python:python ./opc_server.py\
     ./configs/logger_conf.yml\
     ./configs/config.yml\
     ./configs/instrument_config.yml\
     /home/python/OceanOptics-OPCUA/
CMD ["seabreeze_os_setup"]
WORKDIR /home/python/OceanOptics-OPCUA

ENTRYPOINT ["python", "-m", "opc_server"]
