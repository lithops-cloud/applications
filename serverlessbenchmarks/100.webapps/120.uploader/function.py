import datetime
import json
import os
import time
import uuid
import urllib.request

import click
from lithops import FunctionExecutor, Storage


url_generators = {
    # source: mlperf fake_imagenet.sh. 230 kB
    'test': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Jammlich_crop.jpg/800px-Jammlich_crop.jpg',
    # video: HPX source code, 6.7 MB
    'small': 'https://github.com/STEllAR-GROUP/hpx/archive/refs/tags/1.4.0.zip',
    # resnet model from pytorch. 98M
    'large':  'https://download.pytorch.org/models/resnet50-19c8e357.pth'
}


def handler(url, bucket, output_folder):
    name = '{}-{}'.format(uuid.uuid4(), os.path.basename(url))
    download_path = '/tmp/{}'.format(name)

    process_begin = datetime.datetime.now()
    urllib.request.urlretrieve(url, filename=download_path)
    size = os.path.getsize(download_path)
    process_end = datetime.datetime.now()

    storage = Storage()
    upload_begin = datetime.datetime.now()
    key_name = os.path.join(output_folder, name)
    storage.put_object(bucket, key_name, open(download_path, 'rb').read())
    upload_end = datetime.datetime.now()

    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    return {
            'result': {
                'bucket': bucket,
                'url': url,
                'key': key_name
            },
            'measurement': {
                'download_time': 0,
                'download_size': 0,
                'upload_time': upload_time,
                'upload_size': size,
                'compute_time': process_time
            }
    }


def benchmark(backend, storage, tasks, size, bucket_name, outbucket, memory, outdir, name, log_level):
    input_config = {}
    input_config['url'] = url_generators[size]
    input_config['bucket'] = bucket_name
    input_config['output_folder'] = outbucket
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
@click.option('--bucket_name', help='Bucket name in your storage backend', type=str, required=True)
@click.option('--outbucket', help='Output folder in your storage backend', type=str, required=True)
@click.option('--memory', default=1024, help='Memory per worker in MB', type=int)
@click.option('--outdir', default='.', help='Directory to save results in')
@click.option('--name', default='120.uploader', help='Filename to save results in')
@click.option('--log_level', default='INFO', help='Log level', type=str)
def run_benchmark(backend, storage, tasks, size, bucket_name, outbucket, memory, outdir, name, log_level):
    benchmark(backend, storage, tasks, size, bucket_name, outbucket, memory, outdir, name, log_level)


if __name__ == '__main__':
    run_benchmark()
