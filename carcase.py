import pandas
import ADSTP.DataToInformationPipeline as d2t
import ADSTP.IntegratedPipeline as ip
# Set pipelines
integrated_pipeline = ip.general_datastory_pipeline
# Set replace variables names
readable_names = dict((kv.split(': ') for kv in (l.strip(' \n') for l in open('./data/readableNamesForTenData.txt'))))


# Read dataset
# Car_dataset = pandas.read_csv('./data/car data.csv')
# # Select target columns
# Xcol = ['Present_Price', 'Kms_Driven', 'Year']; ycol = 'Selling_Price'
# # Data preprocessing.
# cleandata=d2t.remove_outliers(Car_dataset,Xcol,ycol)
# # Fit the data to the prototype.
# integrated_pipeline.LinearFit(cleandata, Xcol, ycol, [readable_names.get(key) for key in Xcol], readable_names.get(ycol))
#
#
# # # Read dataset
# fish_dataset=pandas.read_csv('./data/fish.csv')
# # Select target columns
# Xcol = ['Length', 'Diagonal', 'Height', 'Width']; ycol = 'Weight'
# # # Data preprocessing.
# # cleandata=d2t.remove_outliers(fish_dataset,Xcol,ycol)
# # Fit the data to the prototype.
# integrated_pipeline.LinearFit(fish_dataset, Xcol, ycol, [readable_names.get(key) for key in Xcol], readable_names.get(ycol)


# Step 1: Read the example dataset about diabetes, the dependent column (target variable) should use 0 or 1 to represent not having diabetes or having diabetes.
col_names = ['pregnant', 'glucose level', 'blood pressure', 'skin', 'insulin level', 'BMI', 'pedigree', 'age', 'diabetes']
diabetes_dataset = pandas.read_csv("./data/diabetes.csv", header=None, names=col_names)
# Step 2: Choose the model (which is logistic regression here) and the independent and dependent variables, the stories will be generated.
pipeline=ip.general_datastory_pipeline
pipeline.LogisticFit(diabetes_dataset, [ 'glucose level', 'blood pressure', 'insulin level', 'BMI', 'age'],'diabetes')
