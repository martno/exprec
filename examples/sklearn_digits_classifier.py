from sklearn import datasets
from sklearn import svm
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
import numpy as np
import click
import pickle
from exprec import Experiment


@click.command()
@click.option('--C', default=100.0, show_default=True, help="SVM's penalty parameter C")
@click.option('--kernel', default='rbf', type=click.Choice(['linear', 'poly', 'rbf', 'sigmoid']), 
    show_default=True, help="Kernel type to be used in the SVM algorithm")
def main(c, kernel):
    with Experiment(title='Train digit classifier') as experiment:
        experiment.set_parameter('C', c)
        experiment.set_parameter('kernel', kernel)

        random_state = np.random.RandomState(1)

        dataset = datasets.load_digits()
        X_train, X_test, y_train, y_test = train_test_split(dataset.data, dataset.target, random_state=random_state)

        svc = svm.SVC(C=c, kernel=kernel)
        gammas = np.logspace(-4, 0, 5)
        clf = GridSearchCV(estimator=svc, param_grid={'gamma': gammas}, verbose=3)
        clf.fit(X_train, y_train)

        predicted = clf.predict(X_test)
        accuracy = accuracy_score(y_true=y_test, y_pred=predicted)

        print('Accuracy:', accuracy)
        experiment.add_scalar('accuracy', accuracy)

        with experiment.open('model.pkl', mode='wb') as f:
            pickle.dump(clf, f)


if __name__ == "__main__":
    main()
