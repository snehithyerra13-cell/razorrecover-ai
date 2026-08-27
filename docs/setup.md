# Setup Guide - RazorRecover AI

Follow these instructions to configure and run the backend server, train the machine learning model, and launch the React dashboard.

## Prerequisites
- **Python** (version 3.13+ recommended)
- **Node.js** (version 22+ recommended) and **yarn** (or npm)
- **Git**

---

## 1. Backend Setup

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows PowerShell**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows Command Prompt**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Train the Machine Learning Model to enable recovery probability prediction:
   ```bash
   python app/ml/train.py
   ```
   *This trains a RandomForest classifier on 10,000 synthetic transaction records and saves the serialized pipeline to `app/ml/model.joblib`.*

---

## 2. Environment Variables Configuration

Copy the example configuration file in the project root:
```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in the credentials:
- **`GEMINI_API_KEY`**: Obtain an API key from Google AI Studio. If left empty, the application will automatically fall back to deterministic rule analysis.
- **`RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`**: Add your Razorpay Test API keys to enable Sandbox checkout simulator functions.

---

## 3. Launching Servers

### Start the Backend API (FastAPI)
From the `backend` folder with your virtual environment active:
```bash
uvicorn app.main:app --port 8000 --reload
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to view the interactive Swagger API documentation.

### Start the Frontend Dashboard (React + Vite)
1. Open a new terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   yarn install
   # or: npm install --no-audit --legacy-peer-deps
   ```
3. Run the development server:
   ```bash
   yarn dev
   # or: npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser to interact with the dashboard.
