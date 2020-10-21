import io
import base64
import time
import shutil
import csv
import lithops
import matplotlib.pyplot as plt


BUCKET = 'cos://airbnb-dataset'

DATSET_URLS = [BUCKET+'/Amsterdam',
               BUCKET+'/Antwerp Belgium',
               BUCKET+'/Athens Europe',
               BUCKET+'/Austin',
               BUCKET+'/Barcelona',
               BUCKET+'/Berlin',
               BUCKET+'/Boston',
               BUCKET+'/Brussels',
               BUCKET+'/Chicago',
               BUCKET+'/Dublin',
               BUCKET+'/London',
               BUCKET+'/Los Angeles',
               BUCKET+'/Madrid',
               BUCKET+'/Palma Mallorca Spain',
               BUCKET+'/Melbourne',
               BUCKET+'/Montreal',
               BUCKET+'/Nashville',
               BUCKET+'/New Orleans',
               BUCKET+'/New York City',
               BUCKET+'/Oakland',
               BUCKET+'/Paris',
               BUCKET+'/Portland',
               BUCKET+'/San Diego',
               BUCKET+'/City of San Francisco',
               BUCKET+'/Santa Cruz',
               BUCKET+'/Seattle',
               BUCKET+'/Sydney',
               BUCKET+'/Toronto',
               BUCKET+'/Trento',
               BUCKET+'/Vancouver',
               BUCKET+'/Venice Italy',
               BUCKET+'/Vienna Austria.',
               BUCKET+'/Washington D.C.']


def analyze_comments(obj):
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    city = obj.key
    print('City: {}'.format(city))

    print('Copying dataset to local disk')
    with open('/tmp/{}.csv'.format(city), 'wb') as csvfile:
        shutil.copyfileobj(obj.data_stream, csvfile)
    print('Finished copying dataset to local disk')

    print('Parsing dataset')
    pos, neg, neu = 0, 0, 0
    positive, neutral, negative = [], [], []
    analyzer = SentimentIntensityAnalyzer()

    with open('/tmp/{}.csv'.format(city), encoding='latin1') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 11:
                continue
            vs = analyzer.polarity_scores(str(row[5]))
            if vs['compound'] >= 0.4:
                pos += 1
                if (row[8], row[9]) not in positive:
                    positive.append((row[8], row[9]))
            elif vs['compound'] < 0.4 and vs['compound'] > -0.4:
                neu += 1
                if (row[8], row[9]) not in neutral:
                    neutral.append((row[8], row[9]))
            else:
                neg += 1
                if (row[8], row[9]) not in negative:
                    negative.append((row[8], row[9]))

    print('Finished parsing dataset')

    return {'city': city, 'comments': {'positive': pos, 'neutral': neu, 'negative': neg},
            'coordinates': {'positive': positive, 'neutral': neutral, 'negative': negative}}


# Reduce Function
def create_map(results):
    from mpl_toolkits.basemap import Basemap
    from geopy.geocoders import Nominatim

    city = None
    comments = None
    coordinates = None

    for data in results:
        if data is None:
            continue
        if city is None:
            city = data['city']

        partial_comments = data['comments']
        partial_coordinates = data['coordinates']

        if not comments:
            comments = {'positive': 0, 'neutral': 0, 'negative': 0}
        if not coordinates:
            coordinates = {'positive': [], 'neutral': [], 'negative': []}

        comments['positive'] += partial_comments['positive']
        comments['neutral'] += partial_comments['neutral']
        comments['negative'] += partial_comments['negative']
        coordinates['positive'] += partial_coordinates['positive']
        coordinates['neutral'] += partial_coordinates['neutral']
        coordinates['negative'] += partial_coordinates['negative']

    print('Rendering Maps')
    plt.switch_backend('agg')
    plt.figure(figsize=(6.7, 6.7), dpi=96)

    geolocator = Nominatim()
    loc = geolocator.geocode(city)
    if not loc:
        print("Could not locate {}".format(city))
        raise Exception("Could not locate {}".format(city))

    m = Basemap(llcrnrlon=loc.longitude-0.12, llcrnrlat=loc.latitude-0.12,
                urcrnrlon=loc.longitude+0.12, urcrnrlat=loc.latitude+0.12,
                projection='lcc', resolution='l', epsg=4263,
                lat_0=loc.latitude, lon_0=loc.longitude)

    # World_Topo_Map
    # NatGeo_World_Map
    # World_Street_Map
    # ESRI_StreetMap_World_2D
    m.arcgisimage(service='NatGeo_World_Map', xpixels=500, verbose=False)

    # Positive
    lats = []
    longs = []
    for coord in coordinates['positive']:
        lat, long = coord
        try:
            lats.append(float(lat))
            longs.append(float(long))
        except Exception:
            pass
    m.scatter(longs, lats, marker='o', color='g', alpha=1, s=0.3)

    # neutral
    lats = []
    longs = []
    for coord in coordinates['neutral']:
        lat, long = coord
        try:
            lats.append(float(lat))
            longs.append(float(long))
        except Exception:
            pass
    m.scatter(longs, lats, marker='o', color='b', alpha=0.3, s=0.2)

    # negative
    lats = []
    longs = []
    for coord in coordinates['negative']:
        lat, long = coord
        try:
            lats.append(float(lat))
            longs.append(float(long))
        except Exception:
            pass
    m.scatter(longs, lats, marker='o', color='r', alpha=0.3, s=0.2)

    imgdata = io.BytesIO()
    plt.savefig(imgdata, format='png', bbox_inches='tight', pad_inches=0, dpi=96)
    imgdata.seek(0)  # rewind the data
    image_string = base64.encodebytes(imgdata.getvalue())
    print('Finished rendering map')

    return {'city': city, 'comments': comments, 'map': image_string}


CHUNK_SIZE = 8*1024**2


if __name__ == "__main__":
    t0 = time.time()
    fexec = lithops.FunctionExecutor(runtime='jsampe/lithops-mpl-nltk-v36', runtime_memory=1024)
    fexec.map_reduce(analyze_comments, BUCKET, create_map, chunk_size=CHUNK_SIZE, reducer_one_per_object=True)
    results = fexec.get_result()

    for res in results:
        with open("maps/{}.png".format(res['city']), "wb") as i:
            i.write(base64.b64decode(res['map']))
        print('{}: {}'.format(res['city'], res['comments']))

    print(time.time()-t0)
    fexec.plot(dst='plots/test')
