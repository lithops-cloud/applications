FROM dhak/pywren-runtime-pytorch:3.6

RUN mkdir /momentsintime
ADD model_weights /momentsintime/model_weights