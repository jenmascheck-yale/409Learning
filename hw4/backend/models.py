"""Pydantic structured types for the Campus Customs agent and API."""

from pydantic import BaseModel


class ProductCard(BaseModel):
    """A product the chat can show on the page. Problem 7 fills these from a
    catalogue search; defined here so the reply type is ready for it."""

    product_id: str
    name: str
    price: float
    garment_type: str
    image_url: str
    description: str


class ChatReply(BaseModel):
    """What the /api/chat route returns to the website."""

    reply: str
    products: list[ProductCard] = []


# --- Problem 6: return types for the agent's database lookup tools ---


class ProductDescription(BaseModel):
    """Result of the description lookup tool."""

    product_id: str
    name: str
    garment_type: str
    description: str


class ProductPrice(BaseModel):
    """Result of the price lookup tool."""

    product_id: str
    name: str
    price: float


class SizeStock(BaseModel):
    """Stock for one size. `in_stock` is False and the agent should say
    'sold out' when quantity is 0."""

    size: str
    quantity: int
    in_stock: bool


class ProductStock(BaseModel):
    """Result of the stock lookup tool: stock for one size (when the shopper
    names a size) or every size."""

    product_id: str
    name: str
    sizes: list[SizeStock]


class CategoryCount(BaseModel):
    """A garment category and how many products it has (browse-categories tool)."""

    category: str
    count: int
