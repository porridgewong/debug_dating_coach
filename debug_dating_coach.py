import os
import streamlit as st
from volcenginesdkarkruntime import Ark
from zhipuai import ZhipuAI

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """
# Role
你是一个经验丰富的约会教练，擅长处理各种男女情感问题，帮助客户解决恋爱关系中的尴尬和疑惑，并可以为客户提供专业的约会建议。

# Task
你的任务是回答客户关于情感以及约会中碰到的问题，包括但不限于
* 约会建议
* 如何处理尴尬的场面
* 如何提升自己的魅力
* 如何处理恋爱中的矛盾
* 如何挽回感情
* 如何回复另一半或者追求者的信息

# Constraints
* 如果客户提出的问题不是情感问题或者与约会无关，你应当礼貌地表示无法回答这类问题。

# Output
请直接输出你的回答，不需要添加额外的标签或者格式
""".strip()

# App title
st.set_page_config(page_title="调试约会教练", page_icon="🧊")


def get_api_key(key_name: str) -> str:
    """Get API key"""
    if key_name in os.environ:
        api_key = os.environ.get(key_name)
    else:
        api_key = st.secrets[key_name]
    return api_key


def get_doubao_model_endpoint():
    """Get model endpoint for doubao LLM"""
    if "ARK_MODEL_ENDPOINT" in os.environ:
        model_endpoint = os.environ.get("ARK_MODEL_ENDPOINT")
    else:
        model_endpoint = st.secrets["ARK_MODEL_ENDPOINT"]
    return model_endpoint


with st.sidebar:
    st.title("设置")

    st.subheader("选择模型与参数")
    selected_model = st.sidebar.selectbox(
        "Select a model",
        ["glm-4-plus", "glm-4-flash", "doubao-pro-4k"],
        key="selected_model",
    )
    if selected_model == "glm-4-plus" or selected_model == "glm-4-flash":
        llm = ZhipuAI(api_key=get_api_key("ZHIPUAI_API_KEY"))
        model = selected_model
    else:
        llm = Ark(api_key=get_api_key("ARK_API_KEY"))
        model = get_doubao_model_endpoint()

    temperature = st.sidebar.slider(
        "temperature", min_value=0.01, max_value=5.0, value=0.3, step=0.01
    )
    top_p = st.sidebar.slider(
        "top_p", min_value=0.01, max_value=1.0, value=0.9, step=0.01
    )

    st.subheader("Override system prompt")
    new_system_prompt = st.text_area("Override system prompt here...")


# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = []

# Display system prompt
with st.expander(
    "System prompt (clear the overriding system prompt to fall back to the default)"
):
    current_system_prompt = DEFAULT_SYSTEM_PROMPT
    if new_system_prompt is not None and len(new_system_prompt.strip()) > 0:
        current_system_prompt = new_system_prompt
    st.text(current_system_prompt)


# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


def clear_chat_history():
    st.session_state.messages = []


st.sidebar.button("清空聊天历史", on_click=clear_chat_history)


def generate_response():
    """Call LLM to generate response"""
    system_prompt = DEFAULT_SYSTEM_PROMPT
    if new_system_prompt is not None and len(new_system_prompt.strip()) > 0:
        system_prompt = new_system_prompt.strip()
    messages = [{"role": "system", "content": system_prompt}]
    # prepare history
    for dict_message in st.session_state.messages:
        messages.append(dict_message)
    resp = llm.chat.completions.create(
        model=model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=512,
        messages=messages,
        stream=False,
    )
    return resp.choices[0].message.content


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if (
    len(st.session_state.messages) > 0
    and st.session_state.messages[-1]["role"] == "user"
):
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response()
            placeholder = st.empty()
            full_response = ""
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
