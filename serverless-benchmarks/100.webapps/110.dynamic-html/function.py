from lithops import FunctionExecutor
from datetime import datetime
from random import sample
from os import path
import time

from jinja2 import Template

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


def benchmark(size, tasks):
    input_config = {'username': 'testname'}
    input_config['random_len'] = size_generators[size]
    input_config['template'] = open(path.join(SCRIPT_DIR, 'template.html')).read()

    iterable = [input_config] * tasks

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
    tasks = 10
    benchmark('test', tasks)
