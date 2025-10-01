conda create -n env_cde_tres python==3.11 -y
conda activate env_cde_tres


python -m venv .venv
.\.venv\Scripts\Activate
python -m pip install --upgrade pip
pip install -r requirements.txt