# %%

import pandas as pd
import matplotlib.pyplot as plt
import sqlalchemy

from sklearn import model_selection
from feature_engine import selection, imputation, encoding

import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment(experiment_id=1)

pd.set_option('display.max_columns', None)
con = sqlalchemy.create_engine('sqlite:///../../data/analytics/database.db')

# %%

# SAMPLE - Import dos dados

df = pd.read_sql("SELECT * FROM abt_fiel", con)

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

# MODEL

from sklearn import tree, ensemble, metrics, pipeline

# model = tree.DecisionTreeClassifier(random_state=42, min_samples_leaf=50)
model = ensemble.AdaBoostClassifier(random_state=42)
# model = ensemble.RandomForestClassifier(random_state=42)

params = {
    "n_estimators": [100,200,400,500,1000],
    "learning_rate": [0.001,0.01,0.05,0.1,0.2,0.5,0.9,0.99],
}

grid = model_selection.GridSearchCV(model, 
                                    param_grid=params,
                                    cv=3,
                                    scoring='roc_auc',
                                    refit=True,
                                    verbose=3,
                                    n_jobs=-1)

with mlflow.start_run() as r:

    mlflow.sklearn.autolog()


    # PIPELINE

    model_pipeline = pipeline.Pipeline(steps=[
        ("Remocao de Features", drop_features),
        ("Imputação de Zeros", imput_0),
        ("Imputacao de Nao Usuario", imput_new),
        ("Imputacao de 1000", imput_1000),
        ("ONEHOT Encoding", onehot),
        ("Algoritmo", grid)
        ])

    model_pipeline.fit(X_train, y_train)

    # ASSESS - Métricas

    # Treino

    y_pred_treino = model_pipeline.predict(X_train)
    y_proba_treino = model_pipeline.predict_proba(X_train)

    y_pred_treino_acc = metrics.accuracy_score(y_train, y_pred_treino)
    y_pred_treino_auc = metrics.roc_auc_score(y_train, y_proba_treino[:,1])

    print(f"Acurácia Treino: {y_pred_treino_acc}")
    print(f"AUC Treino: {y_pred_treino_auc}")

    # Teste

    y_pred_test = model_pipeline.predict(X_test)
    y_proba_test = model_pipeline.predict_proba(X_test)

    y_pred_test_acc = metrics.accuracy_score(y_test, y_pred_test)
    y_pred_test_auc = metrics.roc_auc_score(y_test, y_proba_test[:,1])

    print(f"Acurácia Teste: {y_pred_test_acc}")
    print(f"AUC Teste: {y_pred_test_auc}")

    # OOT

    X_oot = df_oot[features]
    y_oot = df_oot[target]

    y_pred_oot = model_pipeline.predict(X_oot)
    y_proba_oot = model_pipeline.predict_proba(X_oot)

    y_pred_oot_acc = metrics.accuracy_score(y_oot, y_pred_oot)
    y_pred_oot_auc = metrics.roc_auc_score(y_oot, y_proba_oot[:,1])

    print(f"Acurácia oot: {y_pred_oot_acc}")
    print(f"AUC oot: {y_pred_oot_auc}")

    # Métricas

    mlflow.log_metrics({
        "auc_train":y_pred_treino_auc,
        "auc_test":y_pred_test_auc,
        "auc_oot":y_pred_oot_auc,
    })

    # Curva ROC
    roc_train = metrics.roc_curve(y_train, y_proba_treino[:,1])
    roc_test = metrics.roc_curve(y_test, y_proba_test[:,1])
    roc_oot = metrics.roc_curve(y_oot, y_proba_oot[:,1])

    plt.plot(roc_train[0], roc_train[1])
    plt.plot(roc_test[0], roc_test[1])
    plt.plot(roc_oot[0], roc_oot[1])
    plt.legend([f"Treino: {y_pred_treino_auc:.4f}", 
                f"Teste: {y_pred_test_auc:.4f}", 
                f"OOT: {y_pred_oot_auc:.4f}"])
    plt.grid(True)
    plt.title("Curva ROC")
    plt.show()
    plt.savefig("curva_roc.png")

    mlflow.log_artifact("curva_roc.png")

# %%

feature_names = (model_pipeline[:-1].transform(X_train.head(1))
                                    .columns
                                    .tolist())
features_importance = pd.Series(model_pipeline[-1].feature_importances_, index=feature_names)
features_importance.sort_values(ascending=False)