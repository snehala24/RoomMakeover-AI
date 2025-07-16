import streamlit as st
import os
import tempfile
import json
import re
from app.pipeline import image_to_makeover

# Page setup
st.set_page_config(page_title="RoomMakeover.AI", layout="centered")
st.title("🏡 RoomMakeover.AI")
st.markdown("Upload a room image and get a personalized makeover plan powered by **YOLOv8 + Gemini 1.5 Flash**.")

# Upload image
uploaded_file = st.file_uploader("📤 Upload a room image (.jpg or .jpeg)", type=["jpg", "jpeg"])

# Budget input
budget = st.number_input("💸 Enter your budget (₹)", min_value=500, max_value=10000, value=1500, step=100)

# Style input
style = st.selectbox("🎨 Choose a preferred style", ["Any", "Modern", "Minimalist", "Cozy", "Boho", "Industrial"])

# Submit button
submit = st.button("✨ Suggest Makeover", key="makeover_button")

if submit:
    if not uploaded_file:
        st.warning("⚠️ Please upload an image first.")
    else:
        with st.spinner("Processing your room image..."):
            # Save uploaded image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Run the full pipeline
            result = image_to_makeover(tmp_path, budget, style)

            # Clean up temp file
            os.remove(tmp_path)

        # Display room description
        st.subheader("🧩 Room Description")
        st.write(result.get("room_description", "No description generated."))

        # Handle Gemini output
        llm_resp = result.get("llm_response", {})
        if llm_resp.get("status") == "success":
            st.subheader("🎨 Makeover Suggestion")

            raw_output = llm_resp.get("raw_output", "")
            cleaned = re.sub(r"```json|```", "", raw_output).strip()

            try:
                parsed = json.loads(cleaned)

                st.markdown("#### 🪑 Items to Add:")
                for item in parsed.get("items", []):
                    st.markdown(
                        f"- **{item['name']}** — ₹{item['price']}  \n"
                        f"  _{item.get('description', '')}_"
                    )

                st.markdown(f"\n#### 💰 Total Price: ₹{parsed.get('total_price', 'N/A')}")
                st.markdown(f"#### 📝 Notes:\n> {parsed.get('notes', '')}")

            except Exception as e:
                st.error(f"❌ JSON parsing failed: {e}")
                st.code(raw_output)

        else:
            st.error(f"❌ Gemini Error: {llm_resp.get('message', 'Unknown error')}")
