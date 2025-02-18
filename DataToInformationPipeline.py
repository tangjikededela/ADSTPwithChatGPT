import numpy as np
import pandas as pd
import statistics
from pycaret import classification
from pycaret import regression
import matplotlib.pyplot as plt
from pandas import DataFrame
from itertools import islice
import heapq
import pwlf
from GPyOpt.methods import BayesianOptimization
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from iteration_utilities import duplicates, unique_everseen
from scipy.signal import argrelextrema
from sklearn import ensemble
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn import metrics
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeClassifier
from sklearn.decomposition import PCA
from sklearn.metrics import r2_score,mean_squared_error, silhouette_score, calinski_harabasz_score, davies_bouldin_score,accuracy_score,accuracy_score, confusion_matrix,precision_score, recall_score, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import cross_val_score
from pygam import LinearGAM, s, f, te
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import mutual_info_classif
import statsmodels.api as sm
import scipy.signal as signal
import math
import cv2
import shap


def NormalizeData(data):
    """This function takes in as input a dataset, and returns a normalized dataset with values between 0 and 1.

    :param data: This is the dataset that will be normalized.
    :return: A dataset that has normalized values.
    """
    x = data.values  # returns a numpy array
    scaler = preprocessing.MinMaxScaler()
    scaled_x = scaler.fit_transform(x)
    data = pd.DataFrame(scaled_x, columns=data.columns)
    return data

def cleanData(data, threshold):
    """This function takes in as input a dataset, and returns a clean dataset.

    :param data: This is the dataset that will be cleaned.
    :param treshold: This is the treshold that decides whether columns are deleted or their missing values filled.
    :return: A dataset that does not have any missing values.
    """
    data = data.replace('?', np.nan)
    data = data.loc[:, data.isnull().mean() < threshold]  # filter data
    imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
    for i in data.columns:
        imputer = imputer.fit(data[[i]])
        data[[i]] = imputer.transform(data[[i]])
    return data

def create_dummy_variables(dataset, variables):
    for var in variables:
        cat_list = 'var' + '_' + var
        cat_list = pd.get_dummies(dataset[var], prefix=var)
        datatemp = dataset.join(cat_list)
        dataset = datatemp
    data_vars = dataset.columns.values.tolist()
    to_keep = [i for i in data_vars if i not in variables]
    data_final = dataset[to_keep]
    return (data_final)

def remove_outliers(dataset,Xcol,ycol,testsize=0.33):
    X = dataset[Xcol].values
    y = dataset[ycol].values
    # split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=testsize, random_state=1)
    # identify outliers in the training dataset
    lof = LocalOutlierFactor()
    yhat = lof.fit_predict(X_train)
    # select all rows that are not outliers
    mask = yhat != -1
    X_train, y_train = X_train[mask, :], y_train[mask]
    # Set data back
    cleandataset = pd.DataFrame(X_train, columns=Xcol)
    cleandataset[ycol] = y_train
    return (cleandataset)

def RenderModel(model_type, X_train, y_train):  # Renders a model based on model name and X_train and Y_train values

    if model_type == 'Gradient Boosting Regressor':
        result = ensemble.GradientBoostingRegressor(n_estimators=500, max_depth=4, min_samples_split=2,
                                                    learning_rate=0.1)
        result.fit(X_train, y_train)
    elif model_type == 'Random Forest Regressor':
        result = RandomForestRegressor(n_estimators=500, random_state=0)
        result.fit(X_train, y_train)
    elif model_type == 'Linear Regression':
        result = LinearRegression()
        result.fit(X_train, y_train)
    elif model_type == 'Decision Tree Regressor':
        result = DecisionTreeRegressor(random_state=0)
        result.fit(X_train, y_train)
    elif model_type == 'GAMs':
        X = X_train
        y = y_train
        lams = np.random.rand(100, X.shape[1])  # Epochs
        lams = lams * X.shape[1] - 3
        lams = np.exp(lams)
        result = LinearGAM(n_splines=X.shape[1] + 5).gridsearch(X, y, lam=lams)
    return result


def R2(renderdModel, X_test, y_test):
    y_predict = renderdModel.predict(X_test)
    r_square = metrics.r2_score(y_test, y_predict)
    return r_square


def MAE(renderdModel, X_test, y_test):
    y_predict = renderdModel.predict(X_test)
    mae = metrics.mean_absolute_error(y_test, y_predict)
    return mae


def RMSE(renderdModel, X_test, y_test):
    y_predict = renderdModel.predict(X_test)
    rmse = metrics.mean_squared_error(y_test, y_predict, squared=False)
    return rmse

def LinearSKDefaultModel(X, y, Xcol):
    # use sm for P-values
    X = sm.add_constant(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    smmodel = sm.OLS(y_train, X_train).fit()

    y = y.values.reshape(-1, 1)
    # perform linear regression
    model = LinearRegression().fit(X, y)

    # get the coefficient
    coef = model.coef_
    columns = {'coeff': coef[0][1:], 'pvalue': smmodel.pvalues.round(4).values[1:]}
    linearData = DataFrame(data=columns, index=Xcol)
    # calculate the r-squared value
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    return (columns, linearData, r2)

def LinearDefaultModel(X, y, Xcol):
    X = sm.add_constant(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    model = sm.OLS(y_train, X_train).fit()
    # Create DataFrame with results from model
    columns = {'coeff': model.params.values[1:], 'pvalue': model.pvalues.round(4).values[1:]}
    linearData = DataFrame(data=columns, index=Xcol)
    predicted = model.predict(X_test)
    mse = mean_squared_error(y_test, predicted)
    rmse = mse ** (1 / 2.0)
    r2 = model.rsquared

    return (columns, linearData, predicted, mse, rmse, r2)

def LogisticrDefaultModel(X, y, Xcol):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    model = sm.Logit(y_train, X_train).fit()
    # predictions = model.predict(X_test)
    # accuracy = accuracy_score(y_test, predictions)
    # Create DataFrame with results from model
    columns1 = {'coeff': model.params.values, 'pvalue': model.pvalues.round(4).values}
    logisticData1 = DataFrame(data=columns1, index=Xcol)
    r2 = model.prsquared
    logisticRegr = LogisticRegression()
    logisticRegr.fit(X_train, y_train)

    deviance = 2 * logisticRegr.score(X, y) * len(y)  # 2*(-log-likelihood of fitted model)
    df = len(y) - logisticRegr.coef_.shape[1] - 1
    devDdf = deviance / df

    columns2 = {'importance score': abs(model.params.values)}
    logisticData2 = DataFrame(data=columns2, index=Xcol)
    return (columns1, logisticData1, columns2, logisticData2, devDdf)


def GradientBoostingDefaultModel(X, y, Xcol, gbr_params):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    model = ensemble.GradientBoostingRegressor(**gbr_params)
    model.fit(X_train, y_train)
    model.score(X_test, y_test)
    mse = mean_squared_error(y_test, model.predict(X_test))
    rmse = mse ** (1 / 2.0)
    r2 = model.score(X_test, y_test)
    importance = model.feature_importances_
    train_errors = []
    test_errors = []

    for i, y_pred in enumerate(model.staged_predict(X_train)):
        if i % 10 == 0:
            mse_train = mean_squared_error(y_train, y_pred)
            train_errors.append(np.round(mse_train,3))
            y_pred_test = model.staged_predict(X_test)
            mse_test = mean_squared_error(y_test, next(islice(y_pred_test, i + 1)))
            test_errors.append(np.round(mse_test,3))
    columns = {'important': importance}
    DTData = DataFrame(data=columns, index=Xcol)
    imp = ""
    for ind in DTData.index:
        if DTData['important'][ind] == max(DTData['important']):
            imp = ind
    return (model, mse, rmse, r2, imp,train_errors,test_errors,DTData)


def RandomForestDefaultModel(X, y, Xcol, n_estimators, max_depth):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    # Limit depth of tree to 3 levels
    rf_small = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth)
    rf_small.fit(X_train, y_train)
    # Extract the small tree
    tree_small = rf_small.estimators_[5]
    # R2
    r2 = rf_small.score(X_train, y_train)
    # Use the forest's predict method on the test data
    predictions = rf_small.predict(X_test)
    # Calculate the absolute errors
    errors = abs(predictions - y_test)
    # Calculate mean absolute percentage error (MAPE)
    mape = 100 * (abs(predictions - y_test) / y_test)
    # Calculate and display accuracy
    accuracy = 100 - np.mean(mape)
    mae = metrics.mean_absolute_error(y_test, predictions)
    mse = metrics.mean_squared_error(y_test, predictions)
    rmse = mse ** (1 / 2.0)
    importance = rf_small.feature_importances_
    columns = {'important': importance}
    DTData = DataFrame(data=columns, index=Xcol)
    return (tree_small, rf_small, DTData, r2, mse, rmse)


def DecisionTreeDefaultModel(X, y, Xcol, max_depth):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    model = DecisionTreeRegressor(random_state=0, max_depth=max_depth)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    r2 = model.score(X_train, y_train)
    mse = mean_squared_error(y_test, predictions)
    rmse = mse ** (1 / 2.0)
    importance = model.feature_importances_
    columns = {'important': importance}
    DTData = DataFrame(data=columns, index=Xcol)

    return (model, r2, mse, rmse, DTData)


def GAMModel(data, Xcol, ycol, X, y, expect=1, epochs=100, splines='', chatGPT=0):
    titles = Xcol
    n = np.size(titles)
    # Fitting the model
    lams = np.random.rand(epochs, np.size(titles))  # Epochs
    lams = lams * np.size(titles) - 3
    lams = np.exp(lams)
    if splines == '':
        splines = n + 5
    gam = LinearGAM(n_splines=splines).gridsearch(X, y, lam=lams)
    r2 = gam.statistics_.get('pseudo_r2')
    p = gam.statistics_.get('p_values')
    # Plotting
    factor = ""
    mincondition = ""
    condition = ""
    choose = expect
    conflict = [0] * np.size(Xcol)
    message = []
    # print(gam.summary())
    coefficients = gam.coef_
    equation = "y = "
    for i in range(len(coefficients)):
        term = " + " if i > 0 else ""
        term += f"{coefficients[i]:.4f} * f{i}(x{i})"
        equation += term
    # print (equation)
    # Analysis and Story Generate
    for i in range(len(Xcol)):
        maxfirst = 0
        minfirst = 0
        XX = gam.generate_X_grid(term=i)
        Xpre = XX[:, i]
        ypre = gam.partial_dependence(term=i, X=XX)
        Xpre = np.round(Xpre, 3)
        ypre = np.around(ypre, 3)
        message.append("when " + Xcol[i] + " is " + str(Xpre) + ", the " + ycol + " is " + str(ypre) + ".")
        # Find min & max
        maxpoint = signal.argrelextrema(gam.partial_dependence(term=i, X=XX), np.greater)
        minpoint = signal.argrelextrema(gam.partial_dependence(term=i, X=XX), np.less)
        maxpoint = maxpoint[0]
        minpoint = minpoint[0]
        extremum = 0
        loopnum = int(np.size(minpoint)) + int(np.size(maxpoint))
        allpoint = np.hstack((maxpoint, minpoint))
        allpoint.sort()
        if np.size(maxpoint) != 0 and np.size(minpoint) != 0:
            if maxpoint[0] > minpoint[0] and minpoint[0] > 0:
                minfirst = 1
            elif maxpoint[0] < minpoint[0] and maxpoint[0] > 0:
                maxfirst = 1
            for j in range(loopnum):

                if j == 0:
                    if minfirst == 1:
                        factor = "With the growth of  " + Xcol[
                            i] + " , " + ycol + " first decreases to "
                        if ypre[minpoint[0]] == min(ypre):
                            factor = factor + "the minimum when " + Xcol[i] + " is " + str(
                                round(Xpre[minpoint[0]], 3))
                            mincondition = mincondition + Xcol[i] + " is around " + str(
                                round(Xpre[minpoint[0]], 3)) + ", "
                            extremum = 1
                        else:
                            factor = factor + "a relative minimum"
                    elif maxfirst == 1:
                        factor = "With the growth of  " + Xcol[i] + " , " + ycol + " first increases to "
                        if ypre[maxpoint[0]] == max(ypre):
                            factor = factor + "the maximum when " + Xcol[i] + " is " + str(
                                round(Xpre[maxpoint[0]], 3))
                            condition = condition + Xcol[i] + " is around " + str(
                                round(Xpre[maxpoint[0]], 3)) + ", "
                            extremum = 1
                        else:
                            factor = factor + "a relative maximum"
                elif j != 0:
                    if maxfirst == 1:
                        minfirst = 1
                        maxfirst = 0
                        if ypre[allpoint[j]] == min(ypre):
                            factor = factor + "\nthen decreases to the minimum when " + Xcol[
                                i] + " is " + str(round(Xpre[allpoint[j]], 3))
                            mincondition = mincondition + Xcol[i] + " is around " + str(
                                round(Xpre[allpoint[j]], 3)) + ", "
                            extremum = 1
                        else:
                            factor = factor + "\nthen decreases to a relative minimum."
                    elif minfirst == 1:
                        maxfirst = 1
                        minfirst = 0
                        if ypre[allpoint[j]] == max(ypre):
                            factor = factor + "\nthen increases to the maximum when " + Xcol[
                                i] + " is " + str(round(Xpre[allpoint[j]], 3))
                            condition = condition + Xcol[i] + " is around " + str(
                                round(Xpre[allpoint[j]], 3)) + ", "
                            extremum = 1
                        else:
                            factor = factor + "\nthen increases to a relative maximum."
            if allpoint[loopnum - 1] in maxpoint:
                factor = factor + " and finally continues to decline."
                if extremum == 0 and choose == 0:
                    condition = condition + Xcol[i] + " the less the better, "
                    # need change here
                    if ypre[0] > ypre[len(ypre) - 1]:
                        mincondition = mincondition + Xcol[i] + " the higher the better, "
                    else:
                        mincondition = mincondition + Xcol[i] + " the less the better, "
                elif extremum == 0 and choose == 1:
                    if ypre[0] > ypre[len(ypre) - 1]:
                        mincondition = mincondition + Xcol[i] + " the higher the better, "
                    else:
                        mincondition = mincondition + Xcol[i] + " the less the better, "
                elif extremum == 1 and choose == 1:
                    if ypre[0] > ypre[len(ypre) - 1]:
                        mincondition = mincondition + " or " + Xcol[i] + " the higher the better, "
                    elif ypre[0] <= min(ypre):
                        mincondition = mincondition + "or" + Xcol[i] + " the less the better, "
                elif extremum == 1 and choose == 0:
                    if ypre[0] > ypre[len(ypre) - 1]:
                        mincondition = mincondition + Xcol[i] + " the higher the better, "
                    else:
                        mincondition = mincondition + Xcol[i] + " the less the better, "
            else:
                factor = factor + " and finally continues to increase."
                if extremum == 0 and choose == 0:
                    condition = condition + Xcol[i] + " the higher the better, "
                    mincondition = mincondition + Xcol[i] + " the less the better, "
                elif extremum == 0 and choose == 1:
                    mincondition = mincondition + Xcol[i] + " the less the better, "
                elif extremum == 1 and choose == 1:
                    mincondition = mincondition + Xcol[i] + " the less the better, "
                elif extremum == 1 and choose == 0:
                    mincondition = mincondition + Xcol[i] + " the less the better, "
        elif np.size(maxpoint) != 0 and np.size(minpoint) == 0:
            factor = "With the growth of  " + Xcol[
                i] + " , the " + ycol + " first increases to the maximum when " + Xcol[i] + " is " + str(round(
                Xpre[maxpoint][0], 3)) + " then continues to decline."
            condition = condition + Xcol[i] + " is around " + str(round(Xpre[maxpoint][0], 3)) + ", "
            if ypre[0] > ypre[len(ypre) - 1]:
                mincondition = mincondition + Xcol[i] + " the higher the better, "
            else:
                mincondition = mincondition + Xcol[i] + " the less the better, "
        elif np.size(maxpoint) == 0 and np.size(minpoint) != 0:
            mincondition = mincondition + Xcol[i] + " is around " + str(round(Xpre[minpoint][0], 3)) + ", "
            factor = "With the growth of  " + Xcol[
                i] + " , the " + ycol + " first decreases to the minimum when " + Xcol[i] + " is " + str(round(
                Xpre[minpoint][0], 3)) + " then continues to increase."
        elif np.size(maxpoint) == 0 and np.size(minpoint) == 0:
            if ypre[0] < ypre[np.size(ypre) - 1]:
                factor = ycol + " keep increase as " + Xcol[i] + " increase."
                condition = condition + Xcol[i] + " the larger the better, "
                mincondition = mincondition + Xcol[i] + " the less the better, "
            else:
                factor = ycol + " keep decreases as " + Xcol[i] + " increase."
                condition = condition + Xcol[i] + " the less the better, "
                mincondition = mincondition + Xcol[i] + " the higher the better, "
        if np.size(minpoint) >= 2 and np.size(maxpoint) >= 2:
            factor = factor + " It is worth noting that as " + Xcol[
                i] + " increases, " + ycol + " tends to fluctuate periodically."
        # ax.plot(XX[:, i], gam.partial_dependence(term=i, X=XX))
        # ax.plot(XX[:, i], gam.partial_dependence(term=i, X=XX, width=.95)[1], c='r', ls='--')
        # ax.set_title(Xcol[i])
        conflict[i] = factor
    nss = ""
    ss = ""
    #message = message + " By comparing the above data, If "+str(Xcol)+ " are independent variables, "+ycol+" is dependent variable, under what circumstances the "+ycol+" could be as high as possible?"
    for i in range(np.size(p) - 1):
        p[i] = round(p[i], 3)
        if p[i] > 0.05:
            nss = nss + "the " + Xcol[i] + ", "
        else:
            ss = ss + "the " + Xcol[i] + ", "
    # print(message)
    return (gam, data, Xcol, ycol, r2, p, conflict, nss, ss, mincondition, condition,message)

def RidgeClassifierModel(dataset, Xcol, ycol,class1,class2):
    X = dataset[Xcol]
    y = dataset[ycol]
    y = y.map({class1: 0, class2: 1})
    # Split the data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Instantiate the RidgeClassifier model
    rclf = RidgeClassifier()

    # Fit the model to the training data
    rclf.fit(X_train, y_train)

    # Make predictions on the test data
    y_pred = rclf.predict(X_test)

    # Compute accuracy, precision, recall, F1-score
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    # Compute area under the ROC curve
    y_prob = rclf.decision_function(X_test)
    roc_auc = roc_auc_score(y_test, y_prob)

    # Perform PCA for dimensionality reduction
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_test)

    # Compute feature importances
    importances = rclf.coef_[0]

    return (rclf,pca,y_test, y_prob,roc_auc,X_pca,accuracy,importances)


def KNeighborsClassifierModel(dataset, Xcol, ycol,Knum=3,cvnum=5):
    # Extract the feature matrix X and target vector y
    X = dataset[Xcol]
    y = dataset[ycol]
    # Split the data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Instantiate the K Neighbors Classifier model
    k = Knum  # Number of neighbors to consider
    clf = KNeighborsClassifier(n_neighbors=k)
    # Fit the model to the training data
    clf.fit(X_train, y_train)
    # Make predictions on the test data
    y_pred = clf.predict(X_test)
    # Compute accuracy, precision, recall, F1-score
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    # Calculate mutual information between each feature and the target variable
    feature_importances = mutual_info_classif(X, y)
    # Calculate confusion matrix
    confusionmatrix = confusion_matrix(y_test, y_pred)
    # Calculate cross-validation scores
    cv_scores = cross_val_score(clf, X, y, cv=cvnum)
    return (accuracy,precision,feature_importances,recall,f1,confusionmatrix,cv_scores)

def SVCClassifierModel(dataset, Xcol, ycol,kernel='linear', C=1.0,cvnum=5):
    # Extract the feature matrix X and target vector y
    X = dataset[Xcol]
    y = dataset[ycol]
    # Split the data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Instantiate the Support Vector Machine (SVM) model
    clf = SVC(kernel=kernel, C=C)  # Linear kernel with regularization parameter C=1.0
    # Fit the model to the training data
    clf.fit(X_train, y_train)
    # Make predictions on the test data
    y_pred = clf.predict(X_test)
    # Compute accuracy, precision, recall, F1-score
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    # Calculate confusion matrix
    confusionmatrix = confusion_matrix(y_test, y_pred)
    cv_scores = cross_val_score(clf, X, y, cv=cvnum)  # 5-fold cross-validation
    return (accuracy,precision,recall,f1,confusionmatrix,cv_scores)

def kmeanclustermodel(Xcol, df_agg,minnum_clusters=1,maxnum_clusters=11,n_clusters=5):
    # Select features for segmentation
    X = df_agg[Xcol].values

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Determine optimal number of clusters
    wcss = []
    for i in range(minnum_clusters, maxnum_clusters):
        kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42)
        kmeans.fit(X_scaled)
        wcss.append(kmeans.inertia_)

    # find the elbow point
    diffs = np.diff(wcss)
    diffs_ratio = diffs[1:] / diffs[:-1]
    elbow_point = np.argmin(diffs_ratio) + 1

    # store the optimal number of clusters
    best_n_clusters = elbow_point + 1

    # Apply k-means clustering
    n_clusters = n_clusters
    kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42)
    y_pred = kmeans.fit_predict(X_scaled)

    # Print summary statistics by cluster
    summary = df_agg.groupby('Cluster').agg({col: 'sum' for col in Xcol})
    print(summary)

    # Calculate and print clustering performance metrics
    silhouette_score_value = silhouette_score(X_scaled, y_pred)
    calinski_harabasz_score_value = calinski_harabasz_score(X_scaled, y_pred)
    davies_bouldin_score_value = davies_bouldin_score(X_scaled, y_pred)

    print('Silhouette Score: {:.3f}'.format(silhouette_score_value))
    print('Calinski Harabasz Score: {:.3f}'.format(calinski_harabasz_score_value))
    print('davies bouldin score: {:.3f}'.format(davies_bouldin_score_value))

    return (wcss,summary,best_n_clusters,silhouette_score_value,calinski_harabasz_score_value,davies_bouldin_score_value)

def loop_mean_compare(dataset, Xcol, ycol):
    diff = [0] * np.size(Xcol)
    i = 0
    for ind in Xcol:
        diff[i] = (statistics.mean(dataset[ind]) - statistics.mean(dataset[ycol]))
        i = i + 1
    return (diff)


def find_row_n_max(dataset, Xcol, r=0, max_num=5):
    row_data = dataset[Xcol].values[0:r + 1][r]
    max_data = (heapq.nlargest(max_num, row_data))
    max_factor = []
    for ind in Xcol:
        if dataset[ind].values[0:r + 1][r] in max_data:
            max_factor.append(ind)
    return (max_factor)


def detect_same_elements(list1, list2):
    same_element = 0
    for i in list1:
        if i in list2:
            same_element = same_element + 1
    return (same_element)


def select_one_element(dataset, Xcol, ycol):
    datasize = np.size(dataset[Xcol])
    y = dataset[ycol].values[0:datasize][datasize - 1]
    X = dataset[Xcol].values[0:datasize][datasize - 1]
    return (X, y)


def find_all_zero_after_arow(dataset, Xcol, ycol):
    period = dataset[ycol]
    zero_lastdata = ""
    for ind in Xcol:
        remain_num = dataset[ind].values
        for i in range(np.size(remain_num)):
            if remain_num[i] == 0:
                zero_lastdata = period[i]
    return (zero_lastdata)


def find_column_mean(dataset):
    meancol = statistics.mean(dataset)
    return (meancol)


def simple_trendy(ydata, Xdata):
    maxloc = []
    minloc = []
    for i in range(len(ydata)):
        if ydata[i] == max(ydata):
            maxloc.append(i)
        elif ydata[i] == min(ydata):
            minloc.append(i)
    if len(maxloc) != 1:
        XforMaxy = []
        for j in maxloc:
            XforMaxy.append(Xdata[j])
    else:
        XforMaxy = Xdata[maxloc[0]]
    if len(minloc) != 1:
        XforMiny = []
        for j in minloc:
            XforMiny.append(Xdata[j])
    else:
        XforMiny = Xdata[minloc[0]]

    return XforMaxy, XforMiny


class NonFittingReport:
    # Include several simple data comparison methods
    def dependentcompare(m, X, y1, y2, Xcolname, ycolname1, ycolname2, begin, end):
        if "magnificationcompare" in str(m):
            if begin == "":
                begin = 0
            if end == "":
                end = np.size(X) - 1
            magnification1 = math.floor(y1[begin] / y2[begin])
            magnification2 = round(y1[end] / y2[end], 1)
            X1 = X[begin]
            X2 = X[end]
            return (Xcolname, begin, end, ycolname1, ycolname2, magnification1, magnification2, X, X1, X2)
            # print(dc1.render(Xcol=Xcolname, begin=begin, end=end, loopnum=end, y1name=ycolname1, y2name=ycolname2,
            #                  magnification1=magnification1,
            #                  magnification2=magnification2, X=X, X1=X1, X2=X2))
        if "quantitycomparison" in str(m):
            if begin == "":
                begin = 0
            if end == "":
                end = np.size(X) - 1
            diff1 = round(y1[begin] - y2[begin], 2)
            diff2 = round(y1[end] - y2[end], 2)
            X1 = X[begin]
            X2 = X[end]
            return (Xcolname, begin, end, ycolname1, ycolname2, diff1, diff2, X, X1, X2)
            # print(dc3.render(Xcol=Xcolname, begin=begin, end=end, loopnum=end, y1name=ycolname1, y2name=ycolname2,
            #                  diff1=diff1, diff2=diff2, X=X, X1=X1, X2=X2))

    def independenttwopointcompare(m, X, Xcolname, y1, y2, ycolname1, ycolname2, point, mode):
        if "independenttwopointcomparison" in str(m):
            if mode == "":
                mode = "quantity"
            if point == "":
                point = np.size(X) - 1
            y1 = y1[point]
            y2 = y2[point]
            mag = np.round(y1 / y2, 2)
            return (Xcolname, point, ycolname1, ycolname2, X, y1, y2, mode, mag)
            # print(idtpc.render(Xcol=Xcolname, point=point, y1name=ycolname1, y2name=ycolname2, X=X, y1=y1, y2=y2,
            #                    mode=mode, mag=mag))

    def samedependentcompare(m, X, y, Xcolname, ycolname, begin, end):
        if "samedependentmagnificationcompare" in str(m):
            if begin == "":
                begin = 0
            if end == "":
                end = np.size(X) - 1
            magnification = round(y[end] / y[begin], 2)
            return (Xcolname, ycolname, begin, end, magnification, X, y)
            # print(dc2.render(Xcol=Xcolname, ycol=ycolname, begin=begin, end=end, magnification=magnification, X=X, y=y))
        elif "trenddescription" in str(m):
            Xmaxp = ""
            Xminp = ""
            story = ""
            maxpoint = argrelextrema(y.values, np.greater, order=1)[0]
            minpoint = argrelextrema(y.values, np.less, order=1)[0]
            for i in range(np.size(maxpoint)):
                if float(y[maxpoint[i]]) == max(y):
                    Xmaxp = X[maxpoint[i]]
            for i in range(np.size(minpoint)):
                if float(y[minpoint[i]]) == min(y):
                    Xminp = X[minpoint[i]]
            maxy = max(y)
            miny = min(y)
            # return (Xcolname, ycolname, X, Xmaxp, Xminp, y, begin, end, maxy, miny)
            # print(dct.render(Xcol=Xcolname, ycol=ycolname, X=X, Xmaxp=Xmaxp, Xminp=Xminp, y=y, begin=begin, end=end,
            #                  maxy=max(y), miny=min(y)))
            repeatvalue = list(unique_everseen(duplicates(y)))
            if repeatvalue != []:
                for i in range(np.size(repeatvalue)):
                    Xsamep = ""
                    for j in range(np.size(y) - 1):
                        if y[j] == repeatvalue[i] and y[j + 1] == repeatvalue[i]:
                            Xsamep = Xsamep + str(X[j]) + " "
                        elif y[j] == repeatvalue[i] and y[j - 1] == repeatvalue[i]:
                            Xsamep = Xsamep + str(X[j]) + " "
                        if j == np.size(y) - 2 and y[j] == repeatvalue[i] and y[j + 1] == repeatvalue[i]:
                            Xsamep = Xsamep + str(X[j + 1]) + " "
                    story = story + "In " + Xcolname + " " + Xsamep.split()[0] + " to " + Xsamep.split()[
                        np.size(Xsamep.split()) - 1] + " " + ycolname + " does not change much, it is around " + str(
                        repeatvalue[i]) + ". "
            return (Xcolname, ycolname, X, Xmaxp, Xminp, y, begin, end, maxy, miny, story)
            # print("In " + Xcolname + " " + Xsamep.split()[0] + " to " + Xsamep.split()[
            #     np.size(Xsamep.split()) - 1] + " " + ycolname + " does not change much, it is around " + str(
            #     repeatvalue[i]) + ".")
        elif "trendpercentage" in str(m):
            if begin == "":
                begin = 0
            if end == "":
                end = np.size(X) - 1
            ynew = [0] * (end - begin + 1)
            for i in range(end - begin + 1):
                ynew[i] = y[i + begin]
            std = np.std(ynew)
            samepoint = end - 1
            for i in range(end - begin + 1):
                if y[samepoint] == y[end]:
                    samepoint = samepoint - 1
            return (Xcolname, begin, end, ycolname, X, y, std, samepoint + 1)
            # print(dc4.render(Xcol=Xcolname, begin=begin, end=end, ycol=ycolname, X=X, y=y, std=std))

    def independentcompare(m, X, y, Xcolname, ycolname, begin, end):
        if "independentquantitycomparison" in str(m):
            X1 = X[begin]
            X2 = X[end]
            y1 = y[begin]
            y2 = y[end]
            return (Xcolname, ycolname, X, X1, X2, y1, y2)
            # print(idc1.render(Xcol=Xcolname, ycol=ycolname, X=X, X1=X1, X2=X2, y1=y1, y2=y2))

    def two_point_and_peak(m, X, y, Xcolname, ycolname, point1, point2):
        if "twopointpeak_child" in str(m):
            X1 = X[point1]
            X2 = X[point2]
            y1 = y[point1]
            y2 = y[point2]
            ypeak = max(y)
            for i in range(np.size(y)):
                if y[i] == ypeak:
                    Xpeak = X[i]
            return (Xcolname, ycolname, Xpeak, ypeak, X1, X2, y1, y2)
            # print(tppc.render(Xcol=Xcolname, ycol=ycolname, Xpeak=Xpeak, ypeak=ypeak, X1=X1, X2=X2, y1=y1, y2=y2))

    def batchprovessing(m, X, y, Xcolname, ycolnames, category_name, end, begin=0):
        if m == 1:
            allincrease = True
            alldecrease = True
            X1 = X[begin]
            X2 = X[end]
            for i in range(np.size(ycolnames) - 1):
                ycolname = ycolnames[i]
                ydata = y[ycolname]
                if ydata[end] > ydata[begin]:
                    alldecrease = False
                elif ydata[end] < ydata[begin]:
                    allincrease = False
            X1 = 0
            # return (m,Xcolname,X1,allincrease,alldecrease,category_name)
            # print(bp1.render(mode=m, Xcol=Xcolname, X1=0, allincrease=allincrease, alldecrease=alldecrease,
            #                  category_name=category_name))
            return (m, Xcolname, X1, X2, y, allincrease, alldecrease, category_name, ycolnames, begin, end)
            # story=""
            # for i in range(np.size(ycolnames) - 1):
            #     ycolname = ycolnames[i]
            #     ydata = y[ycolname]
            #     y1 = ydata[begin]
            #     y2 = ydata[end]
            #     story=story+bp2.render(mode=m, ycol=ycolname, y1=y1, y2=y2, X1=X1, X2=X2, mag=0)
            #   # print(bp2.render(mode=m, ycol=ycolname, y1=y1, y2=y2, X1=X1, X2=X2, mag=0))
            # return (m, Xcolname, X1, allincrease, alldecrease, category_name, story)
        elif m == 2:
            point = end
            X1 = X[point]
            allincrease = False
            alldecrease = False
            # return (m,Xcolname,X1,allincrease,alldecrease,category_name)
            # print(bp1.render(mode=m, Xcol=Xcolname, X1=X1, allincrease=False, alldecrease=False,
            #                  category_name=category_name))
            total = y[category_name][point]
            return (m, Xcolname, X1, allincrease, alldecrease, category_name, total, ycolnames, y, point)
            # story=""
            # for i in range(np.size(ycolnames) - 1):
            #     ycolname = ycolnames[i]
            #     ydata = y[ycolname]
            #     y1 = ydata[point]
            #     mag = np.round(y1 / total, 2)
            #     story=story+bp2.render(mode=m, ycol=ycolname, y1=y1, y2=0, X1=0, X2=0, mag=mag)
            #     # print(bp2.render(mode=m, ycol=ycolname, y1=y1, y2=0, X1=0, X2=0, mag=mag))
            # return (m, Xcolname, X1, allincrease, alldecrease, category_name,story)


def segmentedregressionsummary(X, y, Xcolname, ycolname, level, graph, base, r2, p, breakpointnum=1,
                               governmentdrug=False, governmentchild=False):
    my_pwlf = pwlf.PiecewiseLinFit(X, y)

    def my_obj(x):
        # define some penalty parameter l
        # you'll have to arbitrarily pick this
        # it depends upon the noise in your data,
        # and the value of your sum of square of residuals
        l = y.mean() * 0.001
        f = np.zeros(x.shape[0])
        for i, j in enumerate(x):
            my_pwlf.fit(j[0])
            f[i] = my_pwlf.ssr + (l * j[0])
        return f

    # define the lower and upper bound for the number of line segments
    bounds = [{'name': 'var_1', 'type': 'discrete',
               'domain': np.arange(2, 2 + breakpointnum)}]

    np.random.seed(12121)

    myBopt = BayesianOptimization(my_obj, domain=bounds, model_type='GP',
                                  initial_design_numdata=10,
                                  initial_design_type='latin',
                                  exact_feval=True, verbosity=True,
                                  verbosity_model=False)
    max_iter = 30

    # perform the bayesian optimization to find the optimum number of line segments
    myBopt.run_optimization(max_iter=max_iter, verbosity=True)
    #######
    # if graph == True:
    #     myBopt.plot_acquisition()
    #     myBopt.plot_convergence()

    # perform the fit for the optimum
    BP = my_pwlf.fit(myBopt.x_opt)
    slopes = my_pwlf.calc_slopes()
    BPNumber = int(myBopt.x_opt[0])
    rsq = my_pwlf.r_squared()
    pvalue = my_pwlf.p_values()
    R = [0] * BPNumber
    P = [0] * BPNumber
    # predict for the determined points
    xHat = np.linspace(min(X), max(X), num=1000)
    yHat = my_pwlf.predict(xHat)
    m = 1
    xSize = 0
    # plot the results
    if (graph == True):
        plt.figure()
        plt.plot(X, y, 'o')
        plt.plot(xHat, yHat, '-')
        plt.show()
    increasePart = " "
    decreasePart = " "
    notchangePart = " "
    maxIncrease = " "
    maxDecrease = " "
    strongRSSI = ""
    strongRNSSI = ""
    weakRSSI = ""
    weakRNSSI = ""
    begin1 = ""
    end1 = ""
    begin2 = ""
    end2 = ""
    X0 = X[0]
    for i in range(BPNumber):
        for n in range(len(X)):
            if X[n] <= BP[m] and X[n] >= X0:
                xSize = xSize + 1
        Xnew = [0] * (xSize)
        ynew = [0] * (xSize)
        l = 0
        for n in range(len(X)):
            if X[n] <= BP[m] and X[n] >= X0:
                Xnew[l] = X[n]
                ynew[l] = y[n]
                l = l + 1
        if len(Xnew) != 0 and len(ynew) != 0:
            Xnew, ynew = np.array(Xnew).reshape(-1, 1), np.array(ynew)
            modelfit = LinearRegression().fit(Xnew, ynew)
            R[m - 1] = modelfit.score(Xnew, ynew)
            Xnew2 = sm.add_constant(Xnew)
            est = sm.OLS(ynew, Xnew2)
            est2 = est.fit()
            if np.size(est2.pvalues) > 1:
                P[m - 1] = est2.pvalues[1]
            else:
                P[m - 1] = est2.pvalues[0]
        X0 = BP[m]
        m = m + 1
        xSize = 0
    # print(R)
    # print(P)
    # print(pvalue)
    for i in range(BPNumber):
        if slopes[i] < 0:
            if i > 0:
                temporary1 = decreasePart
            decreasePart = decreasePart + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
            temporary2 = "over " + str(np.round(BP[i], 0)) + " to " + str(np.round(BP[i + 1], 0)) + ", "
            if i > 0 and np.size(temporary1.split()) != 0:
                if temporary1.split()[np.size(temporary1.split()) - 1].strip(',') == temporary2.split()[1]:
                    decreasePart = "over " + temporary1.split()[1] + " to " + temporary2.split()[
                        np.size(temporary2.split()) - 1]
            if slopes[i] == min(slopes):
                maxDecrease = str(np.round(BP[i], 0)) + " till " + str(np.round(BP[i + 1], 0))
        elif slopes[i] > 0:
            if i > 0:
                temporary3 = increasePart
            increasePart = increasePart + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
            temporary4 = "over " + str(np.round(BP[i], 0)) + " to " + str(np.round(BP[i + 1], 0)) + ", "

            if slopes[i] == max(slopes):
                maxIncrease = maxIncrease + str(np.round(BP[i], 0)) + " to " + str(np.round(BP[i + 1], 0))
                begin1 = str(np.round(BP[i], 0))
                end1 = str(np.round(BP[i + 1], 0))
            elif slopes[i] == sorted(slopes)[-2]:
                maxIncrease = maxIncrease + str(np.round(BP[i], 0)) + " to " + str(
                    np.round(BP[i + 1], 0)) + ", "
                begin2 = str(np.round(BP[i], 0))
                end2 = str(np.round(BP[i + 1], 0))
            if end1 == begin2:
                maxIncrease = begin1 + " to " + end2
            elif end2 == begin1:
                maxIncrease = begin2 + " to " + end1
            if i > 0 and np.size(temporary3.split()) != 0:
                if temporary3.split()[np.size(temporary3.split()) - 1].strip(',') == temporary4.split()[1]:
                    increasePart = "over " + temporary3.split()[1] + " to " + temporary4.split()[
                        np.size(temporary4.split()) - 1]
        else:
            notchangePart = notchangePart + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
        if R[i] > 0.7 and P[i] < 0.05:
            strongRSSI = strongRSSI + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
        elif R[i] > 0.7 and P[i] > 0.05:
            strongRNSSI = strongRNSSI + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
        elif R[i] < 0.7 and P[i] < 0.05:
            weakRSSI = weakRSSI + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
        elif R[i] < 0.7 and P[i] > 0.05:
            weakRNSSI = weakRNSSI + "over " + str(np.round(BP[i], 0)) + " to " + str(
                np.round(BP[i + 1], 0)) + ", "
    if maxIncrease.split()[0] == "to":
        mi = ""
        for j in range(np.size(maxIncrease.split()) - 1):
            mi = mi + maxIncrease.split()[j + 1]
            if j != np.size(maxIncrease.split()) - 2:
                mi = mi + " "
        maxIncrease = mi
    if governmentchild == True:
        Xmaxp = ""
        Xminp = ""
        maxpoint = argrelextrema(y.values, np.greater, order=1)[0]
        minpoint = argrelextrema(y.values, np.less, order=1)[0]
        for i in range(np.size(maxpoint)):
            if float(y[maxpoint[i]]) == max(y):
                Xmaxp = X[maxpoint[i]]
        for i in range(np.size(minpoint)):
            if float(y[minpoint[i]]) == min(y):
                Xminp = X[minpoint[i]]
        diff_from_last_year1 = y[np.size(X) - 1] - y[np.size(X) - 2]
        diff_from_last_year2 = np.round(diff_from_last_year1 / y[np.size(X) - 2], 2)
        return (
            X, max(y), Xmaxp, np.round(y[np.size(X) - 2], 2), np.round(X[np.size(X) - 2], 2),
            diff_from_last_year1,
            diff_from_last_year2
            , np.round(X[0], 2), np.round(X[np.size(X) - 1], 2), np.round(y[np.size(X) - 1], 2), increasePart,
            decreasePart,
            notchangePart, Xcolname, ycolname)
        # print(segmented_GC1.render(
        #     X=X,
        #     ymax=max(y),
        #     Xmax=Xmaxp,
        #     ylast=np.round(y[np.size(X) - 2], 2),
        #     Xlast=np.round(X[np.size(X) - 2], 2),
        #     diff1=diff_from_last_year1,
        #     diff2=diff_from_last_year2,
        #     Xbegin=np.round(X[0], 2),
        #     Xend=np.round(X[np.size(X) - 1], 2),
        #     yend=np.round(y[np.size(X) - 1], 2),
        #     iP=increasePart,
        #     dP=decreasePart,
        #     nP=notchangePart,
        #     Xcol=Xcolname,
        #     ycol=ycolname, ))
    if governmentdrug == True:
        return (increasePart, decreasePart, notchangePart, ycolname, maxIncrease, maxDecrease)
        # print(segmented_GD1.render(
        #     iP=increasePart,
        #     dP=decreasePart,
        #     nP=notchangePart,
        #     ycol=ycolname,
        #     mI=maxIncrease,
        #     mD=maxDecrease,))
    if base == True:
        return (X,
                np.round(X[0], 2),
                np.round(X[np.size(X) - 1], 2),
                increasePart,
                decreasePart,
                notchangePart,
                Xcolname,
                ycolname,
                BPNumber,
                maxIncrease,
                maxDecrease,
                level,
                slopes,
                rsq,
                R,
                P,
                strongRSSI,
                strongRNSSI,
                weakRSSI,
                weakRNSSI,)
        # print(segmented_B.render(
        #     X=X,
        #     Xbegin=np.round(X[0], 2),
        #     Xend=np.round(X[np.size(X) - 1], 2),
        #     iP=increasePart,
        #     dP=decreasePart,
        #     nP=notchangePart,
        #     Xcol=Xcolname,
        #     ycol=ycolname,
        #     n=BPNumber,
        #     mI=maxIncrease,
        #     mD=maxDecrease,
        #     L=level,
        #     slope=slopes,
        #     R1=rsq,
        #     R2=R,
        #     P=P,
        #     SRSSI=strongRSSI,
        #     SRNSSI=strongRNSSI,
        #     WRSSI=weakRSSI,
        #     WRNSSI=weakRNSSI, ))
    ###########
    if r2 == True or p == True:
        return (increasePart,
                decreasePart,
                notchangePart,
                Xcolname,
                ycolname,
                BPNumber,
                maxIncrease,
                maxDecrease,
                level,
                slopes,
                rsq,
                R,
                P,
                strongRSSI,
                strongRNSSI,
                weakRSSI,
                weakRNSSI,)
    # if r2 == True and p == True:
    #     print(segmented_R2P.render(
    #         iP=increasePart,
    #         dP=decreasePart,
    #         nP=notchangePart,
    #         Xcol=Xcolname,
    #         ycol=ycolname,
    #         n=BPNumber,
    #         mI=maxIncrease,
    #         mD=maxDecrease,
    #         L=level,
    #         slope=slopes,
    #         R1=rsq,
    #         R2=R,
    #         P=P,
    #         SRSSI=strongRSSI,
    #         SRNSSI=strongRNSSI,
    #         WRSSI=weakRSSI,
    #         WRNSSI=weakRNSSI,
    #     ))
    # elif r2 == True and p == False:
    #     print(segmented_R2.render(
    #         iP=increasePart,
    #         dP=decreasePart,
    #         nP=notchangePart,
    #         Xcol=Xcolname,
    #         ycol=ycolname,
    #         n=BPNumber,
    #         mI=maxIncrease,
    #         mD=maxDecrease,
    #         L=level,
    #         slope=slopes,
    #         R1=rsq,
    #         R2=R,
    #         P=P,
    #         SRSSI=strongRSSI,
    #         SRNSSI=strongRNSSI,
    #         WRSSI=weakRSSI,
    #         WRNSSI=weakRNSSI,
    #     ))
    # elif p == True and r2 == False:
    #     print(segmented_P.render(
    #         iP=increasePart,
    #         dP=decreasePart,
    #         nP=notchangePart,
    #         Xcol=Xcolname,
    #         ycol=ycolname,
    #         n=BPNumber,
    #         mI=maxIncrease,
    #         mD=maxDecrease,
    #         L=level,
    #         slope=slopes,
    #         R1=rsq,
    #         R2=R,
    #         P=P,
    #         SRSSI=strongRSSI,
    #         SRNSSI=strongRNSSI,
    #         WRSSI=weakRSSI,
    #         WRNSSI=weakRNSSI,
    #     ))


def pycaret_find_best_model(dataset, types, target, sort, exclude, n, session_id):
    print(
        "If all of the data types are correctly identified 'enter' can be pressed to continue or 'quit' can be typed to end the expriment.")
    if types == 0:
        clf = classification.setup(data=dataset, target=target, session_id=session_id)
        if sort == "":
            sort = 'Accuracy'
        best_model = classification.compare_models(exclude=exclude, n_select=n, sort=sort)
        comapre_results = classification.pull()

    elif types == 1:
        reg = regression.setup(data=dataset, target=target, session_id=session_id)
        if sort == "":
            sort = 'R2'
        best_model = regression.compare_models(exclude=exclude, n_select=n, sort=sort)
        comapre_results = regression.pull()

    if n == 1:
        pycaretname = readable_name_converted_input_name(best_model)
    else:
        pycaretname = readable_name_converted_input_name(best_model[0])
    return (best_model, pycaretname, comapre_results)


def more_readable_model_name(modeldetail):
    if "Ridge" in modeldetail and "BayesianRidge" not in modeldetail:
        translatedmodel = "Ridge Model"
    elif "LinearDiscriminant" in modeldetail:
        translatedmodel = "Linear Discriminant Analysis"
    elif "GradientBoosting" in modeldetail:
        translatedmodel = "Gradient Boosting Model"
    elif "AdaBoost" in modeldetail:
        translatedmodel = "Ada Boost"
    elif "LGBMClassifier" in modeldetail:
        translatedmodel = "Light Gradient Boosting Machine Classifier"
    elif "DummyClassifier" in modeldetail:
        translatedmodel = "Dummy Classifier"
    elif "KNeighborsClassifier" in modeldetail:
        translatedmodel = "K Neighbors Classifier"
    elif "SGDClassifier" in modeldetail:
        translatedmodel = "SGD Classifier"
    elif "LGBMRegressor" in modeldetail:
        translatedmodel = "Light Gradient Boosting Machine"
    elif "RandomForest" in modeldetail:
        translatedmodel = "Random Forest Model"
    elif "XGBRegressor" in modeldetail:
        translatedmodel = "Extreme Gradient Boosting"
    elif "XGBClassifier" in modeldetail:
        translatedmodel = "Extreme Gradient Boosting Classifier"
    elif "Logistic" in modeldetail:
        translatedmodel = "Logistic Model"
    elif "QuadraticDiscriminant" in modeldetail:
        translatedmodel = "Quadratic Discriminant Analysis"
    elif "GaussianNB" in modeldetail:
        translatedmodel = "Naive Bayes"
    elif "ExtraTrees" in modeldetail:
        translatedmodel = "Extra Trees model"
    elif "DecisionTree" in modeldetail:
        translatedmodel = "Decision Tree Model"
    elif "Lasso" in modeldetail and "LassoLars" not in modeldetail:
        translatedmodel = "Lasso Regression	"
    elif "LassoLars" in modeldetail:
        translatedmodel = "Lasso Least Angle Regression	"
    elif "BayesianRidge" in modeldetail:
        translatedmodel = "Bayesian Ridge"
    elif "LinearRegression" in modeldetail:
        translatedmodel = "Linear Regression"
    elif "HuberRegressor" in modeldetail:
        translatedmodel = "Huber Regressor"
    elif "PassiveAggressiveRegressor" in modeldetail:
        translatedmodel = "Passive Aggressive Regressor"
    elif "OrthogonalMatchingPursuit" in modeldetail:
        translatedmodel = "Orthogonal Matching Pursuit"
    elif "AdaBoostRegressor" in modeldetail:
        translatedmodel = "AdaBoost Regressor"
    elif "KNeighborsRegressor" in modeldetail:
        translatedmodel = "K Neighbors Regressor"
    elif "ElasticNet" in modeldetail:
        translatedmodel = "Elastic Net"
    elif "DummyRegressor" in modeldetail:
        translatedmodel = "Dummy Regressor"
    elif "Lars" in modeldetail:
        translatedmodel = "Least Angle Regression"
    return (translatedmodel)


def model_translate(modeldetail, n=1):
    if n == 1:
        modeldetail = str(modeldetail)
        translatedmodel = more_readable_model_name(modeldetail)
        return (translatedmodel)
    else:
        for i in range(len(modeldetail)):
            modeldetail[i] = str(modeldetail[i])
        translatedmodel = [0] * len(modeldetail)
        for i in range(len(modeldetail)):
            translatedmodel[i] = more_readable_model_name(modeldetail[i])
        return (translatedmodel)


def readable_name_converted_input_name(modeldetail):
    modeldetail = str(modeldetail)
    if "Ridge" in modeldetail and "BayesianRidge" not in modeldetail:
        pycaretname = "ridge"
    elif "LinearDiscriminant" in modeldetail:
        pycaretname = "lda"
    elif "GradientBoosting" in modeldetail:
        pycaretname = "gbr"
    elif "AdaBoost" in modeldetail:
        pycaretname = "ada"
    elif "LGBMClassifier" in modeldetail:
        pycaretname = "lightgbm"
    elif "DummyClassifier" in modeldetail:
        pycaretname = "dummy"
    elif "KNeighborsClassifier" in modeldetail:
        pycaretname = "knn"
    elif "SGDClassifier" in modeldetail:
        pycaretname = "svm"
    elif "LGBMRegressor" in modeldetail:
        pycaretname = "lightgbm"
    elif "RandomForest" in modeldetail:
        pycaretname = "rf"
    elif "XGBRegressor" in modeldetail:
        pycaretname = "xgboost"
    elif "XGBClassifier" in modeldetail:
        pycaretname = "xgboost"
    elif "Logistic" in modeldetail:
        pycaretname = "lr"
    elif "QuadraticDiscriminant" in modeldetail:
        pycaretname = "qda"
    elif "GaussianNB" in modeldetail:
        pycaretname = "nb"
    elif "ExtraTrees" in modeldetail:
        pycaretname = "et"
    elif "DecisionTree" in modeldetail:
        pycaretname = "dt"
    elif "Lasso" in modeldetail and "LassoLars" not in modeldetail:
        pycaretname = "lasso"
    elif "LassoLars" in modeldetail:
        pycaretname = "llar"
    elif "BayesianRidge" in modeldetail:
        pycaretname = "br"
    elif "LinearRegression" in modeldetail:
        pycaretname = "lr"
    elif "HuberRegressor" in modeldetail:
        pycaretname = "huber"
    elif "PassiveAggressiveRegressor" in modeldetail:
        pycaretname = "par"
    elif "OrthogonalMatchingPursuit" in modeldetail:
        pycaretname = "omp"
    elif "AdaBoostRegressor" in modeldetail:
        pycaretname = "ada"
    elif "KNeighborsRegressor" in modeldetail:
        pycaretname = "knn"
    elif "ElasticNet" in modeldetail:
        pycaretname = "en"
    elif "DummyRegressor" in modeldetail:
        pycaretname = "dummy"
    elif "Lars" in modeldetail:
        pycaretname = "lar"
    return (pycaretname)


def input_name_converted_readable_name(inputname, types):
    modeldetail = str(inputname)
    readablepycaretname = ""
    if "ridge" in modeldetail:
        readablepycaretname = "Ridge model"
    elif "lda" in modeldetail:
        readablepycaretname = "Linear Discriminant model"
    elif "gbr" in modeldetail:
        readablepycaretname = "Gradient Boosting model"
    elif "gbc" in modeldetail:
        readablepycaretname = "Gradient Boosting Classifier"
    elif "lightgbm" in modeldetail:
        readablepycaretname = "Light Gradient Boosting Machine model"
    elif "svm" in modeldetail:
        readablepycaretname = "SGD Classifier"
    elif "rf" in modeldetail:
        readablepycaretname = "Random Forest model"
    elif "xgboost" in modeldetail:
        readablepycaretname = "Extreme Gradient Boosting model"
    elif "lr" in modeldetail and types == 0:
        readablepycaretname = "Logistic model"
    elif "qda" in modeldetail:
        readablepycaretname = "Quadratic Discriminant model"
    elif "nb" in modeldetail:
        readablepycaretname = "Gaussian NB model"
    elif "et" in modeldetail:
        readablepycaretname = "Extra Trees model"
    elif "dt" in modeldetail:
        readablepycaretname = "Decision Tree model"
    elif "lasso" in modeldetail:
        readablepycaretname = "Lasso model"
    elif "llar" in modeldetail:
        readablepycaretname = "Lasso Lars model"
    elif "br" in modeldetail:
        readablepycaretname = "Bayesian Ridge model"
    elif "lr" in modeldetail and types == 1:
        readablepycaretname = "Linear Regression model"
    elif "huber" in modeldetail:
        readablepycaretname = "Huber Regressor model"
    elif "par" in modeldetail:
        readablepycaretname = "Passive Aggressive Regressor model"
    elif "omp" in modeldetail:
        readablepycaretname = "Orthogonal Matching Pursuit model"
    elif "en" in modeldetail:
        readablepycaretname = "Elastic Net model"
    elif "lar" in modeldetail and "llar" not in modeldetail:
        readablepycaretname = "Lars model"
    elif "dummy" in modeldetail:
        readablepycaretname = "Dummy model"
    elif "knn" in modeldetail:
        readablepycaretname = "K Neighbors model"
    elif "ada" in modeldetail:
        readablepycaretname = "Ada Boost model"
    return (readablepycaretname)


def inputname_to_readablename(inputname, types):
    if (len(inputname) == 1):
        readablename = []
        readablename = input_name_converted_readable_name(inputname, types)
    else:
        readablename = [0] * len(inputname)
        for i in range(len(inputname)):
            readablename[i] = input_name_converted_readable_name(inputname[i], types)
    return (readablename)


def SHAP_interpretion(imp_shap, imp_var):
    m = 0
    n = 0
    imp_pos_sum = 0
    imp_pos_value_sum = 0
    imp_neg_sum = 0
    imp_neg_value_sum = 0
    for i in imp_shap['NUM']:
        if float(imp_shap['SHAP Value'].loc[imp_shap['NUM'] == i]) >= 0:
            imp_pos_sum = imp_pos_sum + float(imp_shap['SHAP Value'].loc[imp_shap['NUM'] == i])
            imp_pos_value_sum = imp_pos_value_sum + float(imp_shap[imp_var].loc[imp_shap['NUM'] == i])
            m = m + 1
        else:
            imp_neg_sum = imp_neg_sum + float(imp_shap['SHAP Value'].loc[imp_shap['NUM'] == i])
            imp_neg_value_sum = imp_neg_value_sum + float(imp_shap[imp_var].loc[imp_shap['NUM'] == i])
            n = n + 1
    imp_pos_ave = imp_pos_sum / m
    imp_pos_value_ave = imp_pos_value_sum / m
    imp_neg_ave = imp_neg_sum / n
    imp_neg_value_ave = imp_neg_value_sum / n
    return (imp_pos_ave, imp_pos_value_ave, imp_neg_ave, imp_neg_value_ave)


def pycaret_create_model(types, modelname):
    if types == 0:
        model = classification.create_model(modelname)
        tuned_model = classification.tune_model(model)
        classification.plot_model(tuned_model, plot='error', save=True)
        classification.plot_model(tuned_model, plot='feature', save=True)
        classification.interpret_model(tuned_model, save=True)
        importance = pd.DataFrame({'Feature': classification.get_config('X_train').columns,
                                   'Value': abs(tuned_model.feature_importances_)}).sort_values(by='Value',
                                                                                                ascending=False)
        # importance = pd.DataFrame({'Feature': classification.get_config('X_train').columns,
        #                            'Value': abs(tuned_model.coef_[0])}).sort_values(by='Value', ascending=False)
        print(importance)
        for ind in importance.index:
            if importance['Value'][ind] == max(importance['Value']):
                imp_var = importance['Feature'][ind]
        classification.predict_model(tuned_model)
        results = classification.pull(tuned_model)
        shap_values = shap.TreeExplainer(tuned_model).shap_values(regression.get_config('X_train'))
        imp_shap = pd.DataFrame({imp_var: regression.get_config('X_train')[imp_var],
                                 'SHAP Value': shap_values[:, 0], 'NUM': range(len(shap_values[:, 0]))})
        imp_figure = cv2.imread('Feature Importance.png')
        Error_figure = cv2.imread('Prediction Error.png')
        SHAP_figure = cv2.imread('SHAP summary.png')
        imp_pos_ave, imp_pos_value_ave, imp_neg_ave, imp_neg_value_ave = SHAP_interpretion(imp_shap, imp_var)
        return (importance['Feature'], imp_var, results['Accuracy'][0], results['AUC'][0], imp_figure, Error_figure,
                SHAP_figure, imp_pos_ave, imp_pos_value_ave, imp_neg_ave, imp_neg_value_ave)
    elif types == 1:
        model = regression.create_model(modelname)
        tuned_model = regression.tune_model(model)
        regression.plot_model(tuned_model, plot='error', save=True)
        regression.plot_model(tuned_model, plot='feature', save=True)
        regression.interpret_model(tuned_model, save=True)
        importance = pd.DataFrame({'Feature': regression.get_config('X_train').columns,
                                   'Value': abs(tuned_model.feature_importances_)}).sort_values(by='Value',
                                                                                                ascending=False)
        for ind in importance.index:
            if importance['Value'][ind] == max(importance['Value']):
                imp_var = importance['Feature'][ind]
        regression.predict_model(tuned_model)
        results = regression.pull(tuned_model)
        imp_figure = cv2.imread('Feature Importance.png')
        Error_figure = cv2.imread('Prediction Error.png')
        shap_values = shap.TreeExplainer(tuned_model).shap_values(regression.get_config('X_train'))
        # print(shap_values[:,0])
        # print(regression.get_config('X_train')[imp_var])
        imp_shap = pd.DataFrame({imp_var: regression.get_config('X_train')[imp_var],
                                 'SHAP Value': shap_values[:, 0], 'NUM': range(len(shap_values[:, 0]))})
        imp_pos_ave, imp_pos_value_ave, imp_neg_ave, imp_neg_value_ave = SHAP_interpretion(imp_shap, imp_var)
        SHAP_figure = cv2.imread('SHAP summary.png')
        return (
        importance['Feature'], imp_var, results['R2'][0], results['MAPE'][0], imp_figure, Error_figure, SHAP_figure,
        imp_pos_ave, imp_pos_value_ave, imp_neg_ave, imp_neg_value_ave)


def skpipelinedatatranform(pipe, dataset):
    datatransform = pd.DataFrame(data=dataset)
    for i in range(np.size(pipe) - 1):
        datatransform = pipe[i].fit_transform(datatransform)
    col_names = dataset.columns.values.tolist()
    datatransform = pd.DataFrame(data=datatransform)
    datatransform.columns = col_names
    return (datatransform)
