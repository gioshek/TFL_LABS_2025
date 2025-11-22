from typing import List, Tuple, Optional
import random

# -------------------------
# Параметры теста
# -------------------------
TRIALS = 2000           # число случайных слов
MIN_LEN = 1             # минимальная длина слова
MAX_LEN = 25            # максимальная длина слова
MAX_REDUCE_STEPS = 1000 # максимальное число шагов редукции для одного слова
SHOW_EXAMPLES = 12      # сколько примеров несоответствий показывать
SEED = 123456           # фиксированный seed для воспроизводимости
ALPHABET = "ab"
# -------------------------

# -------------------------
# Исходная SRS (без правила baaabb -> ε, как в твоём отчёте)
# ориентируем по направлению lhs -> rhs (то, что у тебя в разделе "Исходная система (без ...)").
# -------------------------
T: List[Tuple[str, str]] = [
    ("bbb", "bab"),
    ("abab", "bab"),
    ("abba", "aba"),
    ("babb", "abb"),
    ("bbab", "bab"),
    ("aaaaa", "a"),
    ("aaaba", "bba"),
    ("aaaabb", "bb"),
    ("abaaaa", "abb"),
    ("abaaab", "ab"),
    ("baaaab", "bab"),
    ("bbaaaa", "bb"),
    ("bbaaab", "aaaab"),
    ("baabaab", "baaab"),
    ("babaaba", "bab"),
    ("babaabb", "babaaa"),
    ("baba", "aba"),
    ("bab", "ab"),
    ("aab", "ab"),
    ("aba", "ab"),
    ("abb", "ab"),
    ("bb", "ab"),
]

# -------------------------
# Минимальная SRS
# -------------------------
T_MIN: List[Tuple[str, str]] = [
    ("aaaaa", "a"),
    ("aba", "ab"),
    ("aab", "ab"),
    ("bab", "ab"),
    ("bb", "ab"),
]

# -------------------------
# Утилиты редукции
# -------------------------
def find_leftmost_longest_match(word: str, rules: List[Tuple[str, str]]) -> Optional[Tuple[int, str, str]]:
    """
    Ищет самое левое вхождение любого lhs в word.
    Если в одной позиции есть несколько LHS, возвращает самый длинный lhs.
    Возвращает кортеж (pos, lhs, rhs) или None если ни одно правило не применимо.
    """
    n = len(word)
    best = None  # (pos, lhs, rhs)
    for lhs, rhs in rules:
        if not lhs:
            continue
        start = 0
        while True:
            i = word.find(lhs, start)
            if i == -1:
                break
            if best is None or i < best[0] or (i == best[0] and len(lhs) > len(best[1])):
                best = (i, lhs, rhs)
            # ищем дальше, т.к. может быть в той же позиции ещё более длинный lhs
            start = i + 1
    return best

def apply_one_step(word: str, rules: List[Tuple[str, str]]) -> Optional[str]:
    """
    Применяет один шаг редукции: находит leftmost-longest совпадение и заменяет lhs->rhs.
    Если ни одно правило не применимо, возвращает None.
    """
    m = find_leftmost_longest_match(word, rules)
    if m is None:
        return None
    pos, lhs, rhs = m
    new = word[:pos] + rhs + word[pos + len(lhs):]
    return new

def reduce_to_nf(word: str, rules: List[Tuple[str, str]], max_steps: int = 1000) -> Tuple[str, bool, List[str]]:
    """
    Редуцирует слово по правилам rules до нормальной формы по выбранной стратегии.
    Возвращает (nf, finished_flag, trace)
      - nf: полученная строка после остановки (либо при достижении max_steps)
      - finished_flag: True если достигли состояния, где правила не применимы
      - trace: список шагов редукции (включая начальное слово). Ограничен по длине.
    """
    cur = word
    trace = [cur]
    for step in range(max_steps):
        nxt = apply_one_step(cur, rules)
        if nxt is None:
            return cur, True, trace
        cur = nxt
        trace.append(cur)
    # если вышли по лимиту шагов — считаем, что не завершилось
    return cur, False, trace

# -------------------------
# Функция сравнения двух систем
# -------------------------
def compare_systems(word: str) -> Tuple[bool, dict]:
    """
    Редуцирует слово по обеим системам и сравнивает результаты.
    Возвращает (equal, info) где info содержит подробности.
    """
    nf_orig, ok_orig, trace_orig = reduce_to_nf(word, T, MAX_REDUCE_STEPS)
    nf_min, ok_min, trace_min = reduce_to_nf(word, T_MIN, MAX_REDUCE_STEPS)

    equal = (ok_orig and ok_min and nf_orig == nf_min)
    info = {
        "word": word,
        "nf_orig": nf_orig,
        "ok_orig": ok_orig,
        "steps_orig": len(trace_orig) - 1,
        "trace_orig": trace_orig,
        "nf_min": nf_min,
        "ok_min": ok_min,
        "steps_min": len(trace_min) - 1,
        "trace_min": trace_min,
    }
    # если хотя бы одна система не закончила (ok_* == False), считаем это отдельным типом
    return equal, info

# -------------------------
# Генератор случайных слов
# -------------------------
def random_word(rng: random.Random, min_len: int, max_len: int) -> str:
    l = rng.randint(min_len, max_len)
    return ''.join(rng.choice(ALPHABET) for _ in range(l))

# -------------------------
# Main fuzz loop
# -------------------------
def run_fuzz(trials: int = TRIALS):
    rng = random.Random(SEED)
    successes = 0
    failures = 0
    non_terminating = 0
    examples = []

    for t in range(trials):
        w = random_word(rng, MIN_LEN, MAX_LEN)
        equal, info = compare_systems(w)
        if equal:
            successes += 1
        else:
            # считаем как failure, но фиксируем случаи не завершения отдельно
            failures += 1
            if not info["ok_orig"] or not info["ok_min"]:
                non_terminating += 1
            if len(examples) < SHOW_EXAMPLES:
                examples.append(info)

    # Вывод результатов
    print("Fuzz-equivalence test")
    print("=====================")
    print(f"Trials           : {trials}")
    print(f"Successes (match): {successes}")
    print(f"Failures         : {failures}")
    print(f"  of failures due to non-termination (step limit): {non_terminating}")
    print()
    if examples:
        print("Sample counterexamples (up to {}):".format(SHOW_EXAMPLES))
        for idx, ex in enumerate(examples, 1):
            print(f"\n--- Example #{idx} ---")
            print("start word :", ex["word"])
            print("orig nf    :", ex["nf_orig"], "(finished)" if ex["ok_orig"] else "(NOT finished)")
            print("min  nf    :", ex["nf_min"], "(finished)" if ex["ok_min"] else "(NOT finished)")
            print("orig steps :", ex["steps_orig"], "min steps:", ex["steps_min"])
            # короткие трассы: показываем до 20 шагов; если длиннее — сокращаем
            def show_trace(tr):
                if len(tr) <= 20:
                    return " -> ".join(repr(s) for s in tr)
                else:
                    head = " -> ".join(repr(s) for s in tr[:8])
                    tail = " -> ".join(repr(s) for s in tr[-8:])
                    return head + " ... " + tail
            print("trace orig : ", show_trace(ex["trace_orig"]))
            print("trace min  : ", show_trace(ex["trace_min"]))
    else:
        print("No counterexamples found.")

    # краткий вердикт
    if failures == 0:
        print("\n✅ All tested words reduced to the same normal form under both systems.")
    else:
        print(f"\n⚠️  Found {failures} mismatches in {trials} trials. "
              "Посмотри примеры выше, чтобы понять, где системы различаются.")


if __name__ == "__main__":
    run_fuzz(TRIALS)
