import datetime
import json
import os
import random
import time
import uuid

from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import resnet50

from lithops import FunctionExecutor, Storage


SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
class_idx = json.load(open(os.path.join(SCRIPT_DIR, "imagenet_class_index.json"), 'r'))
idx2label = [class_idx[str(k)][1] for k in range(len(class_idx))]
model = None


def handler(model_storage, bucket, input, key):
    storage = Storage()
    download_path = '/tmp/{}-{}'.format(key, uuid.uuid4())

    image_download_begin = datetime.datetime.now()
    image_path = download_path
    storage.download_file(bucket, os.path.join(input, key), image_path)
    image_download_end = datetime.datetime.now()

    global model
    if not model:
        model_download_begin = datetime.datetime.now()
        model_path = os.path.join('/tmp', model_storage)
        storage.download_file(bucket, os.path.join(input, model_storage), model_path)
        model_download_end = datetime.datetime.now()
        model_process_begin = datetime.datetime.now()
        model = resnet50(pretrained=False)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        model_process_end = datetime.datetime.now()
    else:
        model_download_begin = datetime.datetime.now()
        model_download_end = model_download_begin
        model_process_begin = datetime.datetime.now()
        model_process_end = model_process_begin

    process_begin = datetime.datetime.now()
    input_image = Image.open(image_path)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0)  # create a mini-batch as expected by the model
    output = model(input_batch)
    _, index = torch.max(output, 1)
    # The output has unnormalized scores. To get probabilities, you can run a softmax on it.
    prob = torch.nn.functional.softmax(output[0], dim=0)
    _, indices = torch.sort(output, descending=True)
    ret = idx2label[index]
    process_end = datetime.datetime.now()

    download_time = (image_download_end- image_download_begin) / datetime.timedelta(microseconds=1)
    model_download_time = (model_download_end - model_download_begin) / datetime.timedelta(microseconds=1)
    model_process_time = (model_process_end - model_process_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    return {
            'result': {'idx': index.item(), 'class': ret},
            'measurement': {
                'download_time': download_time + model_download_time,
                'compute_time': process_time + model_process_time,
                'model_time': model_process_time,
                'model_download_time': model_download_time
            }
        }


def benchmark(data_dir, benchmarks_bucket, input_paths, tasks):
    '''
        Generate test, small and large workload for compression test.
        :param data_dir: directory where benchmark data is placed
        :param input_buckets: 
    '''
    storage = Storage()

    # upload model
    model_name = 'resnet50-19c8e357.pth'
    storage.upload_file(os.path.join(data_dir, 'model', model_name), benchmarks_bucket, os.path.join(input_paths, model_name))

    input_images = []
    resnet_path = os.path.join(data_dir, 'fake-resnet')
    with open(os.path.join(resnet_path, 'val_map.txt'), 'r') as f:
        for line in f:
            img, img_class = line.split()
            input_images.append(img)
            storage.upload_file(os.path.join(resnet_path, img), benchmarks_bucket, os.path.join(input_paths, img))

    input_config_template = {
        'model_storage': model_name,
        'bucket': benchmarks_bucket,
        'input': input_paths,
    }

    iterable = []
    for _ in range(tasks):
        input_config = input_config_template.copy()
        input_config['key'] = random.choice(input_images)
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
    benchmark(data_dir, bucket_name, input_folder, tasks)
