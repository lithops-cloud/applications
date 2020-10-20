#!/bin/bash

URL="http://moments.csail.mit.edu/moments_models/moments_RGB_resnet50_imagenetpretrained.pth.tar"
DOCKER_USER=$(docker info | sed '/Username:/!d;s/.* //')

wget $URL -O model_weights

pywren-ibm-cloud runtime build $DOCKER_USER/pywren-runtime-resnet -f with_weights.Dockerfile

rm model_weights
