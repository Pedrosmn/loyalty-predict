# %%

import pandas as pd
import sqlalchemy

# %%

def import_query(path):
    with open(path) as open_file:
        query = open_file.read()
    return query

query = import_query("frequencia_valor.sql")
print(query)

# %%

engine = sqlalchemy.create_engine("sqlite:///../../data/loyalty-system/database.db")

df = pd.read_sql(query, engine)
df.head()

#%%

df = df.loc[df['qtdePontosPos'] <= 4000]

# %%

import matplotlib.pyplot as plt

plt.plot(df[['qtdeFrequencia']], df[['qtdePontosPos']], "o")
plt.grid(True)

# %%

from sklearn import cluster
from sklearn import preprocessing

minmax = preprocessing.MinMaxScaler()
X = minmax.fit_transform(df[['qtdeFrequencia','qtdePontosPos']])

df_X = pd.DataFrame(X, columns=['normFreq', 'normValor'])
df_X
# %%

kmean = cluster.KMeans(n_clusters=5,
                       random_state=42,
                       max_iter=1000)

kmean.fit(X)

df['cluster_calc'] = kmean.labels_
df_X['cluster'] = kmean.labels_

df.groupby(by='cluster_calc')['IdCliente'].count()

# %%

import seaborn as sns

sns.scatterplot(data=df,
                x="qtdeFrequencia",
                y="qtdePontosPos",
                hue="cluster_calc",
                palette="deep")

plt.hlines(y=1500, xmin=0,xmax=25, colors='black')
plt.hlines(y=750, xmin=0,xmax=25, colors='black')
plt.vlines(x=4, ymin=0,ymax=750, colors='black')
plt.vlines(x=10, ymin=0,ymax=3000, colors='black')
plt.grid()

# %%