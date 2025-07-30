# 🏡 RoomMakeover.AI

> **AI-Powered Interior Design Assistant** – Upload a room image and get personalized room makeover plans with style-specific suggestions, budget optimization, and direct e-commerce links. Built with YOLOv8n object detection and Gemini 1.5 Flash AI.

---

## 🚀 Project Overview

RoomMakeover.AI is an intelligent room enhancement tool that combines computer vision with advanced AI to transform your living spaces:

### ✨ Key Features

- **🔍 Smart Object Detection**: Uses YOLOv8n to identify furniture, decor, and room type
- **🎨 7 Design Styles**: Choose from Modern, Minimalist, Scandinavian, Bohemian, Industrial, Traditional, and Coastal
- **💰 Budget-Aware Planning**: Intelligent suggestions that respect your budget (₹500 - ₹50,000)
- **🛒 E-commerce Integration**: Direct shopping links to Amazon, Flipkart, Pepperfry, and Urban Ladder
- **📊 Comprehensive Analysis**: Room type classification, object counting, and space assessment
- **🎯 Style-Specific Guidance**: Detailed color palettes, materials, and design elements for each style
- **💡 Professional Tips**: Expert styling advice and arrangement suggestions

### 🏠 Supported Room Types

- **Bedroom**: Bed, wardrobe, nightstand detection
- **Living Room**: Sofa, TV, coffee table analysis  
- **Kitchen**: Appliance and dining furniture recognition
- **Office**: Desk, computer, bookshelf identification
- **Dining Room**: Table and seating arrangement analysis
- **General Rooms**: Flexible detection for mixed-use spaces

---

## 🧠 Tech Stack

| Component | Technology |
|-----------|------------|
| 🔍 Object Detection | YOLOv8n (Ultralytics) |
| 🧠 AI Planning | Google Gemini 1.5 Flash |
| 📝 Prompt Engineering | LangChain Templates |
| 🖥️ Frontend | Streamlit (Enhanced UI) |
| 🔧 API Backend | FastAPI (Optional) |
| 🛒 E-commerce | Multi-platform integration |
| 🎨 Styling | Custom CSS & Components |

---

## 📸 How It Works

### 1. **Image Analysis** 
- Upload any room image (bedroom, living room, kitchen, etc.)
- YOLOv8n detects and counts furniture, decor, and objects
- System automatically classifies room type and assesses current state

### 2. **Style & Budget Input**
- Select from 7 professional interior design styles
- Set your budget range (₹500 - ₹50,000)
- Optional: Choose room priorities (functionality, aesthetics, storage, etc.)

### 3. **AI-Powered Planning**
- Gemini AI analyzes room context with style-specific guidelines
- Generates 3-5 targeted improvement suggestions
- Each suggestion includes pricing, description, and style impact

### 4. **Shopping Integration**
- Direct links to major Indian e-commerce platforms
- Search-optimized keywords for easy product finding
- Price validation against Indian market rates

### 5. **Professional Presentation**
- Comprehensive makeover summary with styling tips
- Budget breakdown and remaining funds calculation
- Visual presentation with organized item cards

---

## 🎨 Design Styles Available

### Modern ✨
- **Focus**: Clean lines, minimal approach, neutral colors
- **Colors**: White, black, gray, beige
- **Materials**: Glass, metal, concrete, leather
- **Elements**: Geometric shapes, open spaces, statement lighting

### Minimalist 🤍
- **Focus**: Less is more philosophy, clutter-free
- **Colors**: White, cream, light gray, natural wood
- **Materials**: Natural wood, linen, cotton, bamboo
- **Elements**: Hidden storage, multi-functional furniture

### Scandinavian 🌲
- **Focus**: Cozy, functional, hygge-inspired comfort
- **Colors**: Light blue, soft gray, natural wood tones
- **Materials**: Light wood, wool, cotton, linen
- **Elements**: Natural textures, cozy textiles, plants

### Bohemian 🌺
- **Focus**: Eclectic, colorful, artistic layers
- **Colors**: Earth tones, jewel tones, warm oranges
- **Materials**: Rattan, macrame, vintage fabrics
- **Elements**: Layered rugs, hanging plants, tapestries

### Industrial 🏭
- **Focus**: Raw materials, exposed elements, urban loft
- **Colors**: Charcoal, rust, black, deep brown
- **Materials**: Exposed brick, metal, reclaimed wood
- **Elements**: Exposed pipes, metal fixtures, Edison bulbs

### Traditional 🏛️
- **Focus**: Classic elegance, rich fabrics, timeless
- **Colors**: Burgundy, navy, forest green, warm gold
- **Materials**: Dark wood, silk, velvet, brass
- **Elements**: Antique furniture, formal arrangements

### Coastal 🌊
- **Focus**: Beach-inspired, light and airy
- **Colors**: Ocean blue, sandy beige, coral, seafoam
- **Materials**: Weathered wood, rope, seagrass, linen
- **Elements**: Nautical decor, natural lighting, woven textures

---

## 🛠️ Installation & Setup

### 🔐 Prerequisites

- **Python 3.9+**
- **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app)
- **Git** for cloning the repository

### 📦 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd room-makeover-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 🚀 Running the Application

#### Option 1: Streamlit Web App (Recommended)
```bash
streamlit run streamlit_app.py
```
Access at: `http://localhost:8501`

#### Option 2: FastAPI Backend
```bash
python app/main.py
```
API Documentation: `http://localhost:8000/docs`

---

## 📋 API Documentation

### Endpoints

#### `POST /makeover`
Generate room makeover suggestions

**Parameters:**
- `image`: Room image file (JPG/JPEG)
- `budget`: Budget in INR (500-50000)
- `style`: Design style preference

**Response:**
```json
{
  "success": true,
  "data": {
    "room_description": "Detailed room analysis",
    "detection_result": {
      "detected_items": ["bed", "chair", "lamp"],
      "room_type": "bedroom", 
      "total_objects": 3
    },
    "makeover_plan": {
      "status": "success",
      "parsed_response": {
        "items": [...],
        "total_price": "4500",
        "makeover_summary": "...",
        "styling_tips": "..."
      }
    }
  }
}
```

#### `GET /styles`
Get available interior design styles with details

#### `GET /health`
Health check endpoint

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
GEMINI_API_KEY=your_google_gemini_api_key

# Optional
SERPAPI_KEY=your_serpapi_key_for_enhanced_search
```

### Customization Options

1. **Budget Ranges**: Modify in `streamlit_app.py` or `app/main.py`
2. **Style Definitions**: Edit `STYLE_GUIDES` in `app/llm_suggester.py`
3. **Object Detection**: Customize `INDOOR_OBJECTS` in `app/image_processor.py`
4. **E-commerce Platforms**: Update `ECOMMERCE_PLATFORMS` for different regions

---

## 📁 Project Structure

```
room-makeover-ai/
├── app/
│   ├── image_processor.py      # YOLOv8 object detection
│   ├── llm_suggester.py        # Gemini AI integration
│   ├── pipeline.py             # Main processing pipeline
│   ├── main.py                 # FastAPI backend
│   └── utils/
│       └── helpers.py          # Utility functions
├── sample_data/                # Test images
├── streamlit_app.py           # Streamlit frontend
├── requirements.txt           # Dependencies
├── yolov8n.pt                # YOLOv8 model weights
└── README.md                 # Documentation
```

---

## 🎯 Usage Examples

### Example 1: Bedroom Makeover
- **Input**: Bedroom image with basic furniture
- **Budget**: ₹8,000
- **Style**: Scandinavian
- **Output**: Cozy textiles, plants, lighting suggestions with Nordic aesthetic

### Example 2: Living Room Enhancement  
- **Input**: Living room with sofa and TV
- **Budget**: ₹15,000
- **Style**: Modern
- **Output**: Accent furniture, artwork, storage solutions with clean lines

### Example 3: Budget-Friendly Kitchen
- **Input**: Simple kitchen space
- **Budget**: ₹3,000
- **Style**: Industrial
- **Output**: Metal accents, hanging storage, vintage elements

---

## 🚀 Future Enhancements

- [ ] **3D Room Visualization**: AR/VR preview of suggestions
- [ ] **Social Features**: Share and rate makeover plans
- [ ] **Professional Consultation**: Connect with real interior designers
- [ ] **Seasonal Themes**: Holiday and seasonal decoration ideas
- [ ] **Multiple Room Planning**: Whole-home makeover coordination
- [ ] **Price Tracking**: Monitor suggested item prices over time

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Ultralytics** for YOLOv8 object detection
- **Google** for Gemini AI capabilities
- **LangChain** for prompt engineering tools
- **Streamlit** for rapid web app development
- **Indian E-commerce Platforms** for product availability

---

<div align="center">

**🏡 RoomMakeover.AI - Transform Your Space with Intelligence**

*Built with ❤️ for Indian homes*

</div>

