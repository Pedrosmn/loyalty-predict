# %%

import pandas as pd
import sqlalchemy

from sklearn import model_selection
from feature_engine import selection, imputation, encoding

pd.set_option('display.max_columns', None) 
# pd.reset_option('display.max_rows')
con = sqlalchemy.create_engine('sqlite:///../../data/analytics/database.db')

# %%

# SAMPLE - Import dos dados

df = pd.read_sql("abt_fiel", con)

# SAMPLE - OOT

df_oot = df[df['dtRef'] == df['dtRef'].max()].reset_index(drop=True)
df_oot

# %%

# SAMPLE Treino e Teste

target = 'flFiel'
features = df.columns.tolist()[3:]

df_train_test = df[df['dtRef'] < df['dtRef'].max()].reset_index(drop=True)

X = df_train_test[features]
y = df_train_test[target]




X_train, X_test, y_train, y_test = model_selection.train_test_split(
    X, y,
    random_state=42,
    test_size=0.2,
    stratify=y
)

print(f"Base Treino: {y_train.shape[0]} Unid | Tx. Target: {100*y_train.mean():.2f}%")
print(f"Base Teste: {y_test.shape[0]} Unid | Tx. Target: {100*y_test.mean():.2f}%")

# %%

# EXPLORE - Missing

s_nas = X_train.isna().mean()
s_nas = s_nas[s_nas > 0]
s_nas

# %%

df_train = X_train.copy()
df_train[target] = y_train.copy()

df_train

# %%

# EXPLORE - Bivariada

cat_features = ['descLifeCycleAtual', 'descLifeCycleD28']
num_features = list(set(features) - set(cat_features))
num_features

# %%

df_train[num_features] = df_train[num_features].astype(float)
bivariada = df_train.groupby(target)[num_features].median().T
bivariada['ratio'] = (bivariada[1] + 0.001) / (bivariada[0] + 0.001) 
bivariada = bivariada.sort_values('ratio', ascending=False)
bivariada

# %%
df_train.groupby('descLifeCycleAtual')[target].mean()

# %%

# MODIFY - Drop

X_train[num_features] = X_train[num_features].astype(float)

to_remove = bivariada[bivariada['ratio'] == 1].index.tolist()
drop_features = selection.DropFeatures(to_remove)

# MODIFY - Missing Values

imput_0 = imputation.ArbitraryNumberImputer(arbitrary_number=0, variables=['python2025'])

imput_new = imputation.CategoricalImputer(fill_value='Nao-Usuario', variables=['descLifeCycleD28'])

imput_1000 = imputation.ArbitraryNumberImputer(arbitrary_number=1000, variables=['qtdDiasUltiAtividade', 'avgIntervaloDiasVida', 'avgIntervaloDiasD28'])

# MODIFY - ONEHOT

onehot = encoding.OneHotEncoder(variables=cat_features)

# MODIFY - Aplicando Transformações no Dataset

X_train_transform = drop_features.fit_transform(X_train)
X_train_transform = imput_0.fit_transform(X_train_transform)
X_train_transform = imput_new.fit_transform(X_train_transform)
X_train_transform = imput_1000.fit_transform(X_train_transform)
X_train_transform = onehot.fit_transform(X_train_transform)

X_train_transform