import datetime
import glob
import io
import json
import os
import random
import time
import uuid

from PIL import Image

import click
from lithops import FunctionExecutor, Storage


# Disk-based solution
# def resize_image(image_path, resized_path, w, h):
#    with Image.open(image_path) as image:
#        image.thumbnail((w, h))
#        image.save(resized_path)

# Memory-based solution
def resize_image(image_bytes, w, h):
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.thumbnail((w, h))
        out = io.BytesIO()
        image.save(out, format='jpeg')
        # necessary to rewind to the beginning of the buffer
        out.seek(0)
        return out


def handler(key, width, height, bucket, input_folder, output_folder):
    storage = Storage()

    download_begin = datetime.datetime.now()
    img = storage.get_object(bucket, os.path.join(input_folder, key))
    download_end = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    resized = resize_image(img, width, height)
    resized_size = resized.getbuffer().nbytes
    process_end = datetime.datetime.now()

    upload_key = 'resized-{}-{}'.format(uuid.uuid4(), key)
    upload_begin = datetime.datetime.now()
    key_name = os.path.join(output_folder, upload_key)
    storage.put_object(bucket, key_name, resized.getvalue())
    upload_end = datetime.datetime.now()

    download_time = (download_end - download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    return {
            'result': {
                'bucket': bucket,
                'key': key_name
            },
            'measurement': {
                'download_time': download_time,
                'download_size': len(img),
                'upload_time': upload_time,
                'upload_size': resized_size,
                'compute_time': process_time
            }
    }


def benchmark(backend, storage_backend, tasks, datadir, bucket_name, inbucket, outbucket, memory, outdir, name, log_level):
    '''
        Generate test, small and large workload for thumbnailer.
    '''
    storage = Storage()

    list_keys = []

    for file in glob.glob(os.path.join(datadir, '*.jpg')):
        img = os.path.relpath(file, datadir)
        list_keys.append(img)
        storage.put_object(bucket_name, os.path.join(inbucket, img), open(file, 'rb').read())

    input_config_template = {
        'width': 200,
        'height': 200,
        'bucket': bucket_name,
        'input_folder': inbucket,
        'output_folder': outbucket
    }

    iterable = []
    for _ in range(tasks):
        input_config = input_config_template.copy()
        input_config['key'] = random.choice(list_keys)
        iterable.append(input_config)

    fexec = FunctionExecutor(backend=backend, storage=storage_backend, runtime_memory=memory, log_level=log_level)

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
@click.option('--datadir', help='Directory containing all the data', type=str, required=True)
@click.option('--bucket_name', help='Bucket name in your storage backend', type=str, required=True)
@click.option('--inbucket', help='Folder where will be stored the input data in your storage backend', type=str, required=True)
@click.option('--outbucket', help='Folder where will be stored the output data in your storage backend', type=str, required=True)
@click.option('--memory', default=1024, help='Memory per worker in MB', type=int)
@click.option('--outdir', default='.', help='Directory to save results in')
@click.option('--name', default='210.thumbnailer', help='Filename to save results in')
@click.option('--log_level', default='INFO', help='Log level', type=str)
def run_benchmark(backend, storage, tasks, datadir, bucket_name, inbucket, outbucket, memory, outdir, name, log_level):
    benchmark(backend, storage, tasks, datadir, bucket_name, inbucket, outbucket, memory, outdir, name, log_level)


if __name__ == '__main__':
    run_benchmark()
