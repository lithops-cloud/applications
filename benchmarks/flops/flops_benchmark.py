#
# Copyright Cloudlab URV 2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import click
import time
import numpy as np
import pickle as pickle

from lithops import FunctionExecutor
from plots import create_execution_histogram, create_rates_histogram, create_total_gflops_plot


def compute_flops(loopcount, MAT_N):

    A = np.arange(MAT_N**2, dtype=np.float64).reshape(MAT_N, MAT_N)
    B = np.arange(MAT_N**2, dtype=np.float64).reshape(MAT_N, MAT_N)

    start = time.time()
    for i in range(loopcount):
        c = np.sum(np.dot(A, B))

    FLOPS = 2 * MAT_N**3 * loopcount
    end = time.time()
    return {'flops': FLOPS / (end-start)}


def benchmark(workers, memory, loopcount, matn):
    iterable = [(loopcount, matn) for i in range(workers)]

    fexec = FunctionExecutor(runtime_memory=memory)
    start_time = time.time()
    worker_futures = fexec.map(compute_flops, iterable)
    results = fexec.get_result()
    end_time = time.time()

    worker_stats = [f.stats for f in worker_futures]
    total_time = end_time-start_time

    print("Total time:", round(total_time, 3))
    est_flops = workers * 2 * loopcount * matn ** 3
    print('Estimated GFLOPS:', round(est_flops / 1e9 / total_time, 4))

    res = {'start_time': start_time,
           'total_time': total_time,
           'est_flops': est_flops,
           'worker_stats': worker_stats,
           'results': results}

    return res


def create_plots(data, outdir, name):
    create_execution_histogram(data, "{}/{}_execution.png".format(outdir, name))
    create_rates_histogram(data, "{}/{}_rates.png".format(outdir, name))
    create_total_gflops_plot(data, "{}/{}_gflops.png".format(outdir, name))


@click.command()
@click.option('--workers', default=10, help='how many workers', type=int)
@click.option('--memory', default=1024, help='Memory per worker in MB', type=int)
@click.option('--outdir', default='.', help='dir to save results in')
@click.option('--name', default='flops_benchmark', help='filename to save results in')
@click.option('--loopcount', default=6, help='Number of matmuls to do.', type=int)
@click.option('--matn', default=1024, help='size of matrix', type=int)
def run_benchmark(workers, memory, outdir, name, loopcount, matn):
    if True:
        res = benchmark(workers, memory, loopcount, matn)
        res['loopcount'] = loopcount
        res['workers'] = workers
        res['MATN'] = matn
        pickle.dump(res, open('{}/{}.pickle'.format(outdir, name), 'wb'))
    else:
        res = pickle.load(open('{}/{}.pickle'.format(outdir, name), 'rb'))
    create_plots(res, outdir, name)


if __name__ == "__main__":
    run_benchmark()
