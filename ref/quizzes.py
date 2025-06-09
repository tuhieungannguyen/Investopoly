import random

# ------------------------------
# 1. Định nghĩa toàn bộ bộ c    âu hỏi mẫu
# ------------------------------
QUIZ_BANK = [
    {
        "id": 1,
        "question": "Treasury bonds are subject to ________ risk but are essentially free of ________ risk.",
        "options": [
            "A) default; interest-rate",
            "B) default; underwriting",
            "C) interest-rate; default",
            "D) interest-rate; underwriting"
        ],
        "correct_index": 2  # "C) interest-rate; default"
    },
    {
        "id": 2,
        "question": "Which of the following is an example of a derivative?",
        "options": [
            "A) Corporate bond",
            "B) Mutual fund",
            "C) Stock option",
            "D) Bank deposit"
        ],
        "correct_index": 2  # "C) Stock option"
    },
    {
        "id": 3,
        "question": "What is a cryptocurrency?",
        "options": [
            "A) A physical currency, like paper money",
            "B) A digital currency that uses cryptography for security",
            "C) A type of stock",
            "D) A type of credit card"
        ],
        "correct_index": 1  # "B) A digital currency that uses cryptography for security"
    },
    {
        "id": 4,
        "question": "Which of the following are securities?",
        "options": [
            "A) A certificate of deposit",
            "B) A share of Texaco common stock",
            "C) A Treasury bill",
            "D) All of the above"
        ],
        "correct_index": 3  # "D) All of the above"
    },
    {
        "id": 5,
        "question": "A debt instrument is called ________ if its maturity is greater than 10 years.",
        "options": [
            "A) perpetual",
            "B) intermediate-term",
            "C) short-term",
            "D) long-term"
        ],
        "correct_index": 3  # "D) long-term"
    },
    {
        "id": 6,
        "question": "The DAX (Germany) and the FTSE 100 (London) are examples of",
        "options": [
            "A) foreign stock exchanges.",
            "B) foreign currencies.",
            "C) foreign stock price indexes.",
            "D) foreign mutual funds."
        ],
        "correct_index": 2  # "C) foreign stock price indexes."
    },
    {
        "id": 7,
        "question": "The security with the longest maturity is a Treasury",
        "options": [
            "A) note.",
            "B) bond.",
            "C) acceptance.",
            "D) bill."
        ],
        "correct_index": 1  # "B) bond."
    },
    {
        "id": 8,
        "question": "To sell an old bond when interest rates have ________, the holder will have to ________ the price of the bond until the yield to the buyer is the same as the market rate.",
        "options": [
            "A) risen; lower",
            "B) risen; raise",
            "C) fallen; lower",
            "D) risen; inflate"
        ],
        "correct_index": 0  # "A) risen; lower"
    },
    {
        "id": 9,
        "question": "What time did Bitcoin Network Start?",
        "options": [
            "A) January 2009",
            "B) February 2001",
            "C) May 2008",
            "D) June 2009"
        ],
        "correct_index": 0  # "A) January 2009"
    },
    {
        "id": 10,
        "question": "What is the main technology behind most cryptocurrencies like Bitcoin?",
        "options": [
            "A) Cloud computing.",
            "B) Blockchain.",
            "C) Data mining.",
            "D) Artificial Intelligence"
        ],
        "correct_index": 1  # "B) Blockchain."
    },
    {
        "id": 11,
        "question": "What does the term “DeFi” stand for in the crypto world?",
        "options": [
            "A) Decentralized Finance.",
            "B) Defined Financial Instruments.",
            "C) Digital File Exchange",
            "D) Default Financial Rules"
        ],
        "correct_index": 0  # "A) Decentralized Finance."
    },
    {
        "id": 12,
        "question": "Which of the following is a stablecoin designed to reduce cryptocurrency volatility?",
        "options": [
            "A) Ethereum",
            "B) Solana",
            "C) Tether (USDT)",
            "D) Dogecoin"
        ],
        "correct_index": 2  # "C) Tether (USDT)"
    },
    {
        "id": 13,
        "question": "In the Bitcoin protocol, what is the maximum total supply of Bitcoin that can ever exist?",
        "options": [
            "A) 100 million",
            "B) 50 million",
            "C) 21 million",
            "D) 15 million"
        ],
        "correct_index": 2  # "C) 21 million"
    },
    {
        "id": 14,
        "question": "What is a blockchain?",
        "options": [
            "A) A distributed ledger on a peer to peer network",
            "B) A type of cryptocurrency",
            "C) An exchange",
            "D) A centralized ledger"
        ],
        "correct_index": 0  # "A) A distributed ledger on a peer to peer network"
    },
    {
        "id": 15,
        "question": "Who is the creator of Bitcoin?",
        "options": [
            "A) Satoshi Nakamoto",
            "B) Anna Delvey",
            "C) Edward Snowden",
            "D) Sam Altman"
        ],
        "correct_index": 0  # "A) Satoshi Nakamoto"
    }
]

# Tiền thưởng khi trả lời đúng
REWARD_AMOUNT = 50

# -------------------------------------
# 2. Lớp Thể hiện Người chơi Giả lập
# -------------------------------------
class Player:
    def __init__(self, name: str, cash: int):
        self.name = name
        self.cash = cash
    
    def __repr__(self):
        return f"<Player name={self.name} cash={self.cash}>"

# -------------------------------------
# 3. Lấy câu hỏi ngẫu nhiên
# -------------------------------------
def get_random_quiz():
    """
    Trả về một câu hỏi ngẫu nhiên với id, question, và options.
    """
    quiz = random.choice(QUIZ_BANK)
    return {
        "id": quiz["id"],
        "question": quiz["question"],
        "options": quiz["options"]
    }

# -------------------------------------
# 4. Đánh giá đáp án của người chơi
# -------------------------------------
def evaluate_answer(player: Player, question_id: int, selected_index: int) -> dict:
    """
    Kiểm tra đáp án đúng/sai. Nếu đúng, cộng REWARD_AMOUNT vào player.cash.
    Trả về dict với chi tiết kết quả.
    """
    question = next((q for q in QUIZ_BANK if q["id"] == question_id), None)
    if question is None:
        return {"error": f"Question ID {question_id} not found."}

    is_correct = (selected_index == question["correct_index"])
    reward = 0
    if is_correct:
        player.cash += REWARD_AMOUNT
        reward = REWARD_AMOUNT

    return {
        "question_id": question_id,
        "selected_index": selected_index,
        "correct_index": question["correct_index"],
        "is_correct": is_correct,
        "reward": reward,
        "new_cash": player.cash
    }

# -------------------------------------
# 5. Phần test mẫu (chạy file độc lập)
# -------------------------------------
if __name__ == "__main__":
    # Tạo một Player giả lập
    player = Player("Alice", 1000)
    print("Before answering:", player)

    # Lấy câu hỏi ngẫu nhiên để hiển thị
    quiz = get_random_quiz()
    print("\n--- Random Quiz ---")
    print(f"Question ID: {quiz['id']}")
    print(f"Question: {quiz['question']}")
    for idx, option in enumerate(quiz["options"]):
        print(f"  {idx}. {option}")

    # Lấy thông tin câu hỏi đầy đủ để tìm correct_index
    full_quiz = next(q for q in QUIZ_BANK if q["id"] == quiz["id"])

    # Ví dụ: Chọn đúng đáp án
    selected_index = full_quiz["correct_index"]
    # Nếu muốn test trường hợp sai, dùng:
    # selected_index = (full_quiz["correct_index"] + 1) % len(full_quiz["options"])

    # Đánh giá đáp án
    result = evaluate_answer(player, quiz["id"], selected_index)
    print("\n--- Evaluation Result ---")
    print(result)
    print("After answering:", player)
