# SeBS: Serverless Benchmark Suite

**FaaS benchmarking suite for serverless functions with automatic build, deployment, and measurements.**

SeBS is a diverse suite of FaaS benchmarks that allows automatic performance analysis of commercial and open-source serverless platforms. We provide a suite of benchmark applications and use them to test and evaluate different components of FaaS systems.

To execute the benchmarks, run the `function.py` file corresponding to each benchmark. This will initiate the benchmark using your Lithops backend.

Certain benchmarks may require a custom runtime due to specific requirements. To build a custom runtime, use the following command:

```bash
lithops runtime build -f <path-to-dockerfile> <runtime-name>
```

For detailed information about your Dockerfile, please refer to the [runtime repository](https://github.com/lithops-cloud/lithops/tree/master/runtime) of Lithops. Additional information on building custom runtimes can be found in the [Lithops documentation](https://lithops-cloud.github.io/docs/source/cli.html#runtime-management).

For further details on the Serverless benchmarks, please visit the [original repository](https://github.com/spcl/serverless-benchmarks/tree/master).