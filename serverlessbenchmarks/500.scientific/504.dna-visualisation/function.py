import datetime
import glob
import io
import json
import os
import random
import time
import uuid

from lithops import FunctionExecutor, Storage

# using https://squiggle.readthedocs.io/en/latest/
from squiggle import transform


def handler(bucket, input_folder, output_folder, key):
    storage = Storage()
    download_path = '/tmp/{}'.format(key)

    download_begin = datetime.datetime.now()
    storage.download_file(bucket, os.path.join(input_folder, key), download_path)
    download_stop = datetime.datetime.now()
    data = open(download_path, "r").read()

    process_begin = datetime.datetime.now()
    result = transform(data)
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    buf = io.BytesIO(json.dumps(result).encode())
    buf.seek(0)
    key_name = storage.put_object(bucket, os.path.join(output_folder, '{}-{}'.format(uuid.uuid4(), key)), buf)
    upload_stop = datetime.datetime.now()
    buf.close()

    download_time = (download_stop - download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_stop - upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)

    return {
            'result': {
                'bucket': bucket,
                'key': key_name
            },
            'measurement': {
                'download_time': download_time,
                'compute_time': process_time,
                'upload_time': upload_time
            }
    }


def benchmark(data_dir, bucket, input_folder, output_folder, tasks):
    '''
        Generate test, small and large workload for thumbnailer.

        :param data_dir: str - path to the directory containing the images
        :param bucket: str - bucket name
        :param input_folder: str - input folder of the bucket
        :param output_folder: str - output folder of the bucket
        :param tasks: int - number of tasks to execute
    '''
    storage = Storage()

    list_keys = []

    for file in glob.glob(os.path.join(data_dir, '*.fasta')):
        data = os.path.relpath(file, data_dir)
        list_keys.append(data)
        storage.upload_file(file, bucket, os.path.join(input_folder, data))

    input_config_template = {
        'bucket': bucket,
        'input_folder': input_folder,
        'output_folder': output_folder
    }

    iterable = []
    for _ in range(tasks):
        input_config = input_config_template.copy()
        input_config['key'] = random.choice(list_keys)
        iterable.append(input_config)

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
    data_dir = ''
    bucket_name = ''
    input_folder = ''
    output_folder = ''
    benchmark(data_dir, bucket_name, input_folder, output_folder, tasks)
