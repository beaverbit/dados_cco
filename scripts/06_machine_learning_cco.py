# 06_machine_learning_cco.py
# Meu objetivo: prever se uma NC é crítica ou não crítica.

import pandas as pd
import os
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import joblib

# Raiz do projeto (pasta pai de scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQ_NCS = os.path.join(BASE_DIR, "dados_tratados", "nao_conformidades_limpas.csv")
PASTA_MODELO = os.path.join(BASE_DIR, "modelo")
PASTA_IMAGENS = os.path.join(BASE_DIR, "imagens")

FEATURES = ["filial", "classificacao", "codigo_unidade", "capitulo_nc"]
TARGET = "critica_bin"

# Cores (Tema Claro)
COR_TEXTO = "#2C3E50"
COR_BORDA = "#B0BEC5"


def carregar():
    print("Carregando NCs...")
    df = pd.read_csv(ARQ_NCS, sep=";", encoding="utf-8", low_memory=False)
    print(f"Linhas: {len(df):,}")
    return df


def preparar(df):
    print("\nPreparando...")

    df = df.assign(
        critica_bin=(df["gravidade"] == "Crítica").map({True: "Crítica", False: "Outra"})
    )

    colunas = FEATURES + [TARGET]
    df = df[colunas].copy()
    antes = len(df)
    df = df.dropna()
    print(f"Nulos removidos: {antes - len(df):,}")

    encoders = {}
    for col in FEATURES:
        le = LabelEncoder()
        df = df.assign(**{col: le.fit_transform(df[col].astype(str))})
        encoders[col] = le
        print(f"  {col}: {len(le.classes_)} únicos")

    le_t = LabelEncoder()
    df = df.assign(**{TARGET: le_t.fit_transform(df[TARGET].astype(str))})
    encoders[TARGET] = le_t

    print(f"Amostras: {len(df):,}")
    print(f"Classes: {list(le_t.classes_)}")
    print(f"Distribuição:")
    print(df[TARGET].value_counts())

    return df, encoders


def treinar(df):
    print("\nTreinando Random Forest...")
    X = df[FEATURES].astype(float)
    y = df[TARGET].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42,
    )

    m = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_split=5,
        n_jobs=-1, random_state=42, class_weight="balanced",
    )
    m.fit(X_tr, y_tr)
    y_p = m.predict(X_te)

    print(f"\nAcurácia: {accuracy_score(y_te, y_p):.4f}")
    print(f"F1 (weighted): {f1_score(y_te, y_p, average='weighted'):.4f}")
    print("\nRelatório:")
    print(classification_report(y_te, y_p, zero_division=0))

    return m, X_te, y_te, y_p


def matriz_confusao(y_te, y_p, encoders):
    print("\nMatriz de confusão...")
    labels = list(encoders[TARGET].classes_)
    cm = confusion_matrix(y_te, y_p, labels=list(range(len(labels))))

    fig = px.imshow(
        cm, text_auto=True, aspect="auto",
        x=labels, y=labels,
        color_continuous_scale="Blues",
        labels=dict(x="Previsto", y="Real"),
        title="Matriz de Confusão",
    )
    fig.update_layout(
        template="plotly_white",
        height=500,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=COR_TEXTO, size=13),
        title_font=dict(color=COR_TEXTO, size=17),
        margin=dict(l=40, r=40, t=60, b=60)
    )
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    caminho = os.path.join(PASTA_IMAGENS, "09_matriz_confusao_cco.png")
    fig.write_image(caminho, width=800, height=600, scale=1.5)
    print(f"  -> {caminho}")


def importancia(modelo):
    print("\nImportância das features...")
    imp = pd.DataFrame({
        "feature": FEATURES,
        "importancia": modelo.feature_importances_,
    }).sort_values("importancia", ascending=True)

    fig = px.bar(
        imp, x="importancia", y="feature", orientation="h",
        color="importancia", color_continuous_scale="Greens",
        labels={"importancia": "Importância", "feature": ""},
        title="Importância das Features",
    )
    # Adiciona contorno e tira a legenda de cor
    fig.update_traces(
        marker_line_color=COR_BORDA, marker_line_width=1,
        text=imp["importancia"].round(3), textposition="outside", cliponaxis=False
    )
    fig.update_layout(
        template="plotly_white",
        coloraxis_showscale=False, 
        height=400,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=COR_TEXTO, size=13),
        title_font=dict(color=COR_TEXTO, size=17),
        margin=dict(l=40, r=40, t=60, b=60)
    )
    caminho = os.path.join(PASTA_IMAGENS, "10_importancia_features_cco.png")
    fig.write_image(caminho, width=900, height=500, scale=1.5)
    print(f"  -> {caminho}")

    print("\nTop features:")
    print(imp.tail(5).to_string(index=False))


def salvar(m, enc):
    os.makedirs(PASTA_MODELO, exist_ok=True)
    joblib.dump(m, os.path.join(PASTA_MODELO, "modelo_cco.pkl"))
    joblib.dump(enc, os.path.join(PASTA_MODELO, "encoders_cco.pkl"))
    print(f"\nSalvos em {PASTA_MODELO}/")


if __name__ == "__main__":
    df = carregar()
    df_prep, encoders = preparar(df)
    modelo, X_te, y_te, y_p = treinar(df_prep)
    salvar(modelo, encoders)
    matriz_confusao(y_te, y_p, encoders)
    importancia(modelo)
    print("\nML concluído.")