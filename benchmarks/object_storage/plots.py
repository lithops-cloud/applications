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

READ_COLOR = (0.12156862745098039, 0.4666666666666667, 0.7058823529411765)
WRITE_COLOR = (1.0, 0.4980392156862745, 0.054901960784313725)


def create_execution_histogram(res_write, res_read, dst):

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

    fig, axes2d = pylab.subplots(nrows=1, ncols=2, sharex=True, sharey=True, figsize=(5, 5))

    for plot_i, (datum, l, c) in enumerate([(res_write, 'Write', WRITE_COLOR), (res_read, 'Read', READ_COLOR)]):

        start_time = datum['start_time']
        time_rates = [(f['worker_start_tstamp'], f['worker_end_tstamp']) for f in datum['worker_stats']]
        total_calls = len(time_rates)

        if plot_i == 0:
            max_seconds = int(max([tr[1]-start_time for tr in time_rates])*1.2)
            max_seconds = 8 * round(max_seconds/8)
            runtime_bins = np.linspace(0, max_seconds, max_seconds)

        ax = axes2d[plot_i]

        time_hist = compute_times_rates(time_rates)

        N = len(time_hist['start_time'])
        line_segments = LineCollection([[[time_hist['start_time'][i], i],
                                         [time_hist['end_time'][i], i]] for i in range(N)],
                                       linestyles='solid', color='k', alpha=0.6, linewidth=0.4)

        ax.add_collection(line_segments)

        ax.plot(runtime_bins, time_hist['runtime_calls_hist'].sum(axis=0), label='Parallel {} Functions'.format(l), zorder=-1, c=c)

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

        ax.set_xlabel('.', color=(0, 0, 0, 0))
        if plot_i == 0:
            ax.set_ylabel("Function Call")
        ax.grid(False)

    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    #fig.legend(lines, labels, loc='upper right')
    fig.legend(lines, labels, bbox_to_anchor=[0.955, 0.885])

    fig.text(0.5, 0.04, 'Execution Time (sec)', va='center', ha='center', fontsize=pylab.rcParams['axes.labelsize'])

    fig.tight_layout()

    dst = os.path.expanduser(dst) if '~' in dst else dst

    fig.savefig(dst)
    pylab.close(fig)


def create_rates_histogram(res_write, res_read, dst):
    write_esults_df = pd.DataFrame(res_write['results'])
    write_rates = write_esults_df.mb_rate

    read_esults_df = pd.DataFrame(res_read['results'])
    read_rates = read_esults_df.mb_rate

    """
    fig = pylab.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)

    ax.hist(write_rates, bins=np.arange(0, write_rates.max()*1.2), histtype='bar', ec='black', color=WRITE_COLOR, alpha=0.8)
    ax.hist(read_rates, bins=np.arange(0, read_rates.max()*1.2), histtype='bar', ec='black', color=READ_COLOR, alpha=0.8)
    ax.set_xlabel('MB/sec')
    ax.set_ylabel('Total functions')
    ax.yaxis.grid(True)
    """

    fig = pylab.figure(figsize=(5, 5))
    sns.distplot(write_rates, label='Write MB Rate', color=WRITE_COLOR, kde=False, hist_kws=dict(alpha=0.8, edgecolor="k", linewidth=1))
    sns.distplot(read_rates, label='Read MB Rate', color=READ_COLOR, kde=False, hist_kws=dict(alpha=0.8, edgecolor="k", linewidth=1))
    pylab.legend()
    pylab.xlabel("MB/sec")
    pylab.ylabel("Total functions")
    pylab.grid(True, axis='y')

    dst = os.path.expanduser(dst) if '~' in dst else dst

    fig.tight_layout()
    fig.savefig(dst)


def create_agg_bdwth_plot(res_write, res_read, dst):

    def compute_times_rates(start_time, d):

        x = np.array(d)
        tzero = start_time
        tr_start_time = x[:, 0] - tzero
        tr_end_time = x[:, 1] - tzero
        rate = x[:, 2]

        N = len(tr_start_time)
        runtime_rate_hist = np.zeros((N, len(runtime_bins)))

        for i in range(N):
            s = tr_start_time[i]
            e = tr_end_time[i]
            a, b = np.searchsorted(runtime_bins, [s, e])
            if b-a > 0:
                runtime_rate_hist[i, a:b] = rate[i]

        return {'start_time': tr_start_time,
                'end_time': tr_end_time,
                'rate': rate,
                'runtime_rate_hist': runtime_rate_hist}

    fig = pylab.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)
    for datum, l, c in [(res_write, 'Aggregate Write Bandwidth', WRITE_COLOR), (res_read, 'Aggregate Read Bandwidth', READ_COLOR)]:
        start_time = datum['start_time']
        mb_rates = [(res['start_time'], res['end_time'], res['mb_rate']) for res in datum['results']]
        max_seconds = int(max([mr[1]-start_time for mr in mb_rates])*1.2)
        max_seconds = 8 * round(max_seconds/8)
        runtime_bins = np.linspace(0, max_seconds, max_seconds)

        mb_rates_hist = compute_times_rates(start_time, mb_rates)

        ax.plot(mb_rates_hist['runtime_rate_hist'].sum(axis=0)/1000, label=l, c=c)

    ax.set_xlabel('Execution Time (sec)')
    ax.set_ylabel("GB/sec")
    ax.set_xlim(0, )
    ax.set_ylim(0, )
    pylab.legend()
    pylab.grid(True, axis='y')

    dst = os.path.expanduser(dst) if '~' in dst else dst

    fig.tight_layout()
    fig.savefig(dst)
