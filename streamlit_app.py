import streamlit as st
import os
import tempfile
import json
import re
from app.pipeline import image_to_makeover

# Page setup
st.set_page_config(page_title="RoomMakeover.AI", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E4057;
        margin-bottom: 2rem;
    }
    .style-card {
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .item-card {
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f0f8ff;
        border-radius: 5px;
    }
    .shopping-links {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .shopping-button {
        background-color: #ff6b35;
        color: white;
        padding: 5px 15px;
        border-radius: 5px;
        text-decoration: none;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🏡 RoomMakeover.AI</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 18px; color: #666;">Transform your space with AI-powered interior design suggestions</p>', unsafe_allow_html=True)

# Sidebar for style information
with st.sidebar:
    st.header("🎨 Style Guide")
    st.write("Choose your preferred interior style to get personalized recommendations:")
    
    # Style descriptions
    style_info = {
        "Modern": "✨ Clean lines, minimalist approach, neutral colors",
        "Minimalist": "🤍 Less is more philosophy, clutter-free design",
        "Scandinavian": "🌲 Cozy, functional, light woods, hygge comfort", 
        "Bohemian": "🌺 Eclectic, colorful, artistic textures",
        "Industrial": "🏭 Raw materials, exposed elements, urban loft",
        "Traditional": "🏛️ Classic elegance, rich fabrics, timeless",
        "Coastal": "🌊 Beach-inspired, light and airy, natural"
    }
    
    for style, desc in style_info.items():
        st.markdown(f"**{style}**: {desc}")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Your Room Image")
    uploaded_file = st.file_uploader("Choose a room image (.jpg or .jpeg)", type=["jpg", "jpeg"])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Your Room", use_column_width=True)

with col2:
    st.subheader("⚙️ Customize Your Makeover")
    
    # Budget input with better formatting
    budget = st.slider("💸 Budget (₹)", min_value=500, max_value=50000, value=5000, step=500)
    st.write(f"Selected Budget: ₹{budget:,}")
    
    # Enhanced style selection
    style_options = ["Any", "Modern", "Minimalist", "Scandinavian", "Bohemian", "Industrial", "Traditional", "Coastal"]
    style = st.selectbox("🎨 Preferred Style", style_options)
    
    # Additional preferences
    st.subheader("🏠 Room Preferences")
    room_priorities = st.multiselect(
        "What's most important to you?",
        ["Functionality", "Aesthetics", "Storage", "Comfort", "Natural Light", "Color Coordination"]
    )

# Submit button
submit = st.button("✨ Generate Makeover Plan", type="primary", use_container_width=True)

if submit:
    if not uploaded_file:
        st.warning("⚠️ Please upload an image first.")
    else:
        with st.spinner("🔍 Analyzing your room and generating personalized suggestions..."):
            # Save uploaded image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Run the full pipeline
            result = image_to_makeover(tmp_path, budget, style)

            # Clean up temp file
            os.remove(tmp_path)

        # Display results
        if result.get("status") == "error":
            st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
        else:
            # Room Analysis Section
            st.header("🧩 Room Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Room Type", result["detection_result"]["room_type"].replace("_", " ").title())
            
            with col2:
                st.metric("Objects Detected", result["detection_result"]["total_objects"])
                
            with col3:
                st.metric("Style Applied", result["llm_response"].get("style_applied", style))
            
            # Room Description
            st.subheader("📝 Room Description")
            st.write(result.get("room_description", "No description generated."))
            
            # Detected Objects
            if result["detection_result"]["detected_items"]:
                st.subheader("🔍 Detected Items")
                detected_items = result["detection_result"]["detected_items"]
                object_counts = result["detection_result"]["object_counts"]
                
                # Display in a nice format
                items_display = []
                for item in detected_items:
                    count = object_counts.get(item, 1)
                    if count > 1:
                        items_display.append(f"{count}x {item}")
                    else:
                        items_display.append(item)
                
                st.write("**Found items:** " + " • ".join(items_display))

            # Makeover Suggestions
            llm_resp = result.get("llm_response", {})
            if llm_resp.get("status") == "success":
                parsed_response = llm_resp.get("parsed_response", {})
                
                if parsed_response:
                    st.header("🎨 Your Personalized Makeover Plan")
                    
                    # Room Analysis
                    if "room_analysis" in parsed_response:
                        st.subheader("📊 Space Analysis")
                        st.info(parsed_response["room_analysis"])
                    
                    # Style Direction
                    if "style_direction" in parsed_response:
                        st.subheader("🎯 Style Direction")
                        st.success(parsed_response["style_direction"])
                    
                    # Suggested Items
                    if "items" in parsed_response and parsed_response["items"]:
                        st.subheader("🛍️ Recommended Items")
                        
                        for i, item in enumerate(parsed_response["items"], 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="item-card">
                                    <h4>{i}. {item.get('name', 'Item')}</h4>
                                    <p><strong>Category:</strong> {item.get('category', 'N/A').title()}</p>
                                    <p><strong>Description:</strong> {item.get('description', 'No description available')}</p>
                                    <p><strong>Price:</strong> ₹{item.get('price', 'N/A')}</p>
                                    <p><strong>Style Impact:</strong> {item.get('style_impact', 'Enhances overall aesthetics')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Shopping Links
                                if 'shopping_links' in item:
                                    st.markdown("**🛒 Shop this item:**")
                                    cols = st.columns(4)
                                    
                                    platforms = ['amazon', 'flipkart', 'pepperfry', 'urban_ladder']
                                    platform_names = ['Amazon', 'Flipkart', 'Pepperfry', 'Urban Ladder']
                                    
                                    for j, (platform, name) in enumerate(zip(platforms, platform_names)):
                                        with cols[j]:
                                            if platform in item['shopping_links']:
                                                st.markdown(f"[{name}]({item['shopping_links'][platform]})")
                    
                    # Total Cost and Summary
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if "total_price" in parsed_response:
                            total_price = parsed_response["total_price"]
                            if isinstance(total_price, str):
                                # Extract number from string if needed
                                price_num = re.findall(r'\d+', total_price)
                                if price_num:
                                    price_num = int(price_num[0])
                                    budget_percentage = (price_num / budget) * 100
                                    st.metric("💰 Total Cost", f"₹{total_price}", f"{budget_percentage:.1f}% of budget")
                                else:
                                    st.metric("💰 Total Cost", f"₹{total_price}")
                            else:
                                budget_percentage = (total_price / budget) * 100
                                st.metric("💰 Total Cost", f"₹{total_price}", f"{budget_percentage:.1f}% of budget")
                    
                    with col2:
                        remaining_budget = budget - (int(re.findall(r'\d+', str(parsed_response.get("total_price", "0")))[0]) if re.findall(r'\d+', str(parsed_response.get("total_price", "0"))) else 0)
                        st.metric("💳 Remaining Budget", f"₹{remaining_budget:,}")
                    
                    # Makeover Summary
                    if "makeover_summary" in parsed_response:
                        st.subheader("✨ Your Transformed Space")
                        st.markdown(f"> {parsed_response['makeover_summary']}")
                    
                    # Styling Tips
                    if "styling_tips" in parsed_response:
                        st.subheader("💡 Pro Styling Tips")
                        st.info(parsed_response["styling_tips"])
                        
                else:
                    # Fallback for old format
                    st.subheader("🎨 Makeover Suggestion")
                    raw_output = llm_resp.get("raw_output", "")
                    st.code(raw_output)
                    
            elif llm_resp.get("status") == "json_error":
                st.error("❌ Error parsing response. Here's the raw output:")
                st.code(llm_resp.get("raw_output", "No output"))
                
            else:
                st.error(f"❌ LLM Error: {llm_resp.get('message', 'Unknown error')}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🏡 <strong>RoomMakeover.AI</strong> - Powered by YOLOv8 Object Detection & Gemini AI</p>
    <p>Transform your space with intelligent design suggestions tailored to Indian homes</p>
</div>
""", unsafe_allow_html=True)
