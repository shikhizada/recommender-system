import numpy as np
import pandas as pd

from sklearn.tree import DecisionTreeClassifier

from src.models import *
from src.enums import *


import pdb
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

def dt_score(dt_input):
    categories = [TraceLabel.FALSE.value, TraceLabel.TRUE.value]

    X = pd.DataFrame(dt_input.encoded_data, columns=dt_input.features)
    y = pd.Categorical(dt_input.labels, categories=categories)
    dtc = DecisionTreeClassifier(class_weight=None, random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    dtc.fit(X_train, y_train)
    y_pred = dtc.predict(X_test)
    # np.sum(y.to_numpy())
    return f1_score(y_test, y_pred)


def generate_decision_tree_paths(dt_input, target_label):
    categories = [TraceLabel.FALSE.value, TraceLabel.TRUE.value]

    X = pd.DataFrame(dt_input.encoded_data, columns=dt_input.features)
    y = pd.Categorical(dt_input.labels, categories=categories)
    dtc = DecisionTreeClassifier(class_weight=None, random_state=0)
    dtc.fit(X, y)

    # find paths
    print("Finding decision tree paths ...")
    left = dtc.tree_.children_left
    right = dtc.tree_.children_right
    features = [dt_input.features[i] for i in dtc.tree_.feature]
    leaf_ids = np.argwhere(left == -1)[:, 0]
    if target_label == TraceLabel.TRUE:
        leaf_ids_positive = filter(
            lambda leaf_id: dtc.tree_.value[leaf_id][0][0] < dtc.tree_.value[leaf_id][0][1], leaf_ids)
    else:
        leaf_ids_positive = filter(
            lambda leaf_id: dtc.tree_.value[leaf_id][0][0] > dtc.tree_.value[leaf_id][0][1], leaf_ids)

    def recurse(left, right, child, lineage=None):
        if lineage is None:
            lineage = []
        if child in left:
            parent = np.where(left == child)[0].item()
            state = TraceState.VIOLATED
        else:
            parent = np.where(right == child)[0].item()
            state = TraceState.SATISFIED

        lineage.append((features[parent], state))

        if parent == 0:
            lineage.reverse()
            return lineage
        else:
            return recurse(left, right, parent, lineage)

    paths = []
    for leaf_id in leaf_ids_positive:
        rules = []
        for node in recurse(left, right, leaf_id):
            rules.append(node)
        if target_label == TraceLabel.TRUE:
            num_samples = {
                "negative": dtc.tree_.value[leaf_id][0][0],
                "positive": dtc.tree_.value[leaf_id][0][1],
                "total": dtc.tree_.value[leaf_id][0][0] + dtc.tree_.value[leaf_id][0][1]
            }
        else:
            num_samples = {
                "negative": dtc.tree_.value[leaf_id][0][1],
                "positive": dtc.tree_.value[leaf_id][0][0],
                "total": dtc.tree_.value[leaf_id][0][0] + dtc.tree_.value[leaf_id][0][1]
            }
        path = PathModel(
            impurity=dtc.tree_.impurity[leaf_id],
            num_samples=num_samples,
            rules=rules
        )
        paths.append(path)
    return paths
