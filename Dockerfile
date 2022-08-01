FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Do everything that requires root user
# install dependencies
RUN apt-get update && \
    apt-get install -y curl unzip wget bzip2 libgoogle-glog-dev sudo && \
    apt-get clean

# Create non-root user and allow it to run `sudo chown ...` without password
RUN useradd -m -r otg && \
    echo "otg ALL = NOPASSWD: /usr/bin/chown" >> /etc/sudoers

# install micromamba
RUN mkdir -p /software/micromamba && \
    cd /software/micromamba && \
    wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/0.15.2 | tar -xvj bin/micromamba && \
    chown -R otg /software
ENV PATH="/software/micromamba/bin:${PATH}"

# switch to otg user
USER otg

# create conda/mamba environment
COPY ./environment.yaml /home/otg
RUN micromamba install --name base --file /home/otg/environment.yaml --root-prefix /software/micromamba --yes

# set JAVA_HOME (useful for Docker commandline)
ENV JAVA_HOME='/software/micromamba'

# install Google Cloud SDK
# RUN curl https://sdk.cloud.google.com | bash && \
#     echo "source /root/google-cloud-sdk/completion.bash.inc; source /root/google-cloud-sdk/path.bash.inc" >> ~/.bashrc

# copy all files of the repo and change owner
COPY ./ /v2d
RUN sudo chown -R otg /v2d

# set default directory
WORKDIR /v2d

# default command
CMD ["/bin/bash"]
