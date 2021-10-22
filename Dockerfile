FROM python:3.7

RUN apt-get update && apt-get install git-all build-essential libusb-dev -y

RUN addgroup --system --gid 1000 python
RUN adduser --system --home /home/python --shell /bin/sh --uid 1000 --gid 1000 python
RUN usermod -aG dialout python

RUN pip install --upgrade pip
RUN pip install PyYAML coloredlogs opcua cryptography==3.3.2 seabreeze

USER python

RUN mkdir -p /home/python/OceanOptics-OPCUA
RUN mkdir -p /home/python/OceanOptics-OPCUA/configs
RUN mkdir -p /home/python/OceanOptics-OPCUA/logs

COPY --chown=python:python ./opc_server.py /home/python/OceanOptics-OPCUA/
ADD ./configs /home/python/OceanOptics-OPCUA/configs

CMD ["seabreeze_os_setup"]

WORKDIR /home/python/OceanOptics-OPCUA
ENTRYPOINT ["python", "-m", "opc_server"]
