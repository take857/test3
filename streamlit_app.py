import streamlit as st
import sys

# st.write('有給はどれくらい取得できますか')
if "history" not in st.session_state:
    st.session_state["history"] = []
    st.session_state.history.append({"role":"user", "content": "こんにちは"})
    st.session_state.history.append({"role":"assistant", "content": "何を手伝いましょうか"})


# チャット履歴を表示する
#for message in st.session_state.history:
#    with st.chat_message(message["role"]):
#        st.write(message["content"])

#if prompt := st.chat_input("質問をどうぞ"):
#    st.session_state.history.append({"role": "user", "content": prompt})
#    with st.chat_message('user'):
#        st.write(prompt)

#    st.session_state.history.append({"role": "assistant", "content": "はい"})
#    with st.chat_message('assistant'):
#        st.write('はい')

st.markdown(
    f"<p>{st.session_state}</p>",
    unsafe_allow_html=True
)
