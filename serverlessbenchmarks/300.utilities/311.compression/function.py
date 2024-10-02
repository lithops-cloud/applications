import datetime
import os
import random
import shutil
import time
import uuid

from lithops import FunctionExecutor, Storage

storage = Storage()


def download_directory(bucket, key, download_path):
    storage = Storage()

    for key in storage.list_keys(bucket, prefix=key):
        storage.download_file(bucket, key, os.path.join(download_path, os.path.basename(key)))


def parse_directory(directory):
    size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            size += os.path.getsize(os.path.join(root, file))
    return size

def handler(bucket, input, output, key):
    storage = Storage()
    download_path = '/tmp/{}'.format(key)
    archive_name = '{}-{}'.format(key, uuid.uuid4())
    archive_path = '/tmp/{}'.format(archive_name)
    os.makedirs(download_path)

    s3_download_begin = datetime.datetime.now()
    download_directory(bucket, os.path.join(input, key), download_path)
    s3_download_stop = datetime.datetime.now()
    size = parse_directory(download_path)

    compress_begin = datetime.datetime.now()
    shutil.make_archive(archive_path, 'zip', root_dir=download_path)
    compress_end = datetime.datetime.now()

    s3_upload_begin = datetime.datetime.now()
    archive_size = os.path.getsize(archive_path + '.zip')
    storage.upload_file(archive_path + '.zip', bucket, os.path.join(output, archive_name + '.zip'))
    s3_upload_stop = datetime.datetime.now()

    download_time = (s3_download_stop - s3_download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (s3_upload_stop - s3_upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (compress_end - compress_begin) / datetime.timedelta(microseconds=1)
    return {
            'result': {
                'bucket': bucket,
                'key': os.path.join(bucket, output, archive_name + '.zip')
            },
            'measurement': {
                'download_time': download_time,
                'download_size': size,
                'upload_time': upload_time,
                'upload_size': archive_size,
                'compute_time': process_time
            }
        }


def upload_files(data_root, data_dir, bucket, input):
    for root, dirs, files in os.walk(data_dir):
        prefix = os.path.relpath(root, data_root)
        for file in files:
            file_name = prefix + '/' + file
            filepath = os.path.join(root, file)
            storage.upload_file(filepath, bucket, os.path.join(input, file_name))


def benchmark(data_dir, benchmarks_bucket, input_paths, output_paths, tasks):
    '''
        Generate test, small and large workload for compression test.

        :param data_dir: directory where benchmark data is placed
        :param size:
        :param input_buckets:
        :param output_buckets:
    '''

    # upload different datasets
    datasets = []

    for dir in os.listdir(data_dir):
        datasets.append(dir)
        upload_files(data_dir, os.path.join(data_dir, dir), benchmarks_bucket, input_paths)

    input_config_template = {
        'bucket': benchmarks_bucket,
        'input': input_paths,
        'output': output_paths
    }

    iterable = []
    for _ in range(tasks):
        input_config = input_config_template.copy()
        input_config['key'] = random.choice(datasets)
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
    print(results)


if __name__ == '__main__':
    tasks = 1
    data_dir = ''
    bucket_name = ''
    input_folder = ''
    output_folder = ''
    benchmark(data_dir, bucket_name, input_folder, output_folder, tasks)
