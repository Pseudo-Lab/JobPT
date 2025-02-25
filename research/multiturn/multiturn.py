from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability.",
        ),
        ("placeholder", "{messages}"),
    ]
)

chat = ChatOpenAI(model="gpt-4o-mini")
chain = prompt | chat

ai_msg = chain.invoke(
    {
        "messages": [
            (
                "human",
                "Translate this sentence from English to French: I love programming.",
            ),
            ("ai", "J'adore la programmation."),
            ("human", "What did you just say?"),
        ],
    }
)
print(ai_msg.content)

history_list = []
while(True):
    user_input = input()
    if user_input == "종료": break
    history_list.append(
        (
            "human",
            user_input,
        )
    )
    print("## CHAT_HISTORY ##")
    print(history_list, "\n")
    ai_msg = chain.invoke(
        {
            "messages": history_list,
        }
    )
    print("AI Says : ",ai_msg.content)

    history_list.append(
        (
            "ai",
            ai_msg.content,
        )
    )
