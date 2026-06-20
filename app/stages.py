"""Фиксированный список из 29 этапов проекта (RU/EN).

Fixed list of the 29 project stages (RU/EN). The order is the canonical
workflow order; ``index`` is 1-based and stable — it is what is stored on
each project's stage rows.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    index: int
    ru: str
    en: str

    def name(self, lang: str) -> str:
        return self.en if lang == "en" else self.ru


STAGES: list[Stage] = [
    Stage(1, "Инспекция", "Inspection"),
    Stage(2, "Получение разрешения от здания и допуск рабочих", "Building permit & worker access"),
    Stage(3, "Защита общеиспользуемого пространства", "Protection of common areas"),
    Stage(4, "Демонтаж", "Demolition"),
    Stage(5, "Разметка", "Layout marking"),
    Stage(6, "Возведение гипсокартонных перегородок", "Drywall partition construction"),
    Stage(7, "Установка потолочных профилей", "Ceiling profile installation"),
    Stage(
        8, "Кондиционерные работы (в закрываемой части потолка)", "HVAC works (in enclosed ceiling)"
    ),
    Stage(9, "Подготовка потолочных коробов", "Ceiling bulkhead preparation"),
    Stage(10, "Электротехнические работы", "Electrical works"),
    Stage(
        11,
        "Водопроводные работы в туалетной и кухонной зонах",
        "Plumbing in toilet & kitchen areas",
    ),
    Stage(
        12,
        "Водозащитные работы и получение согласования от здания",
        "Waterproofing & building approval",
    ),
    Stage(13, "Бетонирование пола", "Floor concreting"),
    Stage(14, "Укладка плитки", "Tiling"),
    Stage(15, "Затирка и завершение отделочных работ в туалетах", "Grouting & toilet finishing"),
    Stage(16, "Подготовка к покраске (штукатурные работы)", "Paint prep (plastering)"),
    Stage(17, "Противопожарные работы", "Fireproofing works"),
    Stage(18, "Закрытие потолка", "Ceiling closing"),
    Stage(19, "Подготовка к покраске потолка", "Ceiling paint prep"),
    Stage(
        20,
        "Металлические воздуховоды в зонах с открытым потолком",
        "Metal ducts in open-ceiling areas",
    ),
    Stage(21, "Установка стеклянных перегородок", "Glass partition installation"),
    Stage(22, "Покраска потолка (1й слой)", "Ceiling painting (1st coat)"),
    Stage(23, "Укладка пола", "Flooring installation"),
    Stage(24, "Установка плинтусов", "Skirting installation"),
    Stage(25, "Итоговая окраска", "Final painting"),
    Stage(
        26, "Установка света и переключателей, розеток", "Lighting, switches & sockets installation"
    ),
    Stage(27, "Установка столярной мебели", "Joinery/millwork installation"),
    Stage(28, "Доставка и установка передвижной мебели", "Loose furniture delivery & installation"),
    Stage(
        29,
        "Получение сертификата соответствия и устранение недоделок",
        "Compliance certificate & snagging",
    ),
]

STAGE_COUNT = len(STAGES)
STAGE_BY_INDEX: dict[int, Stage] = {s.index: s for s in STAGES}


def stage_name(index: int, lang: str) -> str:
    stage = STAGE_BY_INDEX.get(index)
    return stage.name(lang) if stage else f"#{index}"
