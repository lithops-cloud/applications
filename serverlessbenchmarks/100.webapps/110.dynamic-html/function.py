from datetime import datetime
from os import path
from random import sample
import time
import json

import click
from jinja2 import Template
from lithops import FunctionExecutor

size_generators = {
    'test': 10,
    'small': 1000,
    'large': 100000
}

SCRIPT_DIR = path.abspath(path.join(path.dirname(__file__)))


def handler(username, random_len, template):
    cur_time = datetime.now()
    random_numbers = sample(range(0, 1000000), random_len)
    template = Template(template)
    html = template.render(username=username, cur_time=cur_time, random_numbers=random_numbers)
    return {'result': html}


def benchmark(backend, storage, tasks, size, memory, outdir, name, log_level):
    input_config = {'username': 'testname'}
    input_config['random_len'] = size_generators[size]
    input_config['template'] = open(path.join(SCRIPT_DIR, 'template.html')).read()
    iterable = [input_config] * tasks

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
@click.option('--name', default='110.dynamic-html', help='Filename to save results in')
@click.option('--log_level', default='INFO', help='Log level', type=str)
def run_benchmark(backend, storage, tasks, size, memory, outdir, name, log_level):
    benchmark(backend, storage, tasks, size, memory, outdir, name, log_level)


if __name__ == '__main__':
    run_benchmark()
