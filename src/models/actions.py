"""
Test Action Models
Her test aksiyonu için Pydantic modelleri tanımlar.
"""

from typing import Optional, Union, Any
from pydantic import BaseModel, Field


class GotoAction(BaseModel):
    """Belirtilen URL'ye git"""
    url: str = Field(..., description="Gidilecek URL")


class FillAction(BaseModel):
    """Form alanını doldur"""
    label: Optional[str] = Field(None, description="Label metni ile arama")
    placeholder: Optional[str] = Field(None, description="Placeholder metni ile arama")
    selector: Optional[str] = Field(None, description="CSS selector")
    value: str = Field(..., description="Girilecek değer")


class ClickAction(BaseModel):
    """Elemente tıkla"""
    text: Optional[str] = Field(None, description="Buton/link metni")
    selector: Optional[str] = Field(None, description="CSS selector")
    label: Optional[str] = Field(None, description="Aria-label değeri")


class SelectAction(BaseModel):
    """Dropdown'dan seçim yap"""
    label: Optional[str] = Field(None, description="Select box label'ı")
    selector: Optional[str] = Field(None, description="CSS selector")
    option: str = Field(..., description="Seçilecek option değeri")


class AssertUrlNotContainsAction(BaseModel):
    """URL'nin belirtilen metni içermediğini doğrula"""
    fragment: str = Field(..., description="URL'de olmaması gereken metin")


class AssertUrlContainsAction(BaseModel):
    """URL'nin belirtilen metni içerdiğini doğrula"""
    fragment: str = Field(..., description="URL'de olması gereken metin")


class WaitAction(BaseModel):
    """Bekle"""
    seconds: Optional[float] = Field(None, description="Saniye cinsinden bekleme süresi")
    for_element: Optional[str] = Field(None, description="Element görünene kadar bekle")
    for_url_contains: Optional[str] = Field(None, description="URL belirtilen metni içerene kadar bekle")


class ScreenshotAction(BaseModel):
    """Ekran görüntüsü al"""
    name: str = Field(..., description="Screenshot dosya adı")
    full_page: bool = Field(False, description="Tam sayfa screenshot")


# Action Union Type - Tüm action türlerini birleştiren union
ActionType = Union[
    GotoAction,
    FillAction,
    ClickAction,
    SelectAction,
    AssertUrlNotContainsAction,
    AssertUrlContainsAction,
    WaitAction,
    ScreenshotAction
] 