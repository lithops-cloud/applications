#!/bin/bash

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it and login before running this script."
    exit 1
fi

if [ $# -ne 2 ]; then
    echo "Usage: $0 <region> <lambda_role_name>"
    echo "Where <lambda_role_name> is the name of the role, not the full arn (e.g. LambdaExecutionRole)."
    exit 1
fi

# Assign parameters to variables
region=$1
lambda_role_name=$2

# Run the command and store the output in a variable
output=$(aws sts get-caller-identity)

# Use jq to extract the value of "Arn" and then use awk to get the part after the last ":"
caller_id=$(echo $output | jq -r '.UserId' | awk -F ':' '{print $NF}')
aws_account_id=$(echo $output | jq -r '.Account')

aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $aws_account_id.dkr.ecr.$region.amazonaws.com

aws ecr create-repository --repository-name lithops_v310_$caller_id/jordi44/serverless-benchmarks --region $region
aws ecr create-repository --repository-name lithops_v310_$caller_id/jordi44/variant-calling --region $region
aws ecr create-repository --repository-name lithops_v310_$caller_id/jordi44/model-calculation --region $region

docker pull jordi44/serverless-benchmarks:01
container_id=$(docker images -q jordi44/serverless-benchmarks:01)
docker tag $container_id $aws_account_id.dkr.ecr.$region.amazonaws.com/lithops_v310_$caller_id/jordi44/serverless-benchmarks:01
docker push $aws_account_id.dkr.ecr.$region.amazonaws.com/lithops_v310_$caller_id/jordi44/serverless-benchmarks:01

docker pull jordi44/variant-calling:01
container_id=$(docker images -q jordi44/variant-calling:01)
docker tag $container_id $aws_account_id.dkr.ecr.$region.amazonaws.com/lithops_v310_$caller_id/jordi44/variant-calling:01
docker push $aws_account_id.dkr.ecr.$region.amazonaws.com/lithops_v310_$caller_id/jordi44/variant-calling:01

docker pull jordi44/model-calculation:01
container_id=$(docker images -q jordi44/model-calculation:01)
docker tag $container_id $aws_account_id.dkr.ecr.$region.amazonaws.com/lithops_v310_$caller_id/jordi44/model-calculation:01
docker push $aws_account_id.dkr.ecr.$region.amazonaws.com/lithops_v310_$caller_id/jordi44/model-calculation:01

echo "Deploying lithops runtimes..."
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 2560
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 2048
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 1536
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 1024
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 1792
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 512
lithops runtime deploy jordi44/serverless-benchmarks:01 --memory 256
lithops runtime deploy jordi44/model-calculation:01 --memory 4096 --timeout 500
lithops runtime deploy jordi44/variant-calling:01 --memory 8192
echo "Lithops runtimes deployed with exit!!!"

echo "Deploying cruicial lambda function..."
cd serverless_benchmarks/elastic-exploration

sed -i "s|<lambda.awsAccountId>.*</lambda.awsAccountId>|<lambda.awsAccountId>${aws_account_id}</lambda.awsAccountId>|g" "pom.xml"
sed -i "s|<lambda.roleName>.*</lambda.roleName>|<lambda.roleName>${lambda_role_name}</lambda.roleName>|g" "pom.xml"

mvn package shade:shade lambda:deploy-lambda -DskipTests
mvn clean package
