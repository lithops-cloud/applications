from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

import joblib

from pprint import pprint
from time import time
import click
import bz2


def load_data(mib):
    # Download the dataset at
    # https://www.kaggle.com/bittlingmayer/amazonreviews

    print("Loading Amazon reviews dataset:")
    compressed = bz2.BZ2File('./train.ft.txt.bz2')

    X = []
    y = []
    total_size = 0
    for _ in range(3_600_000):
        line = compressed.readline().decode('utf-8')
        X.append(line[11:])
        y.append(int(line[9]) - 1)  # __label__1, __label__2

        total_size += len(line[11:])
        if (total_size / 2 ** 20) > mib:
            break

    print("\t%d reviews" % len(X))
    print("\t%0.2f MiB of data" % (total_size / 2 ** 20))
    return X, y


@click.command()
@click.option('--backend', default='loky', help='Joblib backend to perform grid search '
                                                '(loky | lithops | dask | ray | tune)')
@click.option('--address', default=None, help='Scheduler address (dask) or head node address '
                                              '(ray, ray[tune])')
@click.option('--mib', default=10, type=int, help='Load X MiB from the dataset')
@click.option('--refit', default=False, is_flag=True, help='Fit the final model with the best '
                                                           'configuration and print score')
def main(backend, address, mib, refit):

    X, y = load_data(mib)

    n_features = 2 ** 18
    pipeline = Pipeline([
        ('vect', HashingVectorizer(n_features=n_features, alternate_sign=False)),
        ('clf', SGDClassifier()),
    ])

    parameters = {
        'vect__norm': ('l1', 'l2'),
        'vect__ngram_range': ((1, 1), (1, 2)),
        'clf__alpha': (1e-2, 1e-3, 1e-4, 1e-5),
        'clf__max_iter': (10, 30, 50, 80),
        'clf__penalty': ('l2', 'l1', 'elasticnet')
    }

    if backend == 'lithops':
        from sklearn.model_selection import GridSearchCV
        from lithops.util.joblib import register_lithops
        register_lithops()
        grid_search = GridSearchCV(pipeline, parameters,
                                   error_score='raise',
                                   refit=refit, cv=5, n_jobs=-1)

    elif backend == 'ray':
        from sklearn.model_selection import GridSearchCV
        import ray
        from ray.util.joblib import register_ray
        address = 'auto' if address is None else address
        ray.init(address, redis_password='5241590000000000')
        register_ray()
        grid_search = GridSearchCV(pipeline, parameters,
                                   error_score='raise',
                                   refit=refit, cv=5, n_jobs=-1)

    elif backend == 'tune':
        from tune_sklearn import TuneGridSearchCV
        import ray
        address = 'auto' if address is None else address
        ray.init(address, log_to_driver=False, redis_password='5241590000000000')
        grid_search = TuneGridSearchCV(pipeline, parameters,
            error_score='raise', refit=refit, cv=5, n_jobs=-1)
        backend = 'loky' # not used

    elif backend == 'dask':
        from dask_ml.model_selection import GridSearchCV
        from dask_ml.feature_extraction.text import HashingVectorizer as DaskHashingVectorizer
        from distributed import Client
        if address is None:
            print('Error: must specify a scheduler address for dask distributed')
            exit(1)
        Client(address=address)
        pipeline = Pipeline([
            ('vect', DaskHashingVectorizer(n_features=n_features, alternate_sign=False)),
            ('clf', SGDClassifier()),
        ])
        grid_search = GridSearchCV(pipeline, parameters,
            error_score='raise', refit=refit, cv=5, n_jobs=-1)

    else:   # loky
        from sklearn.model_selection import GridSearchCV
        grid_search = GridSearchCV(pipeline, parameters,
            error_score='raise', refit=refit, cv=5, n_jobs=-1)

    print("pipeline:", [name for name, _ in pipeline.steps])
    print("parameters: ", end='')
    pprint(parameters)

    with joblib.parallel_backend(backend):
        print("Performing grid search...")
        t0 = time()
        grid_search.fit(X, y)
        total_time = time() - t0
        print("Done in %0.3fs\n" % total_time) 

    if refit:
        print("Best score: %0.3f" % grid_search.best_score_)
        print("Best parameters set:")
        best_parameters = grid_search.best_estimator_.get_params()
        for param_name in sorted(parameters.keys()):
            print("\t%s: %r" % (param_name, best_parameters[param_name]))


if __name__ == "__main__":
    main()
