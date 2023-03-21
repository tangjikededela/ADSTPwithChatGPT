import pandas
import ADSTP.DataToInformationPipeline as d2t
import ADSTP.IntegratedPipeline as ip
# Set pipelines
integrated_pipeline = ip.general_datastory_pipeline
# Set replace variables names
readable_names = dict((kv.split(': ') for kv in (l.strip(' \n') for l in open('./data/readableNamesForTenData.txt'))))
# Read dataset
Car_dataset = pandas.read_csv('./data/car data.csv')
# Select target columns
Xcol = ['Present_Price', 'Kms_Driven', 'Year']; ycol = 'Selling_Price'
# Data preprocessing.
cleandata=d2t.remove_outliers(Car_dataset,Xcol,ycol)
# Fit the data to the prototype.
integrated_pipeline.LinearFit(cleandata, Xcol, ycol, [readable_names.get(key) for key in Xcol], readable_names.get(ycol))