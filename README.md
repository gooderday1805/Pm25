# Pm25
#BE 
cd pm-2-5-be
python3 -m venv .venv          # Chỉ chạy lần đầu
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows PowerShell

# Cài các package thường dùng, thiếu cài thêm
pip install fastapi uvicorn flask requests pandas

# Chạy server
python3 app.py

# FE
cd pm-2-5-fe
npm install
npm run dev