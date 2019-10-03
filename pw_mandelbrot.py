import numpy as np
import pywren_ibm_cloud as pywren
from matplotlib import pyplot as plt
from matplotlib import colors
from math import sqrt
import pika, json, os, yaml

class MBPlotter:
    def __init__(self, ax, fig, width, height, blocks_per_row, mat_block_sz):
        self.ax = ax
        self.fig = fig
        self.width = width
        self.height = height
        self.blocks_per_row = blocks_per_row
        self.mat_block_sz = mat_block_sz

    def plotGraph(self, mat_chunks):
        z = np.empty((self.width, self.height))
        for m, mat in enumerate(mat_chunks):
            for i, row in enumerate(mat):
                a = int(i + ((m % self.blocks_per_row) * self.mat_block_sz))
                for j, col in enumerate(row):
                    b = int(j + ((m // self.blocks_per_row) * self.mat_block_sz))
                    z[a,b] = col
        self.ax.imshow(z.T, cmap='Spectral', origin='lower')
        self.fig.canvas.draw()
        
class AcumPlotCallback:
    def __init__(self, concurrency, plotter):
        self.count = concurrency
        self.plotter = plotter
        self.mat_acum = [None] * self.count

    def __call__(self, ch, method, properties, body):
        msg = json.loads(body.decode('utf-8'))
        chunk_pos = msg['position']
        chunk = msg['matrix']
                
        self.mat_acum[chunk_pos] = chunk
        self.count -= 1

        if not self.count:
            self.plotter.plotGraph(self.mat_acum)
            ch.stop_consuming()

def pw_mandelbrot_set(xmin, xmax, ymin, ymax, width, height, 
                      concurrency, maxiter, queue_name):
     
    mat_block_sz = int(sqrt((width * height) / concurrency))    
    blocks_per_column = blocks_per_row = concurrency / sqrt(concurrency)    
    x_step = (abs(xmax-xmin) / blocks_per_row)
    y_step = (abs(ymax-ymin) / blocks_per_column)

    def mandelbrot_chunk_fn(block_pos, rabbitmq):
        rx_min = xmin + ((block_pos % blocks_per_row) * x_step)
        ry_min = ymin + ((block_pos // blocks_per_column) * y_step)
        rx = np.linspace(rx_min, rx_min + x_step, mat_block_sz)
        ry = np.linspace(ry_min, ry_min + y_step, mat_block_sz)
        c = rx + ry[:,None]*1j
        output = np.zeros((mat_block_sz, mat_block_sz))
        z = np.zeros((mat_block_sz, mat_block_sz), np.complex64)
    
        channel = rabbitmq.channel()
    
        for it in range(maxiter+1):
            notdone = np.less(z.real*z.real + z.imag*z.imag, 4.0)
            output[notdone] = it
            z[notdone] = z[notdone]**2 + c[notdone]

        body = {
            'position' : block_pos,
            'matrix' : output.transpose().tolist()
        }
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(body))

    pw = pywren.ibm_cf_executor()
    pw.map(mandelbrot_chunk_fn, range(concurrency))
    
def mandelbrot_image(xmin, xmax, ymin, ymax, width, height, 
                     maxiter, concurrency, subplots=None):

    dpi = 72
    if not subplots:
        fig, ax = create_subplots(width, height)
    else:
        fig, ax = subplots
    ticks = np.arange(0,width,3*dpi)
    x_ticks = xmin + (xmax-xmin)*ticks/width
    plt.xticks(ticks, x_ticks)
    y_ticks = ymin + (ymax-ymin)*ticks/height
    plt.yticks(ticks, y_ticks)

    with open(os.path.expanduser('~/.pywren_config'), 'r') as f:
        secret = yaml.safe_load(f)
    pika_params = pika.URLParameters(secret['rabbitmq']['amqp_url'])
    connection = pika.BlockingConnection(pika_params)
    channel = connection.channel()
    queue_name = 'pw-mandelbrot-result-queuee'
    channel.queue_declare(queue_name)

    mat_block_sz = int(sqrt((width * height) / concurrency))    
    blocks_per_row = concurrency / sqrt(concurrency) 
    plotter = MBPlotter(ax, fig, width, height, blocks_per_row, mat_block_sz)
    callback = AcumPlotCallback(concurrency, plotter)

    pw_mandelbrot_set(xmin, xmax, ymin, ymax, width, height, concurrency, maxiter, queue_name)
    channel.basic_consume(consumer_callback=callback, queue=queue_name, no_ack=True)
    channel.start_consuming()


def create_subplots(width, height):
    dpi = 72
    img_width = width / dpi
    img_height = height / dpi
    fig, ax = plt.subplots(figsize=(img_width, img_height), dpi=dpi)
    
    plt.ion()
    fig.show()
    fig.canvas.draw()

    return fig, ax
    