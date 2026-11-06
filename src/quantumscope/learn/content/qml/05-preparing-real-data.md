---
title: Preparing real data
area: qml
kind: lecture
order: 5
objectives: Explain why real data rarely fits a quantum model as it is | Use PCA to reduce features to qubits | Explain why preprocessing is fitted on the training data only
math: 06-probability, 05-eigenvalues
---
# Preparing real data

Built-in toy datasets fit a quantum model as they are; real data almost never does. The **Datasets** experiment checks a dataset, says what stands in the way, and suggests a fix for each problem.

## What the checker looks for

| Problem | Why it matters | The usual fix |
|---|---|---|
| more features than qubits | one feature per qubit | **PCA**, or choosing features |
| many samples | a kernel compares every pair: $N^2$ circuits | balanced **subsampling** |
| more than two classes | this version separates two | choose **two classes** |
| text columns | circuits need numbers | encode as numbers, or drop |
| missing values | a gap has no angle | drop those samples, or fill with the mean |
| different scales | angles must lie in $[0, \pi]$ | **scale** each feature |

## PCA: from pixels to qubits

An MNIST image has 784 pixels, far more than ten qubits. **Principal component analysis** finds the directions in which the data varies most: the eigenvectors of the data's covariance matrix, with the largest eigenvalues first. Keeping the first $k$ components replaces 784 numbers by $k$ while keeping as much of the variation as possible. For MNIST 0s and 1s, 4 components keep about half of the variance, which is plenty to tell them apart.

Some pixels, near the image borders, are always black; they carry no information and are dropped first.

## Fit on the training data only

Every learned step (the column means for missing values, the PCA directions, the scaling range) is computed from the **training** split only, and then applied unchanged to the test split. Computing them from all the data would let information about the test points leak into the model, and the test accuracy would look better than it really is. This is called **data leakage**, and QuantumScope's preparation avoids it by splitting first.

## Your own data

**Import CSV or .npz…** reads your own files: a CSV with a header (the label column is found by name, such as *label*, *target* or *class*, or is the last column), or a NumPy file with arrays named X and y. The checker then works on it like any built-in dataset.

[Try it: check and prepare MNIST in the Datasets experiment](qs:open/qml_datasets)

## Check your understanding

```quiz
Q: Why are the PCA directions computed from the training data only?
* So that no information from the test points leaks into the model
- Because the test data has no labels
- Because PCA needs exactly 150 points
E: The test set must stay unseen until it is used for the score; fitting any step on it makes the score optimistic.
```

```quiz
Q: A dataset has 30 features and you have 4 qubits. What does the checker suggest?
- Use the first 4 columns
* Reduce to 4 features with PCA
- Use 30 qubits
E: PCA keeps the 4 directions of greatest variation, usually far more informative than the first 4 columns.
```

## Summary

- Real data needs fixing first: features to qubits, samples, classes, text, gaps and scales.
- PCA keeps the directions of greatest variation.
- Fit every step on the training data only, to avoid leakage.
