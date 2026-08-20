# Telegram Chat Analyser 📄🧠

A silent runtime tool that listens to your personal Telegram account, auto-detects research papers (sent as text, PDF attachments, or PDF links), analyzes them using Google Gemini, and appends beautifully formatted, multi-profile summaries to a Google Document via a Google Apps Script Web App.

---

## ✨ Features

- **🔍 Auto-Detection**: Dynamically classifies messages to detect whether they contain research paper content or academic text (using a fast, low-cost Gemini check).
- **📎 PDF Document Support**: Automatically downloads and extracts text from `.pdf` file attachments.
- **🔗 PDF Link Parsing**: Automatically extracts and downloads PDFs from links (like `arxiv.org/pdf/`) inside recommendation messages.
- **🤖 Gemini LLM Summarization**: Generates specialized summaries for four different target audiences:
  1. **For Students**: Accessible language, key concepts defined, analogies.
  2. **For Faculty pursuing PhD**: Methodology, related work context, literature gaps, and future thesis directions.
  3. **For PhD Holders**: Rigorous technical critique, algorithmic/mathematical innovations, and limitations.
  4. **For Product/Business**: Target market, commercialization viability, MVP features, and strategic value.
- **📄 Google Doc Integration**: Appends summaries with Google Docs using Apps Script with clean formatting and separator lines.
- **🤫 Silent Background Mode**: Operates completely silently in your Telegram chats. All updates, status checks, and errors are logged directly to the terminal console to avoid chat clutter.

---

## 🛠️ Project Structure

- [`analyser.py`](./analyser.py): Main Telegram client listener (Telethon), router, and coordinator.
- [`parsers.py`](./parsers.py): Component-based parser registry (follows the Open-Closed Principle). Can easily be extended with new parser classes (e.g. for `.docx`, `.html` or native Gemini Files API uploads).
- [`apps_script.js`](./apps_script.js): Google Apps Script JavaScript code to deploy on your Google Doc editor.
- [`requirements.txt`](./requirements.txt): Required python libraries (`telethon`, `python-dotenv`, `google-genai`, `requests`, `pypdf`).

---

## ⚙️ Prerequisites & Setup

### 1. How to Create a Telegram App (For API ID & API Hash)
Since this script runs on your personal Telegram account, you need to register a Telegram application to obtain your unique API credentials:
1. Open your browser and navigate to [my.telegram.org](https://my.telegram.org).
2. Enter your phone number with your country code (e.g., `+91XXXXXXXXXX`) and click **Next**.
3. Telegram will send a login confirmation code to your official Telegram app. Copy the code, paste it into the browser window, and log in.
4. Once logged in, click on **API development tools**.
5. Fill out the application details:
   - **App title**: `TelegramChatAnalyser`
   - **Short name**: `chatanalyser`
   - You can leave other fields (URL/Description) blank.
6. Click **Create application**.
7. You will see your configuration screen showing **App api_id** and **App api_hash**.
8. Copy these values. You will paste them into your `.env` file as `API_ID` and `API_HASH`.

---

### 2. How to Create & Deploy Google Apps Script on Google Docs
This allows the Python script to communicate directly with your Google Doc and append formatted research summaries:
1. Create a new Google Document (or open an existing one).
2. Look at the browser address bar and copy your **Document ID** from the Google Doc URL:
   - *Example URL*: `https://docs.google.com/document/d/1A2B3C4D5E6F/edit`
   - *Document ID*: `1A2B3C4D5E6F` (the string between `/d/` and `/edit`).
3. In the Google Doc menu bar, click **Extensions** ➔ **Apps Script**.
4. A new tab will open with the Google Apps Script editor. Delete all placeholder template code in the text editor (e.g. `function myFunction() { ... }`).
5. Open the project file [**`apps_script.js`**](./apps_script.js), copy its entire contents, and paste it into the Apps Script editor.
6. Locate line 18 in the Apps Script editor:
   ```javascript
   const DOCUMENT_ID = 'YOUR_DOCUMENT_ID_HERE';
   ```
   Replace `'YOUR_DOCUMENT_ID_HERE'` with your actual **Document ID** (e.g. `const DOCUMENT_ID = '1A2B3C4D5E6F';`).
7. Click the **Save** icon (floppy disk symbol) at the top of the editor.
8. Click the **Deploy** button (blue button on top right) and select **New deployment**.
9. In the deployment configuration popup:
   - Click the gear icon next to "Select type" and select **Web app**.
   - Under **Description**, type: `Telegram Chat Analyser API`.
   - Under **Execute as**, select **Me (your-gmail@gmail.com)**.
   - Under **Who has access**, select **Anyone** (this is necessary so your python script can make HTTP POST requests).
   - Click the **Deploy** button.
10. A prompt will ask you to authorize access. Click **Authorize access**, choose your Google account, click **Advanced**, click **Go to Untitled project (unsafe)**, and select **Allow** to grant document editing permissions.
11. Once completed, copy the **Web app URL** generated under the deployment details (it ends with `/exec`). You will paste this URL into your `.env` file.

---

### 3. Configuration Settings (`.env`)
Create/edit the [**`.env`**](./.env) file in the root folder and add the following variables:
```env
# Telegram API Credentials (obtained from my.telegram.org)
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=your_telegram_phone_number_with_country_code # e.g. +91XXXXXXXXXX

# Gemini API Key (obtained from aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key

# Deployed Google Apps Script Web App URL (obtained from Apps Script deployment)
APPS_SCRIPT_URL=https://script.google.com/macros/s/.../exec
```

---

## 🚀 Running the Application

### 1. Installation
Activate your virtual environment and install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launch the Listener
Run the analyser script:
```bash
python analyser.py
```
* **First-run Login**: Telethon will prompt you in the console to enter your **Phone Number** and the **Verification Code** sent to you via Telegram. This creates a local session file (`session.session`) to keep you logged in.

---

## 💡 How to Use

Once the console prints `👂 Listening for commands...`, the app processes messages automatically and silently:

1. **Text Messages**: Copy and paste raw paper content or abstracts in any chat.
2. **Replies**: Reply `/analyze` to any existing text message in a chat.
3. **PDF Documents**: Upload or forward any PDF research paper file.
4. **Links**: Send a message containing a PDF link (e.g. arXiv URL), like:
   ```text
   🔥 Attention Is All You Need
   🔗 Links:
     • PDF: https://arxiv.org/pdf/1706.03762
   ```

### Console Output Example
The analyser logs message traffic cleanly without writing back to the Telegram chat:
```text
======================================================================
📨 NEW MESSAGE RECEIVED!
======================================================================
⏰ Time: 2026-08-20 15:30:12
👤 From: John Doe (@johndoe)
🆔 User ID: 123456789
💬 Message: Research Link (PDF Link: https://arxiv.org/pdf/1706.03762)
======================================================================

[2026-08-20 15:30:13] Downloading PDF from link: https://arxiv.org/pdf/1706.03762...
[2026-08-20 15:30:16] Analyzing paper from John Doe (@johndoe)...
[2026-08-20 15:30:22] Appending analysis to Google Doc via Apps Script...
[2026-08-20 15:30:24] ✅ Successfully saved analysis of 'Attention Is All You Need' to Google Docs.
```

---

## ☁️ Deploying to Render (Headless Cloud Hosting)

Because cloud hosts like Render run in non-interactive environments without a terminal to type OTP codes, Telethon uses a **`StringSession`** (a single authorization token passed as an environment variable):

### Step 1: Generate your Session String locally (one-time)
Run the session generator script on your local PC:
```bash
python generate_session.py
```
Enter your phone number and the Telegram OTP code in your terminal. Copy the generated `TELEGRAM_SESSION_STRING`.

### Step 2: Create a Background Worker on Render
1. Go to your [Render Dashboard](https://dashboard.render.com/) ➔ **New +** ➔ **Background Worker** (or **Web Service** if worker is not on your plan).
2. Connect your Git repository.
3. Configure the build & start commands:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python analyser.py`
4. Under **Environment Variables**, add:
   - `API_ID`: `your_telegram_api_id`
   - `API_HASH`: `your_telegram_api_hash`
   - `TELEGRAM_SESSION_STRING`: *(Paste the session string generated from Step 1)*
   - `GEMINI_API_KEY`: `your_gemini_api_key`
   - `APPS_SCRIPT_URL`: `https://script.google.com/macros/s/.../exec`
5. Click **Deploy**.

Render will now run your Telegram listener 24/7 without needing any terminal input!