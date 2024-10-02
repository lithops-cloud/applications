import datetime
import os
import stat
import subprocess
import glob
import random
import time
import uuid
from lithops import FunctionExecutor, Storage


SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))


def call_ffmpeg(args):
    ret = subprocess.run([os.path.join(os.getcwd(), 'ffmpeg'), '-y'] + args,
            # subprocess might inherit Lambda's input for some reason
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if ret.returncode != 0:
        print('Invocation of ffmpeg failed!')
        print('Out: ', ret.stdout.decode('utf-8'))
        raise RuntimeError()


# https://superuser.com/questions/556029/how-do-i-convert-a-video-to-gif-using-ffmpeg-with-reasonable-quality
def to_gif(video, duration):
    output = '/tmp/processed-{}.gif'.format(os.path.basename(video))
    call_ffmpeg(["-i", video,
        "-t",
        "{0}".format(duration),
        "-vf",
        "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        output])
    return output


# https://devopstar.com/2019/01/28/serverless-watermark-using-aws-lambda-layers-ffmpeg/
def watermark(video, duration):
    output = '/tmp/processed-{}'.format(os.path.basename(video))
    call_ffmpeg([
        "-i", video,
        "-i", 'watermark.png',
        "-t", "{0}".format(duration),
        "-filter_complex", "overlay=main_w/2-overlay_w/2:main_h/2-overlay_h/2",
        output])
    return output


def transcode_mp3(video, duration):
    pass


operations = {'transcode': transcode_mp3, 'extract-gif': to_gif, 'watermark': watermark}


def handler(op, duration, bucket, input, output, key):
    storage = Storage()

    download_path = '/tmp/{}'.format(key)

    # Download ffmpeg binary and watermark image
    storage.download_file(bucket, os.path.join(input, 'resources', 'ffmpeg'), 'ffmpeg')
    storage.download_file(bucket, os.path.join(input, 'resources', 'watermark.png'), 'watermark.png')

    # Print all folders in the current directory
    print('Current directory: ', os.getcwd())
    print('Folders in current directory: ', os.listdir(os.getcwd()))

    # Print all files in the current directory
    print('Files in current directory: ', os.listdir(os.getcwd()))

    # Restore executable permission
    try:
        st = os.stat('ffmpeg')
        os.chmod('ffmpeg', st.st_mode | stat.S_IEXEC)
    except OSError:
        pass

    download_begin = datetime.datetime.now()
    storage.download_file(bucket, os.path.join(input, key), download_path)
    download_size = os.path.getsize(download_path)
    download_stop = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    upload_path = operations[op](download_path, duration)
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    filename = '{}-{}'.format(uuid.uuid4(), os.path.basename(upload_path))
    upload_size = os.path.getsize(upload_path)
    upload_key = storage.upload_file(upload_path, bucket, os.path.join(output, filename))
    upload_stop = datetime.datetime.now()

    download_time = (download_stop - download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_stop - upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    return {
            'result': {
                'bucket': bucket,
                'key': upload_key
            },
            'measurement': {
                'download_time': download_time,
                'download_size': download_size,
                'upload_time': upload_time,
                'upload_size': upload_size,
                'compute_time': process_time
            }
        }


def benchmark(data_dir, benchmarks_bucket, input_folder, output_folder, tasks):
    '''
        Generate test, small and large workload for thumbnailer.

        :param data_dir: directory where benchmark data is placed
        :param size: 
        :param input_buckets: 
        :param output_buckets:
        :param upload_func: 
    '''
    storage = Storage()

    # Upload ffmpeg binary and watermark image
    for file in glob.glob(os.path.join(SCRIPT_DIR, 'resources', '*')):
        storage.upload_file(file, benchmarks_bucket, os.path.join(input_folder, 'resources', os.path.basename(file)))

    # Prepare input data
    list_keys = []

    for file in glob.glob(os.path.join(data_dir, '*.mp4')):
        img = os.path.relpath(file, data_dir)
        list_keys.append(img)
        storage.put_object(benchmarks_bucket, os.path.join(input_folder, img), open(file, 'rb').read())

    input_config_template = {
        'op': 'watermark',
        'duration': 1,
        'bucket': benchmarks_bucket,
        'input': input_folder,
        'output': output_folder
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
    print(results)


if __name__ == '__main__':
    tasks = 1
    data_dir = ''
    bucket_name = ''
    input_folder = ''
    output_folder = ''
    benchmark(data_dir, bucket_name, input_folder, output_folder, tasks)
