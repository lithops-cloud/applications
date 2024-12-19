#!/bin/bash
docker login

source benchmarks/bin/activate

lithops runtime build -f serverless_benchmarks/runtimes/aws_all.Dockerfile jordi44/serverless-benchmarks:01
docker push jordi44/serverless-benchmarks:01
cd $HOME/serverless_benchmarks/serverless-genomics-variant-calling/dockerfile/
lithops runtime build -f lambda.Dockerfile jordi44/variant-calling:01
docker push jordi44/variant-calling:01
deactivate

source ~/miniconda3/etc/profile.d/conda.sh
conda activate geospatial
cd $HOME/serverless_benchmarks/geospatial-usecase/calculate-models/runtime/
lithops runtime build -f aws_lambda.Dockerfile jordi44/model-calculation:01
docker push jordi44/model-calculation:01
cd $HOME
conda deactivate