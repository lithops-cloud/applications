import datetime
import glob
import io
import os
import random
import time
import uuid
from PIL import Image
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
    key_name = storage.put_object(bucket, os.path.join(output_folder, upload_key), resized.getvalue())
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

    for file in glob.glob(os.path.join(data_dir, '*.jpg')):
        img = os.path.relpath(file, data_dir)
        list_keys.append(img)
        storage.put_object(bucket, os.path.join(input_folder, img), open(file, 'rb').read())

    input_config_template = {
        'width': 200,
        'height': 200,
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
    tasks = 100
    data_dir = ''
    bucket_name = ''
    input_folder = ''
    output_folder = ''
    benchmark(data_dir, bucket_name, input_folder, output_folder, tasks)
