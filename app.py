import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AquaExchange Dashboard", layout="wide")
col2, col3 = st.columns([1, 5])
with col2:
    st.title("AquaExchange Dashboard")
with col3:
    # toggle AI chat on the lef
    st.session_state.show_ai = True

st.divider()

# search + fetch
query = st.text_input("Search", placeholder="e.g. ponds with > 80 DOC")

if st.button("🔄 Fetch Data"):
    st.session_state.df = pd.DataFrame({
        "Pond": ["Pond A", "Pond B"],
        "DOC": [90, 85],
        "Acres": [2.5, 3.0]
    })
    st.success("Data fetched!")

# --- feedback section ---
st.markdown("#### Feedback")

emoji_list = ["🙂","😃","😐","😡","🤬"]

# Create a container for emojis with custom CSS
st.markdown("""
<style>
.emoji-row {
    display: flex;
    gap: 5px;
    margin: 10px 0;
}
.emoji-btn {
    font-size: 1.5rem;
    padding: 0;
    margin: 0;
    border: none;
    background: none;
    cursor: pointer;
    transition: transform 0.2s;
}
.emoji-btn:hover {
    transform: scale(1.2);
}
</style>
""", unsafe_allow_html=True)

# Create emoji buttons in a single row
st.markdown('<div class="emoji-row">' + 
            ''.join([f'<button class="emoji-btn" onclick="handleEmojiClick({i})">{emoji}</button>' 
                    for i, emoji in enumerate(emoji_list)]) + 
            '</div>', 
            unsafe_allow_html=True)

# JavaScript to handle emoji clicks
st.components.v1.html("""
<script>
function handleEmojiClick(emojiIndex) {
    const emojis = ["🙂","😃","😐","😡","🤬"];
    const selectedEmoji = emojis[emojiIndex];
    
    // Store in session state
    window.parent.postMessage({
        isStreamlitMessage: true,
        type: 'streamlit:setSessionState',
        data: {
            type: 'set',
            key: 'selected_feedback',
            value: selectedEmoji
        }
    }, '*');
    
    // Show balloons for happy emojis
    if (emojiIndex === 0 || emojiIndex === 1) {
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: 'streamlit:customComponentMessage',
            componentId: 'balloons',
            args: {}
        }, '*');
    } else {
        // Show warning for other emojis
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: 'streamlit:customComponentMessage',
            componentId: 'warning',
            args: {}
        }, '*');
    }
}
</script>
""", height=0)

# Handle emoji selection in Python
if 'selected_feedback' in st.session_state:
    selected_emoji = st.session_state.selected_feedback
    if selected_emoji in ["🙂","😃"]:
        st.balloons()
    elif selected_emoji in ["😐","😡","🤬"]:
        st.warning("We're sorry to hear that — we'll improve!")

# Feedback submission
feedback_comment = st.text_input("", placeholder="Optional comment...", label_visibility="collapsed")
if st.button("Submit Feedback", use_container_width=True):
    st.success(
        f"Feedback submitted: {selected_emoji or 'No emoji'} with comment: {feedback_comment}"
    )

# data preview if available
if "df" in st.session_state:
    st.divider()
    st.subheader("Pond Data")
    st.dataframe(st.session_state.df)
    csv = st.session_state.df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download CSV",
        csv,
        file_name=f"pond_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# --- AI chatbot in the left sidebar ---
if st.session_state.get("show_ai"):
    with st.sidebar:

        st.caption("Ask any pond or farm-related question!")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_message = st.text_input("Ask a question:", key="chat_input")

        if st.button("Send"):
            # dummy reply
            ai_reply = f"🤖: You asked '{user_message}'. I'll connect to GPT soon!"
            st.session_state.chat_history.append({"role": "user", "content": user_message})
            st.session_state.chat_history.append({"role": "ai", "content": ai_reply})

        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.write(f"👤 {chat['content']}")
            else:
                st.write(chat["content"])