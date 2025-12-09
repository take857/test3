import streamlit as st
import sys

# 状態を保持するためのセッションステートを初期化
if 'user_question' not in st.session_state:
    st.session_state.user_question = ""

def set_question(question):
    """ボタンが押されたときに、セッションステートの値を更新するコールバック関数"""
    # ここで質問テキストをセッションステートにセットしています。
    st.session_state.user_question = question

def main():
    st.title('質問デモ')

#    st.subheader('💡 よくある質問 (タップして質問を入力)')
#    st.write('以下のボタンを押すと、その質問内容が下の入力欄に自動で反映されます。')

    faq_list = [
        "Q: このアプリは何ができますか？",
        "Q: どのように入力すればよいですか？",
        "Q: 入力した内容はどこに保存されますか？",
        "Q: 開発者へのフィードバックを送りたいです。"
    ]

    col1, col2 = st.columns(2)
    
    # ボタンが押されると set_question 関数が実行され、セッションステートが更新されます。
    with col1:
        st.button(faq_list[0], on_click=set_question, args=(faq_list[0] + "\n\nA: ",))
        st.button(faq_list[1], on_click=set_question, args=(faq_list[1] + "\n\nA: ",))

    with col2:
        st.button(faq_list[2], on_click=set_question, args=(faq_list[2] + "\n\nA: ",))
        st.button(faq_list[3], on_click=set_question, args=(faq_list[3] + "\n\nA: ",))
    
    st.markdown("---")

    st.subheader('🖊️ ご質問・コメントをご入力ください')
    
    # text_areaは、valueに設定された st.session_state.user_question の値を表示します。
    user_input = st.text_area(
        label="こちらにテキストを入力してください:",
        height=200,
        placeholder="例：この機能について詳しく教えてください。",
        key='user_input',
        value=st.session_state.user_question # ボタンによって更新された値がここに反映されます
    )

    if st.button('⬆️ 送信'):
        if user_input:
            st.success('ご入力ありがとうございます！')
            st.write('**あなたが入力した内容:**')
            st.code(user_input, language='')
            # 送信後に入力欄をリセット
            st.session_state.user_question = ""
        else:
            st.warning('テキストが入力されていません。')

if __name__ == '__main__':
    main()
