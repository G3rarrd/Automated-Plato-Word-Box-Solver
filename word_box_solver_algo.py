import copy
from typing import List
import ctypes

import json

with open('wordList.json', 'r') as file:
    wordList = json.load(file)

class TrieNode:
    def __init__(self) :
        self.isEnd = False
        self.children = [None] * 26
        self.count = 0
        self.index = -1

        
class Trie:
    def __init__ (self) -> None :
        self.root : TrieNode = TrieNode()
        self.words : List[str] = wordList
        
    def insert(self, word, wordId) -> None:
        node : TrieNode = self.root
        for c in word:
            index = ord(c) - ord("a")
            if (not node.children[index]):
                node.children[index] = TrieNode()
            node = node.children[index]
            node.count += 1
        node.isEnd = True
        node.index = wordId
        
    def createTrie(self) -> None:
        for i in range(len(self.words)):
            w : str = self.words[i]
            if (len(w) > 3):
                self.insert(w, i)
                
    def rebuild(self, foundWords : List[tuple[str, int]]) -> None:
        for w, wId in foundWords:
            if (len(w) > 3):
                self.insert(w, wId)
            
        
class WordBoxSolver:
    def __init__ (self):
        self.trie = Trie()
        self.trie.createTrie()
        self.found_words : dict[tuple[str, int], list[list[int]]] = {}
        
        self.window_left : int
        self.window_top : int
        
        self.letter_grid : List[List[str]] = []
        self.cell_window_positions : List[List[tuple[int, int]]] = []
        
        self.is_solving = False
        self.paused = False
        
        self.speed = 0.8

        
    def is_valid(self, row : int, col : int, rowSize : int, colSize : int ) -> bool: 
        return (row >= 0 and row < rowSize and col >= 0 and col < colSize)
    
    def dfs(self, grid: List[List[str]], node: TrieNode,  path : List[List[int]], row : int, col : int):
        
        if (not self.is_valid(row, col, len(grid), len(grid[0])) or grid[row][col] == ".") :
            return
        
        char : str = grid[row][col]
        index : int = ord(char[0]) - ord("a")
        
        
        if (not node or not node.children[index] or node.children[index].count == 0): return
        
        node = node.children[index]
        grid[row][col] = "."
        
        if (len(char) > 1) :
            if (node):
                node = node.children[ord(char[1]) - ord("a")]
        
        if (not node or node.count < 0):
            grid[row][col] = char
            return
        
        path.append([row, col])
        
        if(node.isEnd):
            wordFound = self.trie.words[node.index]
            key = (wordFound, node.index)
            self.found_words[key] = copy.deepcopy(path)
            node.isEnd = False
            
            # Pruning
            prune : Trie = self.trie.root
            for c in wordFound :
                prune = prune.children[ord(c) - ord("a")]
                prune.count -= 1
                
                
        self.dfs(grid, node, path,  row-1, col-1)
        self.dfs(grid, node,  path,  row-1, col)
        self.dfs(grid, node,  path,  row-1, col+1)
        
        self.dfs(grid, node,  path,  row, col-1)
        self.dfs(grid, node,  path,  row, col+1)
        
        self.dfs(grid, node,  path,  row+1, col-1)
        self.dfs(grid, node,  path,  row+1, col)
        self.dfs(grid, node,  path,  row+1, col+1)
        
        # Backtrack
        grid[row][col] = char
        path.pop()
        
    def solve(self) :
        self.found_words = {} # To remove the previous results
        for row in range(len(self.letter_grid)):
            for col in range(len(self.letter_grid[0])):
                self.dfs(self.letter_grid, self.trie.root, [], row, col)
        
        self.trie.rebuild(foundWords=self.found_words)
        
    def set_cell_positions(self, contour_info_grid : list[list[tuple[int, int, str]]]) -> None :
        self.cell_window_positions = [[(pos[0], pos[1]) for pos in row] 
                            for row in contour_info_grid]
    
    def set_screen_front(self, hwnd):
        ctypes.windll.user32.ShowWindow(hwnd, 5)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        
    def set_letter_grid(self, letter_grid : List[List[str]]) -> None:
        self.letter_grid = letter_grid
