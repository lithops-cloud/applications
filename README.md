# Lithops end-to-end Applications

This repository contains examples of Lithops applications in different ambits.

1. [Flops and object storage benchmarks](benchmarks)

2. [Monte Carlo applications](montecarlo)

3. [Hyperparameter tuning grid search](sklearn)

4. [Moments in time](momentsintime)

5. [Mandelbrot set computation](mandelbrot)

6. [GROMACS computations](gromacs)

7. [Airbnb comments sentiment analysis](airbnb)

8. [Serverless benchmarks](serverlessbenchmarks)

We have gathered a comprehensive collection of serverless pipelines implemented in Lithops (or related serverless projects, as [Crucial](https://dl.acm.org/doi/abs/10.1145/3361525.3361535)) and characterized them. You can find the complete listing and their code references [here](PIPELINES.md).

# Running in AWS

AWS is the simplest cloud provider to test the applications on. We provide a set of publicly available datasets that can be easily imported to users' custom buckets. You simply need the AWS CLI [installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).

Once AWS CLI is correctly set up, execute [import_datasets_aws.sh](./import_datasets_aws.sh) to import test inputs to your AWS S3 bucket or local directory. It uses "Requester pays" billing, so the client is billed for the data downloaded.

```bash
chmod +x import_datasets_aws.sh
./import_datasets_aws.sh MY_BUCKET
# Examples:
# ./import_datasets_aws.sh s3://bucket-name -> import to a AWS S3 bucket.
# ./import_datasets_aws.sh /home/user/lithops-data -> import to a local directory.
```

You need to configure Lithops with your own AWS account keys. Follow the configuration guide for [aws_lambda](https://lithops-cloud.github.io/docs/source/compute_config/aws_lambda.html) and [aws_s3](https://lithops-cloud.github.io/docs/source/storage_config/aws_s3.html).


# Demo run

We provide a public AMI to run out-of-the-box Lithops data analytics pipelines in AWS. Please refer to [demo](demo). 
