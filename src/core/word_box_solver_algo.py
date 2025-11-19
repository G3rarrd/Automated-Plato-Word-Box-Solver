import copy
from typing import List
import ctypes

import json

# Holds all the possible words that can be used
with open('wordList.json', 'r') as file:
    wordList = json.load(file)

class TrieNode:
    def __init__(self) :
        """
        Set's up a Trie node with 26 children, end-of-word flag, 
        count, and optional index for word tracking.
        """
        self.isEnd: bool = False
        self.children: list = [None] * 26 # faster than using a hashmap
        self.count: int = 0
        self.index:int = -1

        
class Trie:
    def __init__ (self) -> None :
        """
        Initializes the Trie with a root node and stores the list of words.
        """
        self.root : TrieNode = TrieNode()
        self.words : List[str] = wordList
        
    def insert(self, word, wordId) -> None:
        """
        Inserts a word into the Trie, updating node counts
        and marking the end of the word.
    
        Args:
            word (str): The word to insert.
            wordId (int): The index or ID associated with the word.
        """
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
        """
        Creates the Trie structure based off all the existing words
        with a length greater than 3
        """
        for i in range(len(self.words)):
            w : str = self.words[i]
            if (len(w) > 3):
                self.insert(w, i)
                
    def rebuild(self, foundWords : List[tuple[str, int]]) -> None:
        """
        Adds back the pruned words to the trie

        Args:
            foundWords (list): All the words that were found in the grid
        """
        for w, wId in foundWords:
            if (len(w) > 3):
                self.insert(w, wId)
            
        
class WordBoxSolver:
    def __init__ (self):
        self.trie = Trie()
        self.trie.createTrie() # Create the dictionary tree
        self.found_words : dict[tuple[str, int], list[list[int]]] = {}
        
        self.window_left : int
        self.window_top : int
        
        self.letter_grid : List[List[str]] = []
        self.cell_window_positions : List[List[tuple[int, int]]] = []
        
        self.is_solving = False
        self.paused = False
        
        self.speed = 0.8

        
    def is_valid(self, row : int, col : int, rowSize : int, colSize : int ) -> bool: 
        """ Grid boundary validation """
        return (row >= 0 and row < rowSize and col >= 0 and col < colSize)
    
    def dfs(self, grid: List[List[str]], node: TrieNode,  path : List[List[int]], row : int, col : int):
        """
        Performs depth-first search to find valid words in the letter grid using a trie.
        
        Explores all 8 possible directions from each cell to form words that exist in the dictionary.
        Implements backtracking to mark visited cells and restores state during recursion unwinding.
        
        Args:
            grid: 2D list of characters representing the game board
            node: Current node in the trie during traversal
            path: List of coordinates for the current word being formed
            row: Current row position in the grid
            col: Current column position in the grid
        """

        if (not self.is_valid(row, col, len(grid), len(grid[0])) or grid[row][col] == ".") :
            return
        
        char : str = grid[row][col]
        index : int = ord(char[0]) - ord("a")
        
        
        if (not node or not node.children[index] or node.children[index].count == 0): return
        
        # Move to the next node in the trie
        node = node.children[index]

        # Mark as visited
        grid[row][col] = "."
        
        # Handles multi character inputs
        if (len(char) > 1) :
            if (node):
                node = node.children[ord(char[1]) - ord("a")]
        
        if (not node or node.count < 0):
            grid[row][col] = char
            return
        
        path.append([row, col])

        # Check if a word has been found
        if(node.isEnd):
            wordFound = self.trie.words[node.index]
            key = (wordFound, node.index)
            self.found_words[key] = copy.deepcopy(path)
            node.isEnd = False # mark as False to avoid duplicates
            
            # Pruning
            prune : Trie = self.trie.root
            for c in wordFound :
                prune = prune.children[ord(c) - ord("a")]
                prune.count -= 1
        

        # Top, Bottom
        self.dfs(grid, node,  path,  row-1, col)
        self.dfs(grid, node,  path,  row+1, col)

        # Left, Right
        self.dfs(grid, node,  path,  row, col-1)
        self.dfs(grid, node,  path,  row, col+1)
        
        # Top-left, Top, Top-right
        self.dfs(grid, node, path,  row-1, col-1)
        self.dfs(grid, node,  path,  row-1, col+1)

        # Bottom-left, Bottom-right
        self.dfs(grid, node,  path,  row+1, col-1)
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
        """
        Ensures the window is at the front for screen capture and automation
        """
        ctypes.windll.user32.ShowWindow(hwnd, 5)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        
    def set_letter_grid(self, letter_grid : List[List[str]]) -> None:
        self.letter_grid = letter_grid
