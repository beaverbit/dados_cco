# run_all.py
# Roda o pipeline completo em ordem.

import subprocess
import sys
import time

ETAPAS = [
    ("01 - Extracao",         "scripts/01_extracao_cco.py"),
    ("02 - Limpeza",          "scripts/02_limpeza_cco.py"),
    ("03 - Analise",          "scripts/03_analise_cco.py"),
    ("04 - Visualizacao",     "scripts/04_visualizacao_cco.py"),
    ("06 - Machine Learning", "scripts/06_machine_learning_cco.py"),
    ("07 - Relatorio PDF",    "scripts/07_gerar_pdf_cco.py"),
]


def etapa(nome, script):
    print()
    print("------------------------------------------------------------")
    print(f" >> {nome}")
    print("------------------------------------------------------------")

    t0 = time.time()
    resultado = subprocess.run([sys.executable, script])
    t1 = time.time()

    if resultado.returncode != 0:
        print(f"\n[ERRO] {nome} falhou (código {resultado.returncode})")
        sys.exit(resultado.returncode)

    print(f" [ok] {nome} em {t1 - t0:.1f}s")


def main():
    inicio = time.time()

    print("============================================================")
    print(" PIPELINE CCO - INICIO")
    print("============================================================")

    for nome, script in ETAPAS:
        etapa(nome, script)

    fim = time.time()
    print()
    print("============================================================")
    print(f" PIPELINE CONCLUIDO em {fim - inicio:.1f}s")
    print("============================================================")
    print()
    print("Pra abrir o dashboard, rode separado:")
    print("  streamlit run scripts/05_dashboard_cco.py")


if __name__ == "__main__":
    main()
