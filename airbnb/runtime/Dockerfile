#FROM python:3.5-slim-jessie
FROM python:3.6-slim-jessie

ENV FLASK_PROXY_PORT 8080

RUN apt-get update && apt-get upgrade -y \
	&& apt-get install -y \
		gcc \
		libc-dev \
		libxslt-dev \
		libxml2-dev \
		libffi-dev \
		libssl-dev \
		zip \
 		unzip \
		vim \
		libgeos-dev \
		wget \
		python3-matplotlib \
		&& rm -rf /var/lib/apt/lists/* \
		&& apt-cache search linux-headers-generic \
		&& wget https://github.com/matplotlib/basemap/archive/v1.1.0.tar.gz \
		&& tar -xvzf v1.1.0.tar.gz && cd basemap-1.1.0 \
		&& pip install --no-cache-dir -r requirements.txt \ 
		&& pip install numpy \
		&& python setup.py install \
		&& cd .. && rm -r v1.1.0.tar.gz basemap-1.1.0/

RUN pip install --upgrade pip setuptools six \
    && pip install --no-cache-dir -U \
        simplejson==3.16.0 \
        httplib2==0.13.0 \
        kafka_python==1.4.6 \
        lxml==4.3.1 \
        python-dateutil==2.8.0 \
        pika==0.13.1 \
        flask==1.1.1 \
        gevent==1.4.0 \
        ibm-cos-sdk==2.6.0 \
        redis==3.3.8 \
        requests==2.22.0 \
        numpy==1.18.1 nltk twython geos geopy pillow matplotlib pyproj
      
RUN python -m nltk.downloader vader_lexicon

# create action working directory
RUN mkdir -p /action \
    && mkdir -p /actionProxy \
    && mkdir -p /pythonAction

ADD https://raw.githubusercontent.com/apache/openwhisk-runtime-docker/8b2e205c39d84ed5ede6b1b08cccf314a2b13105/core/actionProxy/actionproxy.py /actionProxy/actionproxy.py
ADD https://raw.githubusercontent.com/apache/openwhisk-runtime-python/3%401.0.3/core/pythonAction/pythonrunner.py /pythonAction/pythonrunner.py

CMD ["/bin/bash", "-c", "cd /pythonAction && python -u pythonrunner.py"]

