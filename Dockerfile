FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# install dependencies
# TODO: is `update-ca-certificates` really necessary?
RUN apt-get update && \
    apt-get install --no-install-recommends --yes ca-certificates-java curl \
      unzip wget bzip2 libgoogle-glog-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    update-ca-certificates -f

# install micromamba
RUN mkdir -p /software/micromamba && \
    cd /software/micromamba && \
    wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/0.15.2 | tar -xvj bin/micromamba
ENV PATH="/software/micromamba/bin:${PATH}"

# create conda/mamba environment
COPY ./environment.yaml /
RUN micromamba install --name base --file /environment.yaml --root-prefix /software/micromamba --yes && \
    rm -rf /software/micromamba/pkgs

# set JAVA_HOME (useful for Docker commandline)
ENV JAVA_HOME='/software/micromamba'

# install Google Cloud SDK
# RUN curl https://sdk.cloud.google.com | bash && \
#     echo "source /root/google-cloud-sdk/completion.bash.inc; source /root/google-cloud-sdk/path.bash.inc" >> ~/.bashrc

# copy all files of the repo and change owner
COPY ./ /v2d

# set default directory
WORKDIR /v2d

# default command
CMD ["/bin/bash"]
