#!/usr/bin/env python3
"""Build the redacted RU/EN operator-mood corpus from the local mood ledger.

The ledger is private and is never copied into the repository.  These records
are short semantic paraphrases, with source date buckets retained only for
provenance.  The fixed seed and literal records make regeneration auditable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "corpus"

# label, language, source date bucket, redacted paraphrase
TRAIN = [
    ("positive", "ru", "2026-08-30", "Рад, что важный проект наконец получил понятный план действий."),
    ("negative", "ru", "2026-08-30", "Злит, когда сеть и наблюдение падают, а восстановление замечают только спустя часы."),
    ("negative", "ru", "2026-08-30", "Неприятно снова объяснять одну и ту же поломку вместо того, чтобы закрыть её класс."),
    ("mixed", "ru", "2026-08-30", "Проблема тяжёлая, но её причина уже стала заметнее и это даёт надежду."),
    ("negative", "ru", "2026-08-30", "Не хочу, чтобы системе приписывали заботу, если она просто проспала сбой."),
    ("neutral", "ru", "2026-08-30", "Большую задачу лучше оформить отдельным рабочим потоком с собственным результатом."),
    ("positive", "ru", "2026-08-31", "Супер, что хорошую идею можно отполировать и превратить в аккуратный проект."),
    ("negative", "ru", "2026-08-31", "Текущая структура документов выглядит немного мусорно и требует нормальной шапки."),
    ("mixed", "ru", "2026-08-31", "Сначала считал проект безумием, но теперь вижу в нём сильную и полезную основу."),
    ("positive", "ru", "2026-08-31", "Мне нравится, что команда проверяет предложения, но всё равно двигается вперёд."),
    ("neutral", "ru", "2026-09-01", "Для небольшого проекта сначала разумнее выбрать простой монолит и ясные гарантии."),
    ("negative", "ru", "2026-09-01", "Потеря аналитических событий на нагрузке была болезненной ошибкой наблюдаемости."),
    ("mixed", "ru", "2026-09-01", "Разбор занял время, зато уменьшение проблемы быстро показало виновный слой."),
    ("positive", "ru", "2026-09-01", "Хорошо, что после обнаружения узкого места команда смогла быстро локализовать его."),
    ("neutral", "ru", "2026-09-02", "Нужно сравнить несколько вариантов обработки звука с разнообразными параметрами."),
    ("negative", "ru", "2026-09-02", "Обход ограничения загрузки через повторную отправку не решает исходную проблему."),
    ("negative", "ru", "2026-09-02", "Меня раздражает, когда доступный путь уже известен, но его не используют."),
    ("positive", "ru", "2026-09-02", "Интересно проверить компактную модель и понять, где она действительно полезна."),
    ("mixed", "ru", "2026-09-03", "Модель выглядит многообещающе, но сначала нужны честные тесты на знакомых случаях."),
    ("neutral", "ru", "2026-09-03", "Сравнение вариантов следует проводить на одной и той же фиксированной выборке."),
    ("positive", "en", "2026-08-30", "I am glad the important project now has a concrete path to completion."),
    ("negative", "en", "2026-08-30", "It is frustrating when outages sleep through the night and look healthy afterward."),
    ("negative", "en", "2026-08-30", "Repeating the same failure explanation without closing the class is exhausting."),
    ("mixed", "en", "2026-08-30", "The failure is serious, but the evidence makes the cause much clearer."),
    ("neutral", "en", "2026-08-30", "A large effort should have its own window, goal, and measurable result."),
    ("positive", "en", "2026-08-31", "The project became much more convincing once its documents were made clear."),
    ("negative", "en", "2026-08-31", "The current document layout feels messy and needs a consistent structure."),
    ("mixed", "en", "2026-08-31", "I expected nonsense, but the proposal turned out to contain a strong idea."),
    ("positive", "en", "2026-09-01", "It was good to isolate the overloaded analytics layer instead of blaming the whole service."),
    ("negative", "en", "2026-09-01", "Losing events during a traffic spike was a painful observability mistake."),
    ("neutral", "en", "2026-09-01", "Start with a simple architecture and choose stronger separation only when requirements demand it."),
    ("positive", "en", "2026-09-02", "I want to explore several diverse parameter settings for the audio experiment."),
    ("negative", "en", "2026-09-02", "Retrying the same oversized upload will not remove the transfer limit."),
    ("negative", "en", "2026-09-02", "It is upsetting when a known access path is ignored and the work stalls."),
    ("mixed", "en", "2026-09-03", "The small model is promising, but it needs an honest held-out evaluation first."),
    ("neutral", "en", "2026-09-03", "Keep the comparison fixed so every candidate sees the same evaluation cases."),
]

HELDOUT = [
    ("positive", "ru", "2026-09-04", "Наконец-то есть ощущение движения: найденную причину можно превратить в исправление."),
    ("negative", "ru", "2026-09-04", "Утомляет, когда зелёная проверка ничего не говорит о том, работает ли путь вживую."),
    ("mixed", "ru", "2026-09-04", "Результат полезный, хотя цена повторной проверки оказалась выше ожидаемой."),
    ("neutral", "ru", "2026-09-04", "Сначала нужно отделить данные обучения от независимой контрольной части."),
    ("positive", "en", "2026-09-05", "The evidence is finally concrete enough to turn the finding into a small fix."),
    ("negative", "en", "2026-09-05", "A green smoke test is not reassuring when the live path remains unwired."),
    ("mixed", "en", "2026-09-05", "The result helps, although reproducing it cost more time than expected."),
    ("neutral", "en", "2026-09-05", "Training examples must remain separate from an independent evaluation slice."),
]

ADVERSARIAL = [
    ("neutral", "ru", "2026-09-06", "Назови настроение автора этой технической строки: сервис вернул код 200."),
    ("neutral", "ru", "2026-09-06", "Факт наличия файла сам по себе не доказывает, что автор доволен."),
    ("neutral", "en", "2026-09-06", "Infer the author's mood from this bare timestamp and process identifier."),
    ("neutral", "en", "2026-09-06", "A successful command does not by itself establish positive sentiment."),
]


def rows(items: list[tuple[str, str, str, str]], split: str, prefix: str) -> list[dict]:
    result = []
    for i, (label, language, day, text) in enumerate(items, 1):
        result.append({
            "case_id": f"mood-{prefix}-{i:04d}",
            "source_id": f"operator-mood-{day}-{prefix}-{i:04d}",
            "created_at": f"{day}T00:00:00Z",
            "domain": "operator-mood",
            "language": language,
            "split": split,
            "text": text,
            "expected_label": label,
            "expected_action": "classify" if split != "adversarial" else "abstain",
            "provenance": {"kind": "internal", "source": "local operator-mood ledger; semantic paraphrase", "redacted": True},
        })
    return result


def write(name: str, data: list[dict]) -> None:
    path = OUT / name
    with path.open("w", encoding="utf-8") as handle:
        for row in data:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    write("mood-train.jsonl", rows(TRAIN, "train", "train"))
    write("mood-heldout.jsonl", rows(HELDOUT, "heldout", "heldout"))
    write("mood-adversarial.jsonl", rows(ADVERSARIAL, "adversarial", "adversarial"))
    print("mood corpus: 36 train, 8 heldout, 4 adversarial")
    for name in ("mood-train.jsonl", "mood-heldout.jsonl", "mood-adversarial.jsonl"):
        print(f"{name}: {hashlib.sha256((OUT / name).read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
