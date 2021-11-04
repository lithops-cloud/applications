# Object Storage Bandwidth Benchmark from FaaS Service

Execution example:

```
python3 os_benchmark.py run -b aws_lambda -s aws_s3 --mb_per_file=512 --bucket_name=bench-data --number=100 --outdir=aws_s3
```
