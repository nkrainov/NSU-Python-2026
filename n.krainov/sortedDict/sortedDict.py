from typing import Generic, Optional, TypeVar, runtime_checkable, Protocol, Any, Iterator
from dataclasses import dataclass
from enum import Enum
from collections import OrderedDict
import time


class Color(Enum):
    RED = 1
    BLACK = 2


@runtime_checkable
class SupportsLessAndEqThan(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...


K = TypeVar("K", bound=SupportsLessAndEqThan)
T = TypeVar("T")


@dataclass
class SortedDictStats:
    insert_count: int
    insert_find_avg_us: float
    insert_rebalance_avg_us: float
    insert_total_avg_us: float
    get_count: int
    get_find_avg_us: float
    get_total_avg_us: float
    delete_count: int
    delete_find_avg_us: float
    delete_rebalance_avg_us: float
    delete_total_avg_us: float

    cache_hits: int
    cache_misses: int

    def __str__(self) -> str:
        lines = [
            "═" * 54,
            "  SortedDict — operation statistics",
            "═" * 54,
            f"  {'Operation':<30} {'Count':>7}  {'Avg time (μs)':>15}",
            "─" * 54,
            f"  {'Insert (total)':<30} {self.insert_count:>7}  {self.insert_total_avg_us:>15.2f}",
            f"    {'· node search':<28} {'':>7}  {self.insert_find_avg_us:>15.2f}",
            f"    {'· rebalancing':<28} {'':>7}  {self.insert_rebalance_avg_us:>15.2f}",
            "─" * 54,
            f"  {'Get (total)':<30} {self.get_count:>7}  {self.get_total_avg_us:>15.2f}",
            f"    {'· node search':<28} {'':>7}  {self.get_find_avg_us:>15.2f}",
            "─" * 54,
            f"  {'Delete (total)':<30} {self.delete_count:>7}  {self.delete_total_avg_us:>15.2f}",
            f"    {'· node search':<28} {'':>7}  {self.delete_find_avg_us:>15.2f}",
            f"    {'· rebalancing':<28} {'':>7}  {self.delete_rebalance_avg_us:>15.2f}",
            "─" * 54,
            f"  Cache: hits={self.cache_hits}, misses={self.cache_misses}",
            "═" * 54,
        ]
        return "\n".join(lines)


class SortedDictNode(Generic[K, T]):
    def __init__(self, key: Optional[K] = None, value: Optional[T] = None):
        self.key: Optional[K] = key
        self.value: Optional[T] = value
        self.color: Color = Color.RED
        self.rightChild: Optional[SortedDictNode[K, T]] = None
        self.leftChild: Optional[SortedDictNode[K, T]] = None
        self.parent: Optional[SortedDictNode[K, T]] = None
        self._counter: int = 0

    def increment(self):
        self._counter += 1


class SortedDict(Generic[K, T]):
    def __init__(self, seq: Optional[list[tuple[K, T]]] = None, cache_size: int = 1024) -> None:
        self._counterInsertRebalance: int = 0
        self._counterDeleteRebalance: int = 0

        self._noneNode: SortedDictNode[K, T] = SortedDictNode[K, T]()
        self._noneNode.color = Color.BLACK
        self._noneNode.leftChild = self._noneNode
        self._noneNode.rightChild = self._noneNode
        self._noneNode.parent = self._noneNode

        self._root: SortedDictNode[K, T] = self._noneNode

        self._cache_size: int = cache_size
        self._cache: OrderedDict[int, None] = OrderedDict()
        self._cache_hits: int = 0
        self._cache_misses: int = 0

        self._insert_count: int = 0
        self._insert_find_total_ns: int = 0
        self._insert_rebalance_total_ns: int = 0
        self._insert_rebalance_count: int = 0
        self._insert_total_ns: int = 0

        self._get_count: int = 0
        self._get_find_total_ns: int = 0
        self._get_total_ns: int = 0

        self._delete_count: int = 0
        self._delete_find_total_ns: int = 0
        self._delete_rebalance_total_ns: int = 0
        self._delete_rebalance_count: int = 0
        self._delete_total_ns: int = 0

        if seq is not None:
            for pair in seq:
                self[pair[0]] = pair[1]

    def get_stats(self) -> SortedDictStats:

        def _avg_us(total_ns: int, count: int) -> float:
            return (total_ns / count / 1_000) if count > 0 else 0.0

        return SortedDictStats(
            insert_count=self._insert_count,
            insert_find_avg_us=_avg_us(self._insert_find_total_ns, self._insert_count),
            insert_rebalance_avg_us=_avg_us(self._insert_rebalance_total_ns, self._insert_rebalance_count),
            insert_total_avg_us=_avg_us(self._insert_total_ns, self._insert_count),

            get_count=self._get_count,
            get_find_avg_us=_avg_us(self._get_find_total_ns, self._get_count),
            get_total_avg_us=_avg_us(self._get_total_ns, self._get_count),

            delete_count=self._delete_count,
            delete_find_avg_us=_avg_us(self._delete_find_total_ns, self._delete_count),
            delete_rebalance_avg_us=_avg_us(self._delete_rebalance_total_ns, self._delete_rebalance_count),
            delete_total_avg_us=_avg_us(self._delete_total_ns, self._delete_count),

            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
        )

    def reset_stats(self) -> None:
        self._insert_count = 0
        self._insert_find_total_ns = 0
        self._insert_rebalance_total_ns = 0
        self._insert_rebalance_count = 0
        self._insert_total_ns = 0

        self._get_count = 0
        self._get_find_total_ns = 0
        self._get_total_ns = 0

        self._delete_count = 0
        self._delete_find_total_ns = 0
        self._delete_rebalance_total_ns = 0
        self._delete_rebalance_count = 0
        self._delete_total_ns = 0

        self._cache_hits = 0
        self._cache_misses = 0

    def _record_access(self, node: SortedDictNode[K, T]) -> None:
        if node is self._noneNode:
            return
        node.increment()
        node_id = id(node)
        if node_id in self._cache:
            self._cache_hits += 1
            self._cache.move_to_end(node_id)
        else:
            self._cache_misses += 1
            if len(self._cache) >= self._cache_size:
                self._cache.popitem(last=False)
            self._cache[node_id] = None

    def get_cache_stats(self) -> tuple[int, int]:
        return self._cache_hits, self._cache_misses

    def reset_cache_stats(self) -> None:
        self._cache_hits = 0
        self._cache_misses = 0

    def _findNode(self, key: K) -> Optional[SortedDictNode[K, T]]:
        node = self._root
        while node != self._noneNode:
            self._record_access(node)
            assert node.key is not None
            if node.key == key:
                return node
            if node.key < key:
                node = node.rightChild
            else:
                node = node.leftChild
        return None

    def _findNodeWithParent(self, key: K) -> tuple[Optional[SortedDictNode[K, T]], SortedDictNode[K, T]]:
        parent = self._noneNode
        node = self._root
        while node != self._noneNode:
            self._record_access(node)
            assert node.key is not None
            if node.key == key:
                return node, parent
            parent = node
            if node.key < key:
                node = node.rightChild
            else:
                node = node.leftChild
        return None, parent

    def __getitem__(self, key: K) -> T:
        t0 = time.perf_counter_ns()

        t_find0 = time.perf_counter_ns()
        node: Optional[SortedDictNode[K, T]] = self._findNode(key)
        t_find1 = time.perf_counter_ns()

        if node is None:
            raise KeyError("dict doesn't have key " + str(key))
        assert node.value is not None

        t1 = time.perf_counter_ns()

        self._get_count += 1
        self._get_find_total_ns += t_find1 - t_find0
        self._get_total_ns += t1 - t0

        return node.value

    def __setitem__(self, key: K, value: T) -> None:
        t0 = time.perf_counter_ns()

        t_find0 = time.perf_counter_ns()
        existedNode, parent = self._findNodeWithParent(key)
        t_find1 = time.perf_counter_ns()

        self._insert_count += 1
        self._insert_find_total_ns += t_find1 - t_find0

        if existedNode is not None:
            existedNode.value = value
            self._insert_total_ns += time.perf_counter_ns() - t0
            return

        newNode = SortedDictNode[K, T](key, value)
        newNode.leftChild = self._noneNode
        newNode.rightChild = self._noneNode
        newNode.parent = self._noneNode
        newNode.parent = parent

        if parent == self._noneNode:
            self._root = newNode
        elif newNode.key < parent.key:
            parent.leftChild = newNode
        else:
            parent.rightChild = newNode

        t_rb0 = time.perf_counter_ns()
        self._insertRebalance(newNode)
        t_rb1 = time.perf_counter_ns()

        self._insert_rebalance_total_ns += t_rb1 - t_rb0
        self._insert_rebalance_count += 1
        self._insert_total_ns += time.perf_counter_ns() - t0

    def __delitem__(self, key: K) -> None:
        t0 = time.perf_counter_ns()

        t_find0 = time.perf_counter_ns()
        node = self._findNode(key)
        t_find1 = time.perf_counter_ns()

        if node is None:
            raise KeyError("dict doesn't have key " + str(key))

        self._delete_count += 1
        self._delete_find_total_ns += t_find1 - t_find0

        delNode = node
        nodeForFixup = node
        fixupParent = self._noneNode
        originalColor = node.color

        if node.leftChild == self._noneNode:
            nodeForFixup = node.rightChild
            fixupParent = node.parent
            self._replaceNodes(node, node.rightChild)
        elif node.rightChild == self._noneNode:
            nodeForFixup = node.leftChild
            fixupParent = node.parent
            self._replaceNodes(node, node.leftChild)
        else:
            delNode = self._minimum(node.rightChild)
            originalColor = delNode.color
            nodeForFixup = delNode.rightChild

            if delNode.parent == node:
                fixupParent = delNode
            else:
                self._replaceNodes(delNode, delNode.rightChild)
                delNode.rightChild = node.rightChild
                delNode.rightChild.parent = delNode
                fixupParent = delNode.parent

            self._replaceNodes(node, delNode)
            delNode.leftChild = node.leftChild
            delNode.leftChild.parent = delNode
            delNode.color = node.color

        if originalColor == Color.BLACK:
            self._counterDeleteRebalance += 1
            t_rb0 = time.perf_counter_ns()
            self._deleteRebalance(nodeForFixup, fixupParent)
            t_rb1 = time.perf_counter_ns()
            self._delete_rebalance_total_ns += t_rb1 - t_rb0
            self._delete_rebalance_count += 1

        self._delete_total_ns += time.perf_counter_ns() - t0


    def _insertRebalance(self, newNode: SortedDictNode[K, T]) -> None:
        node = newNode
        flag = True
        while node.parent.color == Color.RED:
            if flag:
                flag = False
                self._counterInsertRebalance += 1

            self._record_access(node)
            self._record_access(node.parent)
            self._record_access(node.parent.parent)

            if node.parent == node.parent.parent.leftChild:
                uncle = node.parent.parent.rightChild
                self._record_access(uncle)

                if uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    node = node.parent.parent
                    self._record_access(node)
                else:
                    if node == node.parent.rightChild:
                        node = node.parent
                        self._left_rotate(node)
                        self._record_access(node)
                    node.parent.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    self._right_rotate(node.parent.parent)
                    self._record_access(node.parent.parent)
            else:
                uncle = node.parent.parent.leftChild
                self._record_access(uncle)

                if uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    node = node.parent.parent
                    self._record_access(node)
                else:
                    if node == node.parent.leftChild:
                        node = node.parent
                        self._right_rotate(node)
                        self._record_access(node)
                    node.parent.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    self._left_rotate(node.parent.parent)
                    self._record_access(node.parent.parent)
        self._root.color = Color.BLACK
        self._record_access(self._root)

    def _left_rotate(self, node: SortedDictNode[K, T]) -> None:
        self._record_access(node)
        rightChild = node.rightChild
        self._record_access(rightChild)

        node.rightChild = rightChild.leftChild
        if rightChild.leftChild != self._noneNode:
            rightChild.leftChild.parent = node
            self._record_access(rightChild.leftChild)

        rightChild.parent = node.parent
        if node.parent == self._noneNode:
            self._root = rightChild
        elif node == node.parent.leftChild:
            node.parent.leftChild = rightChild
        else:
            node.parent.rightChild = rightChild

        rightChild.leftChild = node
        node.parent = rightChild

    def _right_rotate(self, node: SortedDictNode[K, T]) -> None:
        self._record_access(node)
        leftChild = node.leftChild
        self._record_access(leftChild)

        node.leftChild = leftChild.rightChild
        if leftChild.rightChild != self._noneNode:
            leftChild.rightChild.parent = node
            self._record_access(leftChild.rightChild)

        leftChild.parent = node.parent
        if node.parent == self._noneNode:
            self._root = leftChild
        elif node == node.parent.rightChild:
            node.parent.rightChild = leftChild
        else:
            node.parent.leftChild = leftChild

        leftChild.rightChild = node
        node.parent = leftChild

    def _replaceNodes(self, u: SortedDictNode[K, T], v: SortedDictNode[K, T]) -> None:
        if u.parent == self._noneNode:
            self._root = v
        elif u == u.parent.leftChild:
            u.parent.leftChild = v
        else:
            u.parent.rightChild = v
        if v != self._noneNode:
            v.parent = u.parent

    def _minimum(self, u: SortedDictNode[K, T]) -> SortedDictNode[K, T]:
        node = u
        while node.leftChild != self._noneNode:
            node = node.leftChild
        return node

    def _deleteRebalance(self, nodeForFixup: SortedDictNode[K, T], parent: SortedDictNode[K, T]) -> None:
        brother = nodeForFixup
        while nodeForFixup != self._root and nodeForFixup.color == Color.BLACK:
            if nodeForFixup == parent.leftChild:
                brother = parent.rightChild
                if brother.color == Color.RED:
                    brother.color = Color.BLACK
                    parent.color = Color.RED
                    self._left_rotate(parent)
                    brother = parent.rightChild
                if brother.leftChild.color == Color.BLACK and brother.rightChild.color == Color.BLACK:
                    brother.color = Color.RED
                    nodeForFixup = parent
                    parent = parent.parent
                else:
                    if brother.rightChild.color == Color.BLACK:
                        brother.leftChild.color = Color.BLACK
                        brother.color = Color.RED
                        self._right_rotate(brother)
                        brother = parent.rightChild
                    brother.color = parent.color
                    parent.color = Color.BLACK
                    brother.rightChild.color = Color.BLACK
                    self._left_rotate(parent)
                    nodeForFixup = self._root
                    parent = self._noneNode
            else:
                brother = parent.leftChild
                if brother.color == Color.RED:
                    brother.color = Color.BLACK
                    parent.color = Color.RED
                    self._right_rotate(parent)
                    brother = parent.leftChild
                if brother.rightChild.color == Color.BLACK and brother.leftChild.color == Color.BLACK:
                    brother.color = Color.RED
                    nodeForFixup = parent
                    parent = parent.parent
                else:
                    if brother.leftChild.color == Color.BLACK:
                        brother.rightChild.color = Color.BLACK
                        brother.color = Color.RED
                        self._left_rotate(brother)
                        brother = parent.leftChild
                    brother.color = parent.color
                    parent.color = Color.BLACK
                    brother.leftChild.color = Color.BLACK
                    self._right_rotate(parent)
                    nodeForFixup = self._root
                    parent = self._noneNode
        nodeForFixup.color = Color.BLACK

    def __iter__(self) -> Iterator[K]:
        return SortedDictKeyIterator(self._root, self._noneNode)

    def items(self) -> Iterator[tuple[K, T]]:
        return SortedDictItemIterator(self._root, self._noneNode)

    def __contains__(self, key: K) -> bool:
        return self._findNode(key) is not None


class SortedDictKeyIterator(Generic[K, T]):
    def __init__(self, root: SortedDictNode[K, T], none_node: SortedDictNode[K, T]) -> None:
        self._stack: list[SortedDictNode[K, T]] = []
        self._none: SortedDictNode[K, T] = none_node
        self._current: SortedDictNode[K, T] = root
        self._go_left()

    def _go_left(self) -> None:
        while self._current != self._none:
            self._stack.append(self._current)
            self._current = self._current.leftChild

    def __iter__(self) -> Iterator[K]:
        return self

    def __next__(self) -> K:
        if not self._stack:
            raise StopIteration
        node = self._stack.pop()
        result = node.key
        self._current = node.rightChild
        self._go_left()
        return result


class SortedDictItemIterator(Generic[K, T]):
    def __init__(self, root: SortedDictNode[K, T], none_node: SortedDictNode[K, T]) -> None:
        self._stack: list[SortedDictNode[K, T]] = []
        self._none: SortedDictNode[K, T] = none_node
        self._current: SortedDictNode[K, T] = root
        self._go_left()

    def _go_left(self) -> None:
        while self._current != self._none:
            self._stack.append(self._current)
            self._current = self._current.leftChild

    def __iter__(self) -> Iterator[tuple[K, T]]:
        return self

    def __next__(self) -> tuple[K, T]:
        if not self._stack:
            raise StopIteration
        node = self._stack.pop()
        result = (node.key, node.value)
        self._current = node.rightChild
        self._go_left()
        return result