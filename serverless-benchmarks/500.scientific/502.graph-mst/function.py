import datetime
import time

from lithops import FunctionExecutor
import igraph

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
    result = graph.spanning_tree(None, False)
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


def benchmark(size, tasks):
    iterable = [size_generators[size]] * tasks

    # fexec = FunctionExecutor(backend=backend, storage=storage, runtime_memory=memory, log_level=log_level)
    fexec = FunctionExecutor()

    start_time = time.time()
    fexec.map(handler, iterable)
    results = fexec.get_result(throw_except=False)
    end_time = time.time()

    results = [flops for flops in results if flops is not None]
    total_time = end_time-start_time
    print("Total time:", round(total_time, 3))


if __name__ == '__main__':
    tasks = 1
    benchmark('test', tasks)
