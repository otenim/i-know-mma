# Weight Limits (MMA)
WEIGHT_LIMIT_ATOM = 47.6272
WEIGHT_LIMIT_STRAW = 52.1631
WEIGHT_LIMIT_FLY = 56.699
WEIGHT_LIMIT_BANTAM = 61.235
WEIGHT_LIMIT_FEATHER = 65.7709
WEIGHT_LIMIT_LIGHT = 70.3068
WEIGHT_LIMIT_SUPER_LIGHT = 74.8427
WEIGHT_LIMIT_WELTER = 77.1107
WEIGHT_LIMIT_SUPER_WELTER = 79.3786647
WEIGHT_LIMIT_MIDDLE = 83.9146
WEIGHT_LIMIT_SUPER_MIDDLE = 88.4505
WEIGHT_LIMIT_LIGHT_HEAVY = 92.9864
WEIGHT_LIMIT_CRUISER = 102.058
WEIGHT_LIMIT_HEAVY = 120.202


# Weight Classes (MMA)
WEIGHT_CLASS_ATOM = "atom"
WEIGHT_CLASS_STRAW = "straw"
WEIGHT_CLASS_FLY = "fly"
WEIGHT_CLASS_BANTAM = "bantam"
WEIGHT_CLASS_FEATHER = "feather"
WEIGHT_CLASS_LIGHT = "light"
WEIGHT_CLASS_SUPER_LIGHT = "super_light"
WEIGHT_CLASS_WELTER = "welter"
WEIGHT_CLASS_SUPER_WELTER = "super_welter"
WEIGHT_CLASS_MIDDLE = "middle"
WEIGHT_CLASS_SUPER_MIDDLE = "super_middle"
WEIGHT_CLASS_LIGHT_HEAVY = "light_heavy"
WEIGHT_CLASS_CRUISER = "cruiser"
WEIGHT_CLASS_HEAVY = "heavy"
WEIGHT_CLASS_SUPER_HEAVY = "super_heavy"
WEIGHT_CLASSES = [
    WEIGHT_CLASS_ATOM,
    WEIGHT_CLASS_STRAW,
    WEIGHT_CLASS_FLY,
    WEIGHT_CLASS_BANTAM,
    WEIGHT_CLASS_FEATHER,
    WEIGHT_CLASS_LIGHT,
    WEIGHT_CLASS_SUPER_LIGHT,
    WEIGHT_CLASS_WELTER,
    WEIGHT_CLASS_SUPER_WELTER,
    WEIGHT_CLASS_MIDDLE,
    WEIGHT_CLASS_SUPER_MIDDLE,
    WEIGHT_CLASS_LIGHT_HEAVY,
    WEIGHT_CLASS_CRUISER,
    WEIGHT_CLASS_HEAVY,
    WEIGHT_CLASS_SUPER_HEAVY,
]


# Expected values of weight classes
VALUES_WEIGHT_CLASS_ATOM = ["atomweight"]
VALUES_WEIGHT_CLASS_STRAW = ["strawweight"]
VALUES_WEIGHT_CLASS_FLY = ["flyweight"]
VALUES_WEIGHT_CLASS_BANTAM = ["bantamweight"]
VALUES_WEIGHT_CLASS_FEATHER = ["featherweight"]
VALUES_WEIGHT_CLASS_LIGHT = ["lightweight"]
VALUES_WEIGHT_CLASS_SUPER_LIGHT = ["super lightweight"]
VALUES_WEIGHT_CLASS_WELTER = ["welterweight"]
VALUES_WEIGHT_CLASS_SUPER_WELTER = ["super welterweight"]
VALUES_WEIGHT_CLASS_MIDDLE = ["middleweight"]
VALUES_WEIGHT_CLASS_SUPER_MIDDLE = ["super middleweight"]
VALUES_WEIGHT_CLASS_LIGHT_HEAVY = ["light heavyweight"]
VALUES_WEIGHT_CLASS_CRUISER = ["cruiserweight"]
VALUES_WEIGHT_CLASS_HEAVY = ["heavyweight"]
VALUES_WEIGHT_CLASS_SUPER_HEAVY = ["super heavyweight"]


# Sport
SPORT_MMA = "mma"
SPORT_KNUCKLE_MMA = "knuckle_mma"
SPORT_BOX = "box"
SPORT_KNUCKLE_BOX = "knuckle_box"
SPORT_KICK = "kick"
SPORT_MUAY = "muay"
SPORT_KARATE = "karate"
SPORT_SANDA = "sanda"
SPORT_LETHWEI = "lethwei"
SPORT_GRAPPLE = "grapple"
SPORT_SHOOT = "shoot"
SPORT_WRESTLE = "wrestle"
SPORT_SAMBO = "sambo"
SPORT_VALE = "vale"
SPORT_JUDO = "judo"
SPORT_COMBAT_JIU_JITSU = "combat_jiu_jitsu"
SPORT_CUSTOM = "custom"


# Expected values of sports
VALUES_SPORT_MMA = ["mma", "pancrase"]
VALUES_SPORT_KNUCKLE_MMA = ["knuckle_mma"]
VALUES_SPORT_BOX = ["boxing", "boxing_cage"]
VALUES_SPORT_KNUCKLE_BOX = ["knuckle"]
VALUES_SPORT_KICK = ["kickboxing"]
VALUES_SPORT_MUAY = ["muay"]
VALUES_SPORT_KARATE = ["karate"]
VALUES_SPORT_SANDA = ["sanda"]
VALUES_SPORT_LETHWEI = ["lethwei"]
VALUES_SPORT_GRAPPLE = ["grappling"]
VALUES_SPORT_SHOOT = ["shootboxing"]
VALUES_SPORT_WRESTLE = ["wrestling"]
VALUES_SPORT_SAMBO = ["sambo"]
VALUES_SPORT_VALE = ["valetudo"]
VALUES_SPORT_JUDO = ["judo"]
VALUES_SPORT_COMBAT_JIU_JITSU = ["combat_jj"]
VALUES_SPORT_CUSTOM = ["custom"]


# Billing of the match
BILLING_MAIN = "main"
BILLING_CO_MAIN = "co_main"
BILLING_MAIN_CARD = "main_card"
BILLING_PRELIM_CARD = "prelim_card"
BILLING_POSTLIM_CARD = "postlim_card"


# Expected values of billing
VALUES_BILLING_MAIN = ["main event"]
VALUES_BILLING_CO_MAIN = ["co-main event"]
VALUES_BILLING_MAIN_CARD = ["main card"]
VALUES_BILLING_PRELIM_CARD = ["preliminary card"]
VALUES_BILLING_POSTLIM_CARD = ["postlim"]


# Status of the match
STATUS_WIN = "win"
STATUS_LOSS = "loss"
STATUS_CANCELLED = "cancelled"
STATUS_DRAW = "draw"
STATUS_UPCOMING = "upcoming"
STATUS_NO_CONTEST = "no_contest"
STATUS_UNKNOWN = "unknown"


# Expected values of status
VALUES_STATUS_WIN = ["win"]
VALUES_STATUS_LOSS = ["loss"]
VALUES_STATUS_CANCELLED = ["cancelled", "cancelled bout"]
VALUES_STATUS_DRAW = ["draw"]
VALUES_STATUS_UPCOMING = ["upcoming", "confirmed upcoming bout"]
VALUES_STATUS_NO_CONTEST = ["no contest", "overturned to no contest"]
VALUES_STATUS_UNKNOWN = ["unknown"]


# Decision types
DECISION_TYPE_UNANIMOUS = "unanimous"
DECISION_TYPE_SPLIT = "split"
DECISION_TYPE_MAJORITY = "majority"
DECISION_TYPE_TIMELIMIT = "timelimit"
DECISION_TYPE_INJURY = "injury"
DECISION_TYPE_TECHNICAL = "technical"
DECISION_TYPE_POINTS = "points"
DECISION_TYPE_UNKNOWN = "unknown"


# Ended by
ENDED_BY_KO_TKO = "ko/tko"
ENDED_BY_SUBMISSION = "submission"
ENDED_BY_DECISION = "decision"


# Division of the match
DIVISION_PRO = "pro"
DIVISION_AM = "am"


# Expected values for "not available"
VALUES_NOT_AVAILABLE = ["n/a"]
