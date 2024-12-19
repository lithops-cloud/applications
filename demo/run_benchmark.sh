#!/bin/bash

display_usage() {
    echo -e "Usage: $0 [OPTION] [benchmark]\n"
    echo "Run a benchmark script for different use cases."
    echo -e "\nOptions:"
    echo -e "  -b, --benchmark BENCHMARK   specify the benchmark to run [flops, os, gridsearch, montecarlo, mandelbrot, ndvi, metaspace, all]"
    echo -e "  -h, --help                  display this help message and exit\n"
    echo "Examples:"
    echo -e "  $0 -b flops -s my_bucket\n  $0 --benchmark all --storage my_bucket"
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -b|--benchmark)
            benchmark_to_run="$2"
            shift 2
            ;;
        -h|--help)
            display_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            display_usage
            exit 1
            ;;
    esac
done


case $benchmark_to_run in
    flops)
        echo -e "\nRunning FLOPS benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/flops    
        python3 flops_benchmark.py -b  aws_lambda -s aws_s3 --loopcount=3 --matn=2048 --tasks=100 --memory=1024 --outdir=aws_lambda
        cd ../..
        deactivate
        ;;
    os)
        echo -e "\nRunning Object Storage benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/object_storage    
        python3 os_benchmark.py run -b aws_lambda -s aws_s3 --mb_per_file=512 --bucket_name=serverless-elastic-benchmarks --number=100 --outdir=aws_s3
        cd ../..
        deactivate
        ;;
    sklearn)
        echo -e "\nRunning Hyperparameter Tunning benchmark...\n"
        source benchmarks/bin/activate    
        cd serverless_benchmarks/sklearn    
        python3 gridsearch.py --backend lithops --mib 1 
        cd ../..
        deactivate
        ;;
    montecarlo)
        echo -e "\nRunning Montecarlo Pi estimation benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/pi-estimation    
        python3 pi-estimation.py 
        cd ../..
        deactivate
        ;;
    mandelbrot)
        echo -e "\nRunning Mandelbrot benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/mandelbrot
        python3 mandelbrot.py 
        cd ../..
        deactivate
        ;;
    ndvi)
        echo -e "\nRunning NDVI calculation benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/geospatial-usecase/ndvi-diff    
        python3 ndvi-diff.py 
        cd ../..
        deactivate
        ;;
    model-calculation)
        echo -e "\nRunning Model generation benchmark...\n"
        source ~/miniconda3/etc/profile.d/conda.sh
        conda activate geospatial
        cd serverless_benchmarks/geospatial-usecase/calculate-models
        python3 model-calculation.py
        cd ../..
        conda deactivate
        ;;
    metaspace)
        echo -e "\nRunning METASPACE benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/Lithops-METASPACE
        python3 annotation-pipeline-demo.py
        cd ../..
        deactivate
        ;;
    extract)
        echo -e "\nRunning Serverless Extract benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/serverlessextract
        python3 pipeline.py
        cd ../..
        deactivate
        ;;
    variant-calling)
        echo -e "\nRunning Variant Calling benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/serverless-genomics-variant-calling
        python3 example.py
        cd ../..
        deactivate
        ;;
    terasort)
        echo -e "\nRunning Terasort benchmark...\n"
        source benchmarks/bin/activate
        cd serverless_benchmarks/terasort-lithops
        python3 terasort.py --bucket serverless-elastic-benchmarks --key terasort-10 --map_parallelism 50 
        cd ../..
        deactivate
        ;;
    UTS)
        echo -e "\nRunning UTS algorithm benchmark...\n"
        cd serverless_benchmarks/elastic-exploration/target
        java -Xmx7g -Xms7g -cp utslambda-1.0.jar eu.cloudbutton.utslambda.serverless.taskmanager.TMServerlessUTS -depth 16 -warmupDepth 15 -workers 100
        cd ../../..
        ;;
    mariani-silver)
        echo -e "\nRunning Mandelbrot with Mariani Silver algorithm benchmark...\n"
        cd serverless_benchmarks/elastic-exploration/target
        java -Xmx7g -Xms7g -cp utslambda-1.0.jar eu.cloudbutton.mandelbrot.serverless.MarianiSilverServerless -width 724 -height 724 -workers 100
        cd ../../.. 
        ;;
    BC)
        echo -e "\nRunning Betweenness Centrality benchmark...\n"
        cd serverless_benchmarks/elastic-exploration/target
        java -Xmx7g -Xms7g -cp utslambda-1.0.jar eu.cloudbutton.bc.serverless.ServerlessBC -n 16 -w 100 -g 64
        cd ../../..
        ;;          
    all)
        # Execute all scripts
        $0 -b flops
        $0 -b os
        $0 -b sklearn
        $0 -b montecarlo
        $0 -b mandelbrot
        $0 -b ndvi
        $0 -b model-calculation
        $0 -b extract
        $0 -b metaspace
        $0 -b terasort
        $0 -b UTS
        $0 -b mariani-silver
        $0 -b BC
        $0 -b variant-calling
        ;;
    *)
        echo "Invalid argument. Please provide one of: flops, os, sklearn, montecarlo, mandelbrot, ndvi, model-calculation, metaspace, extract, variant-calling, terasort, UTS, mariani-silver, BC, all."
        exit 1
        ;;
esac
