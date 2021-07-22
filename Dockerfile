FROM ubuntu:21.04

ENV DEBIAN_FRONTEND=noninteractive

# Create non-root user 
ARG UID
ARG GID
RUN groupadd -g $GID -o otg
RUN useradd -m -u $UID -g $GID -o -s /bin/bash otg

# Do everything that requires root user
# install dependencies
RUN apt-get update && \
    apt-get install -y curl unzip wget bzip2 && \
    apt-get clean

# install micromamba
RUN mkdir -p /software/micromamba && \
    cd /software/micromamba && \
    wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/0.15.2 | tar -xvj bin/micromamba && \
    chown -R otg:otg /software
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
USER root
RUN chown -R otg:otg /v2d
USER otg

# set default directory
WORKDIR /v2d

# default command
CMD ["/bin/bash"]
