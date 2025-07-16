# 🏡 RoomMakeover.AI

> **AI-Powered Interior Design Assistant** – Upload a room image and get a personalized room makeover plan with decor suggestions, budget estimation, style recommendations, and shoppable Amazon links. Built with YOLOv8 and Gemini 1.5 Flash.

---

## 🚀 Project Overview

RoomMakeover.AI is an intelligent room enhancement tool that:
- Analyzes a room from an uploaded image.
- Understands its layout and elements using **YOLOv8 object detection**.
- Suggests stylish decor improvements using **Gemini 1.5 Flash LLM**.
- Respects your **budget** and **preferred style**.
- Lets you **download a PDF makeover plan**.
- Adds **Amazon links** so users can directly shop the recommended items.

---


## 🧠 Tech Stack

| Module            | Tech Used                             |
|------------------|----------------------------------------|
| 💡 Object Detection | [YOLOv8](https://github.com/ultralytics/ultralytics) (via `ultralytics`) |
| 🧠 LLM Decor Ideas | [Gemini 1.5 Flash](https://deepmind.google/technologies/gemini/) via `google.generativeai` |
| 🧪 LLM Prompting   | LangChain Prompt Templates            |
| 🖼️ Frontend UI     | Streamlit                             |
| 📄 PDF Generator   | `xhtml2pdf`                           |
| 🧠 Embedding Logic | Custom + FAISS                        |

---

## 📸 How It Works

1. **Upload a Room Image** (e.g., bedroom, living room).
2. The app uses **YOLOv8** to detect objects (bed, lamp, plant, etc.).
3. A prompt is created combining detected objects, budget, and preferred style.
4. **Gemini 1.5 Flash** generates:
   - Suggested decor items
   - Descriptions & prices
   - Notes and layout suggestions
5. You can:
   - View Amazon links for items.
   - Download a professional **PDF report** of the plan.

---

## 📂 Folder Structure

RoomMakeover.AI/
│
├── app/
│   ├── __init__.py
│   ├── pipeline.py          # Main function: image_to_makeover()
│   ├── llm_suggester.py     # Gemini prompt handling and JSON output
│   └── yolo_utils.py        # (Optional) Object detection helper (YOLOv8)
│
├── assets/                  # (Optional) Sample images / icons / CSS
│
├── .env                     # Your Gemini API key
├── requirements.txt
├── README.md
└── streamlit_app.py         # Main UI: Streamlit frontend


---

## 🛠️ Installation & Setup

### 🔐 Prerequisites

- Python 3.9+
- Gemini API key (from [Google AI Studio](https://makersuite.google.com/app))
- `pip install` permissions

---

### 🔧 Install Dependencies

```bash
git clone https://github.com/your-username/room-makeover-ai.git
cd room-makeover-ai
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

