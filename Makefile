# Define o ambiente Conda
CONDA_ENV=loyalty-predict

# Define o diretório do ambiente virtual
VENV_DIR=.venv

# Define os diretórios
ENGINEERING_DIR=src/engineering
ANALYTICS_DIR=src/analytics


# Configura o ambiente virtual
.PHONY: setup
setup:
	rm -rf $(VENV_DIR)
	@echo "Criando ambiente virtual..."
	python3 -m venv $(VENV_DIR)
	@echo "Ativando ambiente virtual e instalando dependências..."
	. $(VENV_DIR)/bin/activate && \
	pip install pipreqs && \
 	pipreqs src/ --force --savepath requirements.txt && \
	sed -i 's/pandas==3.0.5/pandas>=2.2,<3/' requirements.txt && \
	pip install -r requirements.txt


# Executa os scripts
.PHONY: collect
collect:
	@echo "Ativando ambiente virtual..."
	@echo "Executando scripts de engenharia..."
	. $(VENV_DIR)/bin/activate && \
	cd src/engineering && \
	python get_data.py


# etl das features
.PHONY: etl
etl:
	@echo "Ativando ambiente virtual..."
	@echo "Executando scripts de feature store..."
	. $(VENV_DIR)/bin/activate && \
	cd src/analytics && \
	python pipeline_analytics.py

# predicao
.PHONY: predict
predict:
	@echo "Ativando ambiente virtual..."
	@echo "Executando script de predição..."
	. $(VENV_DIR)/bin/activate && \
	cd src/analytics && \
	python predict_fiel.py


# Alvo padrão
.PHONY: all
all: setup collect etl predict