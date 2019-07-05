FROM continuumio/miniconda:4.6.14

# Conda and the envirounment dependencies
COPY ./environment.yaml /v2d/
WORKDIR /v2d
RUN conda env create -n v2d_data --file environment.yaml
# overrule base envirounment set in .bashrc file
RUN echo "source activate v2d_data" >> ~/.bashrc
ENV PATH /opt/conda/envs/v2d_data/bin:$PATH

# Google Cloud SDK
RUN curl https://sdk.cloud.google.com | bash

# Plink
ENV PLINK_VERSION       1.07
ENV PLINK_HOME          /usr/local/plink
ENV PATH                $PLINK_HOME:$PATH

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y unzip wget && \
    wget http://zzz.bwh.harvard.edu/plink/dist/plink-$PLINK_VERSION-x86_64.zip && \
    unzip plink-$PLINK_VERSION-x86_64.zip -d /usr/local/ && \
    rm plink-$PLINK_VERSION-x86_64.zip && \
    cd /usr/local && \
    ln -s plink-$PLINK_VERSION-x86_64 $PLINK_HOME && \
    DEBIAN_FRONTEND=noninteractive apt-get autoremove -y unzip wget && \
    rm -rf /var/lib/apt/lists/* && \
    echo '#!/bin/bash'                                                 > /usr/local/bin/plink && \
    echo '#Launch the real plink script forcing the --noweb argument' >> /usr/local/bin/plink && \
    echo '/usr/local/plink/plink --noweb "$@"'                        >> /usr/local/bin/plink && \
    chmod a+x /usr/local/bin/plink

# Entrypoint
COPY ./entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD [ "/bin/bash" ]

# Copy the v2d project
COPY ./ /v2d
