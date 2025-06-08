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
STOCKS = [
    {"name": "VCB", "price": 100, "min_price": 50, "max_price": 200},
    {"name": "VIC", "price": 100, "min_price": 50, "max_price": 200},
    {"name": "FPT", "price": 100, "min_price": 50, "max_price": 200},
    {"name": "GAS", "price": 100, "min_price": 50, "max_price": 200},
    {"name": "SAB", "price": 100, "min_price": 50, "max_price": 200},
]
# === ESTATES ===
ESTATES = [
    {"name": "Real Estate 1", "position": 18, "price": 100, "rent_price": 10},
    {"name": "Real Estate 2", "position": 16, "price": 200, "rent_price": 20},
    {"name": "Real Estate 3", "position": 14, "price": 300, "rent_price": 30},
    {"name": "Real Estate 4", "position": 11, "price": 400, "rent_price": 40},
    {"name": "Real Estate 5", "position": 1, "price": 500, "rent_price": 50},
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
    "Jail Visit", "Stock Corp B", "Shock event", "Savings", "Real estate 3", "Quizzes (Education)",
    "Real Estate 4", "Stock Corp C", "Chance", "Stock Corp D", "Jail (Challenge)", 
    "Stock Corp E", "Shock event","Tax Checkpoint", "Real Estate 5"
]

# === SHOCK EVENTS ===
SHOCK_EVENTS = [
    {
        "name": "Global Pandemic",
        "description": "Một biến thể virus mới khiến các thành phố phong tỏa. Nhà máy và sân bay đóng cửa.",
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
        "description": "Các ngân hàng và định chế tài chính sụp đổ, niềm tin thị trường lao dốc.",
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
        "description": "Hoa Kỳ áp thuế 46% lên hàng Việt Nam, công nghệ & năng lượng chịu ảnh hưởng.",
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
        "description": "Chiến tranh châu Âu leo thang khiến giá năng lượng và cổ phiếu biến động mạnh.",
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
        "description": "Quỹ đầu cơ lớn phá sản gây hiệu ứng lan truyền toàn cầu.",
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
        "description": "Hiệp định thương mại tự do EU-VN tạo cú hích xuất khẩu.",
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
        "description": "Chiến tranh thương mại khiến chuỗi cung ứng chuyển về Việt Nam.",
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
        "description": "Du lịch và logistics bùng nổ hậu đại dịch.",
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
        "description": "Việt Nam trở thành trung tâm sản xuất thay thế Trung Quốc.",
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
        "description": "Việt Nam được đưa vào danh sách chờ nâng hạng MSCI.",
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
    {"name": "Trúng số +600$", "type": "plus", "amount": 600},
    {"name": "Thừa kế +500$", "type": "plus", "amount": 500},
    {"name": "Nộp thuế -200$", "type": "minus", "amount": 200},
    {"name": "Bị cướp -100$", "type": "minus", "amount": 100},
    {"name": "Bị kiện phỉ báng -100$", "type": "minus", "amount": 100},
    {"name": "Bị gắn cờ trốn thuế -300$", "type": "minus", "amount": 300},
    {"name": "Trả viện phí -200$", "type": "minus", "amount": 200},
    {"name": "Khoá học lừa đảo -150$", "type": "minus", "amount": 150},
    {"name": "Cổ phiếu tất tay -150$", "type": "minus", "amount": 150},
    {"name": "Được miễn thuế vòng này", "type": "bonus", "amount": 0},
    {"name": "Miễn nhà tù", "type": "bonus", "amount": 0},
]
