# Demo: Serverless Pipelines

This demo is prepared to automate small runs of Lithops serverless pipelines in AWS. We provide a public AWS AMI (id: ami-0b4e12e0012d96b6f, you can find it in the AWS community AMIs cataloque in region us-east-1) with all the necessary requirements installed and prepared to run the benchmarks. The necessary runtimes for Lithops benchmarks are deployed previously as public Docker containers in Docker Hub ([runtime1](https://hub.docker.com/r/jordi44/serverless-benchmarks), [runtime2](https://hub.docker.com/r/jordi44/variant-calling), [runtime3](https://hub.docker.com/r/jordi44/model-calculation), [runtime4](https://hub.docker.com/r/jordi44/water-consumption)).

The scripts used in this tutorial are stored in `/home/ubuntu/` directory of the AMI.

## Requirements

    - An AWS Account
    - A Docker Hub account

## Instructions

1. Launch EC2 instance from this AMI.

2. Connect to the EC2 using `ubuntu` user name (as shown in this [link](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-linux-inst-ssh.html)).

3. Login in Docker:
   ```
   $ docker login
   ```
   
4. Introduce your AWS credentials. You have to options:
   - Edit the file `home/ubuntu/.aws/credentials`.
   - Use AWS cli:
      ```
      $ aws configure
      ```  
5. Set up an appropriate [AWS Lambda role](https://lithops-cloud.github.io/docs/source/compute_config/aws_lambda.html#configuration). Save its ARN.

6. Run the `update_aws_credentials.sh` script in order to propagate your credentials to all necessary config files. The first time you run this demo you should pass the name of the storage bucket in which you want to store the results and the **ARN** of your AWS Lambda Role as options:
      ```
      $ ./update_aws_credentials -r <YOUR_ROLE_ARN> -b <YOUR_S3_BUCKET>
      ``` 
    
7. Run the `deploy_runtimes.sh` script in order to deploy the runtimes needed to run each of the benchmarks. You must pass by parameter the aws region name in which you want to deploy them (preferably use `us-east-1`) and the **name** of the AWS Lambda role:
      ```
      $ ./deploy_runtimes <AWS_REGION> <AWS_LAMBDA_ROLE_NAME>
      ``` 


8. Then all is ready to start testing the benchmarks. You can use the `run_benchmark.sh` script to test a single benchmark or all one after the other. You just have to use the `-b` option to specify the benchmark:
      ```
      $ ./run_benchmark -b flops
      ``` 
      ```
      $ ./run_benchmark --benchmark all
      ```
   In case that more space in EBS is needed you can just increase it following this [instructions](https://repost.aws/knowledge-center/expand-ebs-root-volume-windows).

**Note:** Additionally, the `build_runtimes.sh` scripts allows you to build all the runtimes and AWS Lambda functions instead of using the docker images deployed in `deploy_runtimes.sh` script. However, this step will take a long time. Before running it, you should comment the lines tha perform `docker push` in case you dont want to upload the docker images to your Docker Hub account. You can use it as follows:
  ```
  $ ./build_runtimes
  ``` 
