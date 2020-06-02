# Python 3.6
FROM continuumio/miniconda3:4.5.4 

# YOU MUST PIN THE PYTHON VERSION TO PREVENT IT TO BE UPDATED
RUN echo "python==3.6.5" >> /opt/conda/conda-meta/pinned

ENV FLASK_PROXY_PORT 8080

RUN apt-get update \
        # Upgrade installed packages to get latest security fixes if the base image does not contain them already.
        && apt-get upgrade -y --no-install-recommends \
        # add some packages required for the pip install
        && apt-get install -y --no-install-recommends \
           gcc \
           libc-dev \
           libxslt-dev \
           libxml2-dev \
           libffi-dev \
           libssl-dev \
           zip \
           unzip \
           vim \
        # install required lib for opencv-python
        && apt-get install -y libgtk2.0-dev \
        # cleanup package lists, they are not used anymore in this image
        && rm -rf /var/lib/apt/lists/* \
        && apt-cache search linux-headers-generic

# Add your Conda required packages here. Ensure "conda clean --all" at 
# the end to remove temporary data. One "RUN" line is better than multiple
# ones in terms of image size. For example:
RUN conda update -n base conda \
    && conda install -c conda-forge ffmpeg \
    && conda install -c pytorch pytorch torchvision cpuonly \
    && conda clean --all


# install additional python modules
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip setuptools six && pip install --no-cache-dir -r requirements.txt

RUN pip install opencv-python
        
# create action working directory
RUN mkdir -p /action \
    && mkdir -p /actionProxy \
    && mkdir -p /pythonAction

ADD https://raw.githubusercontent.com/apache/openwhisk-runtime-docker/8b2e205c39d84ed5ede6b1b08cccf314a2b13105/core/actionProxy/actionproxy.py /actionProxy/actionproxy.py
ADD https://raw.githubusercontent.com/apache/openwhisk-runtime-python/3%401.0.3/core/pythonAction/pythonrunner.py /pythonAction/pythonrunner.py

CMD ["/bin/bash", "-c", "cd /pythonAction && python -u pythonrunner.py"]

