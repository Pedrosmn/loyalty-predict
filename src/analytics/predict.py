# %%

import pandas as pd
import sqlalchemy

con = sqlalchemy.create_engine('sqlite:///../../data/analytics/database.db')

# %%

data = pd.read_sql("SELECT * FROM abt_fiel", con)
data

# %%

model = pd.read_pickle("model_fiel.pkl")
model
# %%

predict = model["model"].predict_proba(data[model["features"]])[:,1]

data["predict"] = predict

data
# %%
