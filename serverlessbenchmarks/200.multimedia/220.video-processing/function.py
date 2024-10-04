import datetime
import glob
import json
import os
import random
import stat
import subprocess
import time
import uuid

import click
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
    upload_key = os.path.join(output, filename)
    storage.upload_file(upload_path, bucket, upload_key)
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


def benchmark(backend, storage_backend, tasks, datadir, bucket_name, inbucket, outbucket, memory, outdir, name, log_level):
    '''
        Generate test, small and large workload for thumbnailer.
    '''
    storage = Storage()

    # Upload ffmpeg binary and watermark image
    for file in glob.glob(os.path.join(SCRIPT_DIR, 'resources', '*')):
        storage.upload_file(file, bucket_name, os.path.join(inbucket, 'resources', os.path.basename(file)))

    # Prepare input data
    list_keys = []

    for file in glob.glob(os.path.join(datadir, '*.mp4')):
        img = os.path.relpath(file, datadir)
        list_keys.append(img)
        storage.put_object(bucket_name, os.path.join(inbucket, img), open(file, 'rb').read())

    input_config_template = {
        'op': 'watermark',
        'duration': 1,
        'bucket': bucket_name,
        'input': inbucket,
        'output': outbucket
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
@click.option('--name', default='220.video-processing', help='Filename to save results in')
@click.option('--log_level', default='INFO', help='Log level', type=str)
def run_benchmark(backend, storage, tasks, datadir, bucket_name, inbucket, outbucket, memory, outdir, name, log_level):
    benchmark(backend, storage, tasks, datadir, bucket_name, inbucket, outbucket, memory, outdir, name, log_level)


if __name__ == '__main__':
    run_benchmark()
