import pandas as pd

df = pd.read_csv("hf://datasets/criteo/FairJob/fairjob.csv.gz")

print(df.head())