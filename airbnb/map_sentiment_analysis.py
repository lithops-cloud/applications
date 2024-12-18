import io
import base64
import time
import shutil
import csv
import lithops
import matplotlib.pyplot as plt


BUCKET = ['cos://airbnb-dataset/']

DATASET = {'amsterdam-2016-01-03-reviews.csv': 'Amsterdam',
           'antwerp-2015-10-03-reviews.csv': 'Antwerp Belgium',
           'athens-2015-07-17-reviews.csv': 'Athens Europe',
           'austin-2015-11-07-reviews.csv': 'Austin',
           'barcelona-2016-01-03-reviews.csv': 'Barcelona',
           'berlin-2015-10-03-reviews.csv': 'Berlin',
           'boston-2015-10-03-reviews.csv': 'Boston',
           'brussels-2015-10-03-reviews.csv': 'Brussels',
           'chicago-2015-10-03-reviews.csv': 'Chicago',
           'dublin-2016-01-06-reviews.csv': 'Dublin',
           'london-2016-02-02-reviews.csv': 'London',
           'los-angeles-2016-01-02-reviews.csv': 'Los Angeles',
           'madrid-2015-10-02-reviews.csv': 'Madrid',
           'mallorca-2016-01-06-reviews.csv': 'Palma Mallorca Spain',
           'melbourne-2016-01-03-reviews.csv': 'Melbourne',
           'montreal-2015-10-02-reviews.csv': 'Montreal',
           'nashville-2015-10-03-reviews.csv': 'Nashville',
           'new-orleans-2015-09-02-reviews.csv': 'New Orleans',
           'new-york-city-2016-02-02-reviews.csv': 'New York City',
           'oakland-2015-06-22-reviews.csv': 'Oakland',
           'paris-2015-09-02-reviews.csv': 'Paris',
           'portland-2016-01-01-reviews.csv': 'Portland',
           'san-diego-2015-06-22-reviews.csv': 'San Diego',
           'san-francisco-2015-11-01-reviews.csv': 'City of San Francisco',
           'santa-cruz-county-2015-10-15-reviews.csv': 'Santa Cruz',
           'seattle-2016-01-04-reviews.csv': 'Seattle',
           'sydney-2016-01-03-reviews.csv': 'Sydney',
           'toronto-2015-09-03-reviews.csv': 'Toronto',
           'trentino-2015-10-12-reviews.csv': 'Trento',
           'vancouver-2015-12-03-reviews.csv': 'Vancouver',
           'venice-2015-07-18-reviews.csv': 'Venice Italy',
           'vienna-2015-07-18-reviews.csv': 'Vienna Austria.',
           'washington-dc-2015-10-03-reviews.csv': 'Washington D.C.'}


def analyze_comments(obj):
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    city = DATASET[obj.key]
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

    geolocator = Nominatim(user_agent="lithops")
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


if __name__ == "__main__":
    t0 = time.time()

    fexec = lithops.FunctionExecutor(runtime='jsampe/lithops-mpl-nltk-v36', runtime_memory=2048)
    fexec.map_reduce(analyze_comments, BUCKET, create_map, obj_reduce_by_key=True)
    # fexec.map(analyze_comments, BUCKET)
    results = fexec.get_result()

    for res in results:
        with open("maps/{}.png".format(res['city']), "wb") as i:
            i.write(base64.b64decode(res['map']))
        print('{}: {}'.format(res['city'], res['comments']))

    print('Total time: {} seconds'.format(round(time.time()-t0, 2)))
    fexec.plot(dst='plots/test')
