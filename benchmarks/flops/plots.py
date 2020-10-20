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

import os
import pylab
import logging
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import LineCollection

pylab.switch_backend("Agg")
logger = logging.getLogger(__name__)


def create_execution_histogram(benchmark_data, dst):
    start_time = benchmark_data['start_time']
    time_rates = [(f['worker_start_tstamp'], f['worker_end_tstamp']) for f in benchmark_data['worker_stats']]
    total_calls = len(time_rates)

    max_seconds = int(max([tr[1]-start_time for tr in time_rates])*1.1)
    max_seconds = 8 * round(max_seconds/8)

    runtime_bins = np.linspace(0, max_seconds, max_seconds)

    def compute_times_rates(time_rates):
        x = np.array(time_rates)
        tzero = start_time
        tr_start_time = x[:, 0] - tzero
        tr_end_time = x[:, 1] - tzero

        N = len(tr_start_time)

        runtime_calls_hist = np.zeros((N, len(runtime_bins)))

        for i in range(N):
            s = tr_start_time[i]
            e = tr_end_time[i]
            a, b = np.searchsorted(runtime_bins, [s, e])
            if b-a > 0:
                runtime_calls_hist[i, a:b] = 1

        return {'start_time': tr_start_time,
                'end_time': tr_end_time,
                'runtime_calls_hist': runtime_calls_hist}

    fig = pylab.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)

    time_hist = compute_times_rates(time_rates)

    N = len(time_hist['start_time'])
    line_segments = LineCollection([[[time_hist['start_time'][i], i],
                                     [time_hist['end_time'][i], i]] for i in range(N)],
                                   linestyles='solid', color='k', alpha=0.6, linewidth=0.4)

    ax.add_collection(line_segments)

    ax.plot(runtime_bins, time_hist['runtime_calls_hist'].sum(axis=0), label='Parallel Functions', zorder=-1)

    yplot_step = int(np.max([1, total_calls/20]))
    y_ticks = np.arange(total_calls//yplot_step + 2) * yplot_step
    ax.set_yticks(y_ticks)
    ax.set_ylim(-0.02*total_calls, total_calls*1.02)

    xplot_step = max(int(max_seconds/8), 1)
    x_ticks = np.arange(int(max_seconds//xplot_step)+1) * xplot_step
    ax.set_xlim(0, max_seconds)
    ax.set_xticks(x_ticks)
    for x in x_ticks:
        ax.axvline(x, c='k', alpha=0.2, linewidth=0.8)

    ax.set_xlabel("Execution Time (sec)")
    ax.set_ylabel("Function Call")
    ax.grid(False)
    ax.legend(loc='upper right')

    fig.tight_layout()

    dst = os.path.expanduser(dst) if '~' in dst else dst

    fig.savefig(dst)
    pylab.close(fig)


def create_rates_histogram(benchmark_data, dst):
    results_df = pd.DataFrame(benchmark_data['results'])
    flops = results_df.flops/1e9

    fig = pylab.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)
    ax.hist(flops, bins=np.arange(0, flops.max()*1.2), histtype='bar', ec='black')
    ax.set_xlabel('GFLOPS')
    ax.set_ylabel('Total functions')
    ax.yaxis.grid(True)
    """
    fig = pylab.figure(figsize=(5, 5))
    sns.distplot(flops, label='GFLOPS Rate', kde=False, hist_kws=dict(alpha=0.8, edgecolor="k", linewidth=1))
    pylab.legend()
    pylab.xlabel("GFLOPS")
    pylab.ylabel("Total functions")
    pylab.grid(True, axis='y')
    """

    dst = os.path.expanduser(dst) if '~' in dst else dst

    fig.tight_layout()
    fig.savefig(dst)


def create_total_gflops_plot(benchmark_data, dst):
    tzero = benchmark_data['start_time']
    data_df = pd.DataFrame(benchmark_data['worker_stats'])
    data_df['est_flops'] = benchmark_data['est_flops'] / benchmark_data['workers']

    max_time = np.max(data_df.worker_end_tstamp) - tzero
    runtime_bins = np.linspace(0, int(max_time), int(max_time), endpoint=False)
    runtime_flops_hist = np.zeros((len(data_df), len(runtime_bins)))

    for i in range(len(data_df)):
        row = data_df.iloc[i]
        s = row.worker_func_start_tstamp - tzero
        e = row.worker_func_end_tstamp - tzero
        a, b = np.searchsorted(runtime_bins, [s, e])
        if b-a > 0:
            runtime_flops_hist[i, a:b] = row.est_flops / float(b-a)

    results_by_endtime = data_df.sort_values('worker_end_tstamp')
    results_by_endtime['job_endtime_zeroed'] = data_df.worker_end_tstamp - tzero
    results_by_endtime['flops_done'] = results_by_endtime.est_flops.cumsum()
    results_by_endtime['rolling_flops_rate'] = results_by_endtime.flops_done/results_by_endtime.job_endtime_zeroed

    fig = pylab.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)

    ax.plot(runtime_flops_hist.sum(axis=0)/1e9, label='Peak GFLOPS')
    ax.plot(results_by_endtime.job_endtime_zeroed, results_by_endtime.rolling_flops_rate/1e9, label='Effective GFLOPS')
    ax.set_xlabel('Execution Time (sec)')
    ax.set_ylabel("GFLOPS")
    ax.set_xlim(-1)
    ax.set_ylim(-1)
    pylab.legend(loc='upper right')
    ax.grid(True)

    dst = os.path.expanduser(dst) if '~' in dst else dst

    fig.tight_layout()
    fig.savefig(dst)
