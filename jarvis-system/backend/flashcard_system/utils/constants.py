"""Constants used throughout the flashcard system."""

# SM-2 Algorithm Constants
SM2_CONSTANTS = {
    "EASE_FACTOR_MIN": 1.3,
    "EASE_FACTOR_MAX": 2.5,
    "EASE_FACTOR_DEFAULT": 2.5,
    "EASE_FACTOR_DECREMENT": 0.2,
    "EASE_FACTOR_INCREMENT": 0.1,
    "MINIMUM_QUALITY_FOR_EASE_INCREMENT": 3,
    "MINIMUM_QUALITY_FOR_EASE_DECREMENT": 3,
}

# Study Constants
STUDY_CONSTANTS = {
    "DAILY_CARD_LIMIT": 50,
    "NEW_CARD_LIMIT": 20,
    "REVIEW_CARD_LIMIT": 30,
    "STUDY_SESSION_TIMEOUT_MINUTES": 60,
    "MAX_STUDY_SESSION_DURATION_MINUTES": 120,
    "BREAK_INTERVAL_MINUTES": 25,
}

# API Constants
API_CONSTANTS = {
    "MAX_CARDS_PER_REQUEST": 100,
    "MAX_BATCH_SIZE": 1000,
    "REQUEST_TIMEOUT_SECONDS": 30,
    "RATE_LIMIT_REQUESTS_PER_MINUTE": 100,
}

# Card Status Constants
CARD_STATUSES = {
    "NEW": "new",
    "LEARNING": "learning",
    "REVIEW": "review",
    "SUSPENDED": "suspended",
    "BURIED": "buried",
}

# Review Type Constants
REVIEW_TYPES = {
    "AGAIN": 1,          # Card failed, needs relearning
    "HARD": 2,           # Card was difficult
    "GOOD": 3,           # Card was correct
    "EASY": 4,           # Card was easy/too easy
    "AGAIN_QUALITY": 0,
    "HARD_QUALITY": 2,
    "GOOD_QUALITY": 3,
    "EASY_QUALITY": 4,
}

# Quality Rating Constants
QUALITY_RATINGS = {
    "COMPLETE_BLACKOUT": 0,
    "INCORRECT_WITH_SIGNIFICANT_ERROR": 1,
    "INCORRECT_BUT_RECALLED": 2,
    "CORRECT_WITH_DIFFICULTY": 3,
    "CORRECT_WITH_HESITATION": 4,
    "PERFECT": 5,
}

# WebSocket Constants
WEBSOCKET_CONSTANTS = {
    "HEARTBEAT_INTERVAL": 30,
    "CONNECTION_TIMEOUT": 60,
    "MAX_MESSAGE_SIZE": 1000000,  # 1MB
}

# Cache Constants
CACHE_CONSTANTS = {
    "EMBEDDINGS_CACHE_DIR": "./cache/embeddings",
    "CACHE_EXPIRY_HOURS": 24,
    "MAX_CACHE_SIZE_MB": 1000,
}

# LLM Constants
LLM_CONSTANTS = {
    "DEFAULT_MODEL": "neural-chat",
    "EMBEDDING_MODEL": "all-minilm",
    "TEMPERATURE": 0.7,
    "MAX_TOKENS": 2000,
    "TOP_P": 0.9,
}

# Error Messages
ERROR_MESSAGES = {
    "CARD_NOT_FOUND": "Flashcard not found",
    "INVALID_CARD_DATA": "Invalid card data provided",
    "DATABASE_ERROR": "Database operation failed",
    "GENERATION_ERROR": "Failed to generate flashcard",
    "RETRIEVAL_ERROR": "Failed to retrieve flashcard",
    "REVIEW_ERROR": "Failed to process review",
    "UNAUTHORIZED": "Unauthorized access",
    "RATE_LIMITED": "Rate limit exceeded",
}

# Success Messages
SUCCESS_MESSAGES = {
    "CARD_CREATED": "Flashcard created successfully",
    "CARD_UPDATED": "Flashcard updated successfully",
    "CARD_DELETED": "Flashcard deleted successfully",
    "REVIEW_RECORDED": "Review recorded successfully",
    "BATCH_PROCESSED": "Batch processed successfully",
}
