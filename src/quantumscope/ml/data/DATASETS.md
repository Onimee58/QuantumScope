# Datasets bundled with QuantumScope

QuantumScope's code is MIT-licensed. The datasets in this folder are **not** covered by that licence: each keeps its own licence, listed below, and is redistributed under its terms with attribution. They are used offline, for teaching quantum machine learning.

| File | Dataset | Licence | Source and citation |
|---|---|---|---|
| iris.npz | Iris: 150 samples, 4 features, 3 classes | CC BY 4.0 | Fisher, R. (1936). Iris [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C56C76 |
| wine.npz | Wine: 178 samples, 13 features, 3 classes | CC BY 4.0 | Aeberhard, S. & Forina, M. (1992). Wine [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5PC7J |
| breast_cancer.npz | Breast Cancer Wisconsin (Diagnostic): 569 samples, 30 features, 2 classes | CC BY 4.0 | Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin (Diagnostic) [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B |
| digits.npz | Optical Recognition of Handwritten Digits, test set: 1,797 images, 8×8, 10 classes | CC BY 4.0 | Alpaydin, E. & Kaynak, C. (1998). Optical Recognition of Handwritten Digits [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C50P49 |
| mnist.npz | MNIST, a subset: the first 200 images of each digit from the 10,000-image test set (2,000 images, 28×28); `index` gives each image's position in the original test set | CC BY-SA 3.0 | LeCun, Y., Cortes, C., & Burges, C. J. C. The MNIST database of handwritten digits. Copyright © Yann LeCun and Corinna Cortes. |

**Licences:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ · CC BY-SA 3.0, https://creativecommons.org/licenses/by-sa/3.0/

**About the MNIST subset:** mnist.npz is an adaptation of the MNIST database and is itself licensed under CC BY-SA 3.0. Its source files (t10k-images-idx3-ubyte.gz and t10k-labels-idx1-ubyte.gz) were verified against their official MD5 checksums (9fb629c4189551a2d022fa330f9573f3 and ec29112dd5afa0611ce80d1b7f02629c) before the subset was made.

**How the files were made:** the four UCI datasets come from the copies distributed with scikit-learn 1.9.1. They were checked against the UCI Repository's published sample and class counts (for example Iris 50/50/50, Wine 59/71/48, Breast Cancer 212 malignant / 357 benign, and the Digits test set's per-digit counts), and saved unchanged as NumPy .npz files.
