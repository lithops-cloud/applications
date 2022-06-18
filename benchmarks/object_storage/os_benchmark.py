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

import uuid
import numpy as np
import time
import hashlib
import pickle
import click

from lithops import FunctionExecutor, Storage
from plots import create_execution_histogram, create_rates_histogram, create_agg_bdwth_plot


class RandomDataGenerator(object):
    """
    A file-like object which generates random data.
    1. Never actually keeps all the data in memory so
    can be used to generate huge files.
    2. Actually generates random data to eliminate
    false metrics based on compression.

    It does this by generating data in 1MB blocks
    from np.random where each block is seeded with
    the block number.
    """

    def __init__(self, bytes_total):
        self.bytes_total = bytes_total
        self.pos = 0
        self.current_block_id = None
        self.current_block_data = ""
        self.BLOCK_SIZE_BYTES = 1024*1024
        self.block_random = np.random.randint(0, 256, dtype=np.uint8,
                                              size=self.BLOCK_SIZE_BYTES)

    def __len__(self):
        return self.bytes_total

    @property
    def len(self):
        return self.bytes_total 

    def tell(self):
        return self.pos

    def seek(self, pos, whence=0):
        if whence == 0:
            self.pos = pos
        elif whence == 1:
            self.pos += pos
        elif whence == 2:
            self.pos = self.bytes_total - pos

    def get_block(self, block_id):
        if block_id == self.current_block_id:
            return self.current_block_data

        self.current_block_id = block_id
        self.current_block_data = (block_id + self.block_random).tostring()
        return self.current_block_data

    def get_block_coords(self, abs_pos):
        block_id = abs_pos // self.BLOCK_SIZE_BYTES
        within_block_pos = abs_pos - block_id * self.BLOCK_SIZE_BYTES
        return block_id, within_block_pos

    def read(self, bytes_requested):
        remaining_bytes = self.bytes_total - self.pos
        if remaining_bytes == 0:
            return b''

        bytes_out = min(remaining_bytes, bytes_requested)
        start_pos = self.pos

        byte_data = b''
        byte_pos = 0
        while byte_pos < bytes_out:
            abs_pos = start_pos + byte_pos
            bytes_remaining = bytes_out - byte_pos

            block_id, within_block_pos = self.get_block_coords(abs_pos)
            block = self.get_block(block_id)
            # how many bytes can we copy?
            chunk = block[within_block_pos:within_block_pos + bytes_remaining]

            byte_data += chunk

            byte_pos += len(chunk)

        self.pos += bytes_out

        return byte_data


runtime_bins = np.linspace(0, 50, 50)


def write(backend, storage, bucket_name, mb_per_file, number, key_prefix, debug):

    def write_object(key_name, storage):
        bytes_n = mb_per_file * 1024**2
        d = RandomDataGenerator(bytes_n)
        print(key_name)
        start_time = time.time()
        storage.put_object(bucket_name, key_name, d)
        end_time = time.time()

        mb_rate = bytes_n/(end_time-start_time)/1e6
        print('MB Rate: '+str(mb_rate))

        return {'start_time': start_time, 'end_time': end_time, 'mb_rate': mb_rate}

    # create list of random keys
    keynames = [key_prefix + str(uuid.uuid4().hex.upper()) for unused in range(number)]

    log_level = 'INFO' if not debug else 'DEBUG'
    fexec = FunctionExecutor(backend=backend, storage=storage, runtime_memory=1024, log_level=log_level)
    start_time = time.time()
    worker_futures = fexec.map(write_object, keynames)
    results = fexec.get_result(throw_except=False)
    end_time = time.time()
    total_time = end_time-start_time
    results = [gbs for gbs in results if gbs is not None]
    worker_stats = [f.stats for f in worker_futures if not f.error]

    res = {'start_time': start_time,
           'total_time': total_time,
           'worker_stats': worker_stats,
           'bucket_name': bucket_name,
           'keynames': keynames,
           'results': results}

    return res


def read(backend, storage, bucket_name, number, keylist_raw, read_times, debug):

    blocksize = 1024*1024

    def read_object(key_name, storage):
        m = hashlib.md5()
        bytes_read = 0
        print(key_name)

        start_time = time.time()
        for unused in range(read_times):
            fileobj = storage.get_object(bucket_name, key_name, stream=True)
            try:
                buf = fileobj.read(blocksize)
                while len(buf) > 0:
                    bytes_read += len(buf)
                    #if bytes_read % (blocksize *10) == 0:
                    #    mb_rate = bytes_read/(time.time()-t1)/1e6
                    #    print('POS:'+str(bytes_read)+' MB Rate: '+ str(mb_rate))
                    m.update(buf)
                    buf = fileobj.read(blocksize)
            except Exception as e:
                print(e)
                pass
        end_time = time.time()
        mb_rate = bytes_read/(end_time-start_time)/1e6
        print('MB Rate: '+str(mb_rate))

        return {'start_time': start_time, 'end_time': end_time, 'mb_rate': mb_rate, 'bytes_read': bytes_read}

    if number == 0:
        keynames = keylist_raw
    else:
        keynames = [keylist_raw[i % len(keylist_raw)] for i in range(number)]

    log_level = 'INFO' if not debug else 'DEBUG'
    fexec = FunctionExecutor(backend=backend, storage=storage, runtime_memory=1024, log_level=log_level)
    start_time = time.time()
    worker_futures = fexec.map(read_object, keynames)
    results = fexec.get_result(throw_except=False)
    end_time = time.time()
    total_time = end_time-start_time

    results = [gbs for gbs in results if gbs is not None]
    worker_stats = [f.stats for f in worker_futures if not f.error]

    res = {'start_time': start_time,
           'total_time': total_time,
           'worker_stats': worker_stats,
           'results': results}

    return res


def delete_temp_data(storage, bucket_name, keynames):
    print('Deleting temp files...')
    storage = Storage(backend=storage)
    try:
        storage.delete_objects(bucket_name, keynames)
    except:
        pass
    print('Done!')


def create_plots(res_write, res_read, outdir, name):
    create_execution_histogram(res_write, res_read, f"{outdir}/{name}_execution.png")
    create_rates_histogram(res_write, res_read, f"{outdir}/{name}_rates.png")
    create_agg_bdwth_plot(res_write, res_read, f"{outdir}/{name}_agg_bdwth.png")


@click.group()
def cli():
    pass


@cli.command('write')
@click.option('--backend', '-b', default='aws_lambda', help='compute backend name', type=str)
@click.option('--storage', '-s', default='aws_s3', help='storage backend name', type=str)
@click.option('--bucket_name', help='bucket to save files in')
@click.option('--mb_per_file', help='MB of each object', type=int)
@click.option('--number', help='number of files', type=int)
@click.option('--key_prefix', default='', help='Object key prefix')
@click.option('--outdir', default='.', help='dir to save results in')
@click.option('--name', default=None, help='filename to save results in')
@click.option('--debug', '-d', is_flag=True, help='debug mode')
def write_command(backend, storage, bucket_name, mb_per_file, number, key_prefix, outdir, name, debug):
    if name is None:
        name = number
    if bucket_name is None:
        raise ValueError('You must provide a bucket name within --bucket_name parameter')
    res_write = write(backend, storage, bucket_name, mb_per_file, number, key_prefix, debug)
    pickle.dump(res_write, open('{}/{}_write.pickle'.format(outdir, name), 'wb'), -1)


@cli.command('read')
@click.option('--backend', '-b', default='aws_lambda', help='compute backend name', type=str)
@click.option('--storage', '-s', default='aws_s3', help='storage backend name', type=str)
@click.option('--key_file', default=None, help="filename generated by write command, which contains the keys to read")
@click.option('--number', help='number of objects to read, 0 for all', type=int, default=0)
@click.option('--outdir', default='.', help='dir to save results in')
@click.option('--name', default=None, help='filename to save results in')
@click.option('--read_times', default=1, help="number of times to read each COS key")
@click.option('--debug', '-d', is_flag=True, help='debug mode')
def read_command(backend, storage, key_file, number, outdir, name, read_times, debug):
    if name is None:
        name = number
    if key_file:
        res_write = pickle.load(open(key_file, 'rb'))
    else:
        res_write = pickle.load(open('{}/{}_write.pickle'.format(outdir, name), 'rb'))
    bucket_name = res_write['bucket_name']
    keynames = res_write['keynames']
    res_read = read(backend, storage, bucket_name, number, keynames, read_times, debug)
    pickle.dump(res_read, open('{}/{}_read.pickle'.format(outdir, name), 'wb'), -1)


@cli.command('delete')
@click.option('--key_file', default=None, help="filename generated by write command, which contains the keys to read")
@click.option('--outdir', default='.', help='dir to save results in')
@click.option('--name', default='os_benchmark', help='filename to save results in')
def delete_command(key_file, outdir, name):
    if key_file:
        res_write = pickle.load(open(key_file, 'rb'))
    else:
        res_write = pickle.load(open('{}/{}_write.pickle'.format(outdir, name), 'rb'))
    bucket_name = res_write['bucket_name']
    keynames = res_write['keynames']
    delete_temp_data(bucket_name, keynames)


@cli.command('run')
@click.option('--backend', '-b', default='aws_lambda', help='compute backend name', type=str)
@click.option('--storage', '-s', default='aws_s3', help='storage backend name', type=str)
@click.option('--bucket_name', help='bucket to save files in')
@click.option('--mb_per_file', help='MB of each object', type=int)
@click.option('--number', help='number of files', type=int)
@click.option('--key_prefix', default='', help='Object key prefix')
@click.option('--outdir', default='.', help='dir to save results in')
@click.option('--name', '-n', default=None, help='filename to save results in')
@click.option('--read_times', default=1, help="number of times to read each COS key")
@click.option('--debug', '-d', is_flag=True, help='debug mode')
def run(backend, storage, bucket_name, mb_per_file, number, key_prefix, outdir, name, read_times, debug):
    if name is None:
        name = number

    if True:
        print('Executing Write Test:')
        if bucket_name is None:
            raise ValueError('You must provide a bucket name within --bucket_name parameter')
        res_write = write(backend, storage, bucket_name, mb_per_file, number, key_prefix, debug)
        pickle.dump(res_write, open(f'{outdir}/{name}_write.pickle', 'wb'), -1)
        print('Sleeping 20 seconds...')
        time.sleep(20)
        print('Executing Read Test:')
        bucket_name = res_write['bucket_name']
        keynames = res_write['keynames']
        res_read = read(backend, storage, bucket_name, number, keynames, read_times, debug)
        pickle.dump(res_read, open(f'{outdir}/{name}_read.pickle', 'wb'), -1)

        delete_temp_data(storage, bucket_name, keynames)
    else:
        res_write = pickle.load(open(f'{outdir}/{name}_write.pickle', 'rb'))
        res_read = pickle.load(open(f'{outdir}/{name}_read.pickle', 'rb'))
    create_plots(res_write, res_read, outdir, name)


if __name__ == '__main__':
    cli()
