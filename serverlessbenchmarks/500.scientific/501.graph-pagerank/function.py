import datetime
import json
import time

import click
import igraph
from lithops import FunctionExecutor


size_generators = {
    'test': 10,
    'small': 10000,
    'large': 100000
}


def handler(size):
    graph_generating_begin = datetime.datetime.now()
    graph = igraph.Graph.Barabasi(size, 10)
    graph_generating_end = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    result = graph.pagerank()
    process_end = datetime.datetime.now()

    graph_generating_time = (graph_generating_end - graph_generating_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)

    return {
            'result': result[0],
            'measurement': {
                'graph_generating_time': graph_generating_time,
                'compute_time': process_time
            }
    }


def benchmark(backend, storage, tasks, size, memory, outdir, name, log_level):
    iterable = [size_generators[size]] * tasks

    fexec = FunctionExecutor(backend=backend, storage=storage, runtime_memory=memory, log_level=log_level)

    start_time = time.time()
    fexec.map(handler, iterable)
    results = fexec.get_result(throw_except=False)
    end_time = time.time()

    results = [flops for flops in results if flops is not None]
    total_time = end_time-start_time
    print("Total time:", round(total_time, 3))

    # Save results to json
    with open('{}/{}.json'.format(outdir, name), 'w') as f:
        json.dump(results, f, indent=4)
    fexec.plot(dst='{}/{}'.format(outdir, name))


@click.command()
@click.option('--backend', '-b', default=None, help='Compute backend name', type=str)
@click.option('--storage', '-s', default=None, help='Storage backend name', type=str)
@click.option('--tasks', default=10, help='How many tasks', type=int)
@click.option('--size', default='test', help='Size of the benchmark', type=str)
@click.option('--memory', default=1024, help='Memory per worker in MB', type=int)
@click.option('--outdir', default='.', help='Directory to save results in')
@click.option('--name', default='501.graph-pagerank', help='Filename to save results in')
@click.option('--log_level', default='INFO', help='Log level', type=str)
def run_benchmark(backend, storage, tasks, size, memory, outdir, name, log_level):
    benchmark(backend, storage, tasks, size, memory, outdir, name, log_level)


if __name__ == '__main__':
    run_benchmark()
