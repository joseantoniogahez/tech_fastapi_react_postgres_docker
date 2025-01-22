from enum import Enum, unique


@unique
class BookStatus(str, Enum):
    PUBLISHED = "published"
    DRAFT = "draft"
