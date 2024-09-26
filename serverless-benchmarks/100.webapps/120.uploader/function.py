from lithops import FunctionExecutor
from lithops import Storage
import datetime
import os
import time
import uuid

import urllib.request


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
    key_name = storage.put_object(bucket, os.path.join(output_folder, name), open(download_path, 'rb').read())
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


def benchmark(size, bucket, output_folder, tasks):
    input_config = {}
    input_config['url'] = url_generators[size]
    input_config['bucket'] = bucket
    input_config['output_folder'] = output_folder
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
    bucket_name = ''
    output_folder = ''
    benchmark('test', bucket_name, output_folder, tasks)
