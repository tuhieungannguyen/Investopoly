SERVER = "http://localhost:8000"
WS_URL_BASE = "ws://localhost:8000/ws"


# === TOTAL ROUND ===đđ
TOTAL_ROUND = 15

# === STARTING MONEY ===
START_MONEY = 2000  # Starting money for each player

# === GO REWARD ===
GO_REWARD = 200  # Amount of money received when passing GO

# === PLAYER COUNT ===
PLAYER_COUNT = 4  # Default number of players in the game

# === STOCKS ===
STOCK_POSITIONS = [2, 6, 12, 14, 16]
STOCKS = [
    {"name": "SAB", "industry": "A", "start_price": 200, "now_price": 200, "service_fee": 80, "available_units": 5, "max_per_player": 3, "position": 2},
    {"name": "FPT", "industry": "B", "start_price": 300, "now_price": 300, "service_fee": 100, "available_units": 5, "max_per_player": 3, "position": 6},
    {"name": "GAS", "industry": "C", "start_price": 300, "now_price": 300, "service_fee": 100, "available_units": 5, "max_per_player": 3, "position": 12},
    {"name": "VCB", "industry": "D", "start_price": 400, "now_price": 400, "service_fee": 120, "available_units": 5, "max_per_player": 3, "position": 14},
    {"name": "VIC", "industry": "E", "start_price": 400, "now_price": 400, "service_fee": 120, "available_units": 5, "max_per_player": 3, "position": 16},
]

# === ESTATES ===
ESTATES = [
    {"name": "Real Estate 1", "position": 1, "price": 100, "rent_price": 10},
    {"name": "Real Estate 2", "position": 4, "price": 200, "rent_price": 20},
    {"name": "Real Estate 3", "position": 9, "price": 300, "rent_price": 30},
    {"name": "Real Estate 4", "position": 11, "price": 400, "rent_price": 40},
    {"name": "Real Estate 5", "position": 19, "price": 500, "rent_price": 50},
]
# === JAIL STATUS ===
JAIL_STATUS = {
    "status": False,
    "start_round": 0,
    "end_round": 0,
    "player_name": ""
}
# === SAVING INTEREST RATE ===
SAVING_INTEREST_RATE = 0.04  # 4% interest rate for savings

# === SAVING DURATION ===
SAVING_DURATION = 3  # Savings last for 3 rounds
# === TAX AMOUNT ===
TAX_AMOUNT = 100

RENTING_ESTATE_FEE = 0.1
# === SERVICE FEE ===
SERVICE_FEE = 0.02  # 2% service fee for stock transactions

# === GAME SETTINGS ===
GAME_SETTINGS = {
    "total_round": TOTAL_ROUND,
    "player_count": PLAYER_COUNT,  # Default player count
    "saving_interest_rate": SAVING_INTEREST_RATE,
    "saving_duration": SAVING_DURATION,
    "service_fee": SERVICE_FEE
}

# === TILE MAP ===
TILE_MAP = [
    "GO", "Real Estate 1","Stock Corp A", "Chance","Real Estate 2",
    "Jail Visit", "Stock Corp B", "Shock event", "Savings", "Real Estate 3", "Quizzes (Education)",
    "Real Estate 4", "Stock Corp C", "Chance", "Stock Corp D", "Jail (Challenge)", 
    "Stock Corp E", "Shock event","Tax Checkpoint", "Real Estate 5"
]

# === SHOCK EVENTS ===
SHOCK_EVENTS = [
    {
        "name": "Global Pandemic",
        "description": "A new virus variant forces city lockdowns. Factories and airports are shut down.",
        "effect_stock": [
            {"name": "VCB", "amount": -20},
            {"name": "VIC", "amount": -20},
            {"name": "FPT", "amount": -30},
            {"name": "GAS", "amount": -30},
            {"name": "SAB", "amount": -40},
        ],
        "effect_estate": {
            "value": 0,
            "rent": -30
        }
    },
    {
        "name": "Global Financial Crisis",
        "description": "Banks and financial institutions collapse, shaking market confidence.",
        "effect_stock": [
            {"name": "VCB", "amount": -20},
            {"name": "VIC", "amount": -20},
            {"name": "FPT", "amount": -35},
            {"name": "GAS", "amount": -35},
            {"name": "SAB", "amount": -60},
        ],
        "effect_estate": {
            "value": -40,
            "rent": -20
        }
    },
    {
        "name": "US Tariff Policy",
        "description": "The US imposes a 46% tariff on Vietnamese goods. Tech and energy sectors are hit.",
        "effect_stock": [
            {"name": "VCB", "amount": 10},
            {"name": "VIC", "amount": 10},
            {"name": "FPT", "amount": -10},
            {"name": "GAS", "amount": -10},
            {"name": "SAB", "amount": -20},
        ],
        "effect_estate": {
            "value": 25,
            "rent": 20
        }
    },
    {
        "name": "Geopolitical Crisis",
        "description": "Escalating European war causes sharp fluctuations in energy and stock prices.",
        "effect_stock": [
            {"name": "VCB", "amount": -10},
            {"name": "VIC", "amount": -10},
            {"name": "FPT", "amount": -20},
            {"name": "GAS", "amount": -20},
            {"name": "SAB", "amount": -40},
        ],
        "effect_estate": {
            "value": 0,
            "rent": 0
        }
    },
    {
        "name": "Global Meltdown",
        "description": "A major hedge fund collapses, triggering a worldwide chain reaction.",
        "effect_stock": [
            {"name": "VCB", "amount": -10},
            {"name": "VIC", "amount": -10},
            {"name": "FPT", "amount": -25},
            {"name": "GAS", "amount": -25},
            {"name": "SAB", "amount": -35},
        ],
        "effect_estate": {
            "value": 0,
            "rent": 0
        }
    },
    {
        "name": "EVFTA Takes Effect",
        "description": "The EU-Vietnam Free Trade Agreement boosts exports.",
        "effect_stock": [
            {"name": "VCB", "amount": 15},
            {"name": "FPT", "amount": 15},
        ],
        "effect_estate": {
            "value": 0,
            "rent": 0
        }
    },
    {
        "name": "U.S.-China Trade War",
        "description": "Trade tensions drive global supply chains to shift toward Vietnam.",
        "effect_stock": [
            {"name": "FPT", "amount": 20},
            {"name": "GAS", "amount": 20},
        ],
        "effect_estate": {
            "value": 0,
            "rent": 0
        }
    },
    {
        "name": "Post-COVID Tourism Rebound",
        "description": "Tourism and logistics boom in the post-pandemic era.",
        "effect_stock": [
            {"name": "FPT", "amount": 20},
            {"name": "GAS", "amount": 20},
            {"name": "SAB", "amount": 20},
        ],
        "effect_estate": {
            "value": 0,
            "rent": 0
        }
    },
    {
        "name": "Vietnam Becomes Asia’s Factory Hub",
        "description": "Vietnam emerges as the new manufacturing hub, replacing China.",
        "effect_stock": [
            {"name": "FPT", "amount": 20},
            {"name": "GAS", "amount": 20},
            {"name": "SAB", "amount": 20},
        ],
        "effect_estate": {
            "value": 0,
            "rent": 0
        }
    },
    {
        "name": "MSCI Watchlist Upgrade",
        "description": "Vietnam is added to MSCI’s upgrade watchlist.",
        "effect_stock": [
            {"name": "VCB", "amount": 20},
            {"name": "VIC", "amount": 20},
            {"name": "FPT", "amount": 20},
            {"name": "GAS", "amount": 20},
            {"name": "SAB", "amount": 20},
        ],
        "effect_estate": {
            "value": 10,
            "rent": 10
        }
    }
]


# === CHANCE EVENTS ===
CHANCE_EVENTS = [
    {"name": "Skip 1 tax payment", "type": "bonus", "amount": 0},
    {"name": "Skip Jail", "type": "bonus", "amount": 0},
    {"name": "Win lottery +$600", "type": "plus", "amount": 600},
    {"name": "Inheritance +$500", "type": "plus", "amount": 500},
    
    {"name": "Pay another tax -$200", "type": "minus", "amount": 200},
    {"name": "Getting robbed at gunpoint -$100", "type": "minus", "amount": 100},
    {"name": "No dividend for 1 round", "type": "minus", "amount": 0},
    {"name": "Flagged for tax evasion and fined -$300", "type": "minus", "amount": 300},
    {"name": "Pay margin call -$100", "type": "minus", "amount": 100},
    {"name": "Sued for defamation -$100", "type": "minus", "amount": 100},
    {"name": "Emergency surgery medical fee -$200", "type": "minus", "amount": 200},
    {"name": "Scammed by 'get rich fast' course -$150", "type": "minus", "amount": 150},
    {"name": "All-in on Facebook stock tip -$150", "type": "minus", "amount": 150},
]

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