import random
from typing import List, Tuple, Optional, Set


# ---------------------------------------------------------
# Минимальная SRS
# ---------------------------------------------------------
RULES: List[Tuple[str, str]] = [
    ("aaaaa", "a"),
    ("aba", "ab"),
    ("aab", "ab"),
    ("bab", "ab"),
    ("bb", "ab"),
]


# ---------------------------------------------------------
# Инварианты
# ---------------------------------------------------------

def has_b(word: str) -> int:
    """Инвариант 1 — наличие хотя бы одного символа b."""
    return int("b" in word)


def a_mod4_if_no_b(word: str) -> Optional[int]:
    """Инвариант 2 — |w|_a mod 4, если слово без b. Иначе None."""
    if "b" in word:
        return None
    return len(word) % 4


def end_b_nf(word: str) -> Optional[str]:
    """
    Инвариант 3:
    Если |w| >= 2 и заканчивается на 'b', нормальная форма обязана быть 'ab'.
    Во всех остальных случаях инвариант не определён.
    """
    if len(word) >= 2 and word.endswith("b"):
        return "ab"
    return None


# ---------------------------------------------------------
# Редукция до нормальной формы
# ---------------------------------------------------------

def normal_form(word: str) -> str:
    """
    Применяет правила минимальной SRS, пока возможно.
    Порядок применения — жадный слева направо, но это допустимо,
    потому что минимальная система конфлюэнтна.
    """
    changed = True
    while changed:
        changed = False
        for lhs, rhs in RULES:
            pos = word.find(lhs)
            if pos != -1:
                word = word[:pos] + rhs + word[pos + len(lhs):]
                changed = True
                break
    return word


# ---------------------------------------------------------
# Объединённый объект инвариантов
# ---------------------------------------------------------

class Inv:
    def __init__(self, word: str):
        self.has_b = has_b(word)
        self.mod4 = a_mod4_if_no_b(word)
        self.end_b = end_b_nf(word)
        self.nf = normal_form(word)

    def ok_vs(self, other: "Inv") -> bool:
        """Проверяет совпадение всех определённых инвариантов."""
        if self.has_b != other.has_b:
            return False

        if self.mod4 is not None and other.mod4 is not None:
            if self.mod4 != other.mod4:
                return False

        if self.end_b is not None:
            if other.nf != "ab":
                return False

        return True

    def __repr__(self):
        return f"(has_b={self.has_b}, mod4={self.mod4}, end_b={self.end_b}, nf={self.nf})"


# ---------------------------------------------------------
# Генерация соседей
# ---------------------------------------------------------

def neighbors(word: str, rules=RULES) -> List[str]:
    outs: Set[str] = set()

    for lhs, rhs in rules:
        # lhs → rhs
        start = 0
        while True:
            pos = word.find(lhs, start)
            if pos == -1:
                break
            outs.add(word[:pos] + rhs + word[pos+len(lhs):])
            start = pos + 1

        # rhs → lhs
        start = 0
        while True:
            pos = word.find(rhs, start)
            if pos == -1:
                break
            outs.add(word[:pos] + lhs + word[pos+len(rhs):])
            start = pos + 1

    outs.discard(word)
    return list(outs)


# ---------------------------------------------------------
# Генерация случайных слов и цепочек
# ---------------------------------------------------------

def random_word(min_len=3, max_len=14) -> str:
    L = random.randint(min_len, max_len)
    return "".join(random.choice("ab") for _ in range(L))


def random_chain(start: str, steps_min=3, steps_max=15) -> List[str]:
    w = start
    chain = [w]
    steps = random.randint(steps_min, steps_max)

    for _ in range(steps):
        neigh = neighbors(w)
        if not neigh:
            return chain
        w = random.choice(neigh)
        chain.append(w)

    return chain


# ---------------------------------------------------------
# Проверка цепочки
# ---------------------------------------------------------

def check_chain(chain: List[str]):
    base = Inv(chain[0])
    for w in chain[1:]:
        cur = Inv(w)
        if not base.ok_vs(cur):
            return False, base, cur, w
    return True, base, None, None


# ---------------------------------------------------------
# Fuzz-тест
# ---------------------------------------------------------

def fuzz(trials=5000):
    ok = 0
    fail = 0
    examples = []

    for _ in range(trials):
        w0 = random_word()
        chain = random_chain(w0)
        good, base, bad, wbad = check_chain(chain)

        if good:
            ok += 1
        else:
            fail += 1
            examples.append(
                f"FAIL: base={base}, bad={bad}, wbad='{wbad}', chain={chain}"
            )

    return ok, fail, examples


if __name__ == "__main__":
    print("=== Метаморфное тестирование минимальной SRS ===")
    ok, fail, examples = fuzz()
    print(f"Successful chains: {ok}")
    print(f"Failed chains:     {fail}")

    if fail > 0:
        print("\n--- Examples ---")
        for e in examples[:10]:
            print(e)
