# -*- coding: utf-8 -*-
import numpy as np
import sys
import scipy.spatial
import marshal
#import heapq

cosine_distance = scipy.spatial.distance.cosine

first = lambda x: x[0]
second = lambda x: x[1]

class VecIndexReader:
    def __init__(self, indexfile, vecfile):
        self.dimension = 128
        if indexfile.endswith(".marshal"):
            indexfile_f = open(indexfile, "rb")
            self.indices = marshal.load(indexfile_f)
        else:
            indexfile_f = open(indexfile, "r")
            self.indices = {}
            for line in indexfile_f:
                parts = line.strip().split()
                self.indices[first(parts)] = int(second(parts))
        self.vecfile = open(vecfile, "rb")

    def find(self, word):
        if word not in self.indices:
            return None
        self.vecfile.seek(2 * self.dimension * self.indices[word])
        return np.fromfile(self.vecfile, dtype = np.float16,
                           count = self.dimension)

    def findbest(self, word):
        v = self.find(word)
        if v is not None:
            return v
        i = 1
        while i < len(word):
            v = self.find(word[:len(word) - i])
            if v is not None:
                return v
            v = vindex.find(word[i:])
            if v is not None:
                return v
            i += 1
        return(np.zeros(self.dimension))
            
class VecReader:
    def __init__(self, vecfile, datatype = "float32", vocabulary = None, top_n = None, verbose = False):
        self.vectors = []
        self.word2vec = {}
        f = open(vecfile, "rb")
        firstline = f.readline().strip()
        self.vocabulary_size, self.dimension = map(int, firstline.split())
        self.orig_vocabulary_size = self.vocabulary_size
        fraction_of_vocab = self.vocabulary_size // 20
        if verbose:
            print("reading from " + vecfile, end = '', flush=True)
        wordsread = 0
        if vecfile.endswith(".bin"):
            if datatype == "float32":
                datasize = 4
            elif datatype == "float16":
                datasize = 2
            data = f.read()
            i = 0
            while i < len(data):
                if top_n and top_n <= wordsread:
                    self.vocabulary_size = len(self.vectors)
                    break
                wordsread += 1
                if verbose and wordsread % fraction_of_vocab == 0:
                    print(".", end = '', flush=True)
                spacepos = data.index(ord(' '), i)
                try:
                    word = str(data[i:spacepos], "utf-8")
                except UnicodeDecodeError:
                    self.vocabulary_size -= 1
                    i = spacepos + 1 + 1 + self.dimension * datasize
                    continue
                floats = np.frombuffer(data, offset = spacepos + 1,
                                       count = self.dimension, dtype=datatype).astype("float16")
                i = spacepos + 1 + 1 + self.dimension * datasize
                if not vocabulary or word in vocabulary:
                    self.vectors.append((word, floats))
                    self.word2vec[word] = floats
                else:
                    self.vocabulary_size -= 1
        else:
            for line in f:
                if top_n and top_n <= wordsread:
                    self.vocabulary_size = len(self.vectors)
                    break
                wordsread += 1
                if verbose and wordsread % fraction_of_vocab == 0:
                    print(".", end='', flush=True)
                spacepos = line.index(ord(' '))
                try:
                    word = str(line[:spacepos], "utf-8")
                except UnicodeDecodeError:
                    print("unicode error!")
                    self.vocabulary_size -= 1
                    continue
                line = line.strip()
                floats = np.array(list(map(float, line[spacepos+1:].split())), dtype=datatype).astype("float16")
                if not vocabulary or word in vocabulary:
                    self.vectors.append((word, floats))
                    self.word2vec[word] = floats
                else:
                    self.vocabulary_size -= 1
        if verbose:
            print()

    def get_vocabulary(self):
        return self.word2vec.keys()
                    
    def remove_words(self, wds):
        words_to_keep = set(self.word2vec.keys()).difference(set(wds))
        self.word2vec = { w: self.word2vec[w] for w in words_to_keep }
        self.vectors = [(w, self.word2vec[w]) for w in words_to_keep]

    def keep_words(self, wds):
        words_to_keep = set(self.word2vec.keys()).intersection(set(wds))
        self.word2vec = { w: self.word2vec[w] for w in words_to_keep }
        self.vectors = [(w, self.word2vec[w]) for w in words_to_keep]

    def closest_n_vecs(self, v, n):
        sortkey = lambda x: cosine_distance(x[1], v)
        retval = []
        return list(map(lambda x: x[0], sorted(self.vectors, key = sortkey)[:n]))
        
    def closest_n_vecs_(self, v, n):
        sortkey = lambda x: cosine_distance(x[1], v)
        retval = []
        if n == 0:
            return retval
        for vec in self.vectors:
            if len(retval) == 0:
                retval.append(vec)
                continue
            if len(retval) >= n:
                if sortkey(vec) >= sortkey(retval[-1]):
                    continue
                else:
                    for i in range(len(retval) - 1, -1, -1):
                        if sortkey(vec) >= sortkey(retval[i-1]):
                            retval[i] = vec
                            break
        return list(map(lambda x: x[0], sorted(self.vectors, key = sortkey)[:n]))
        
    def closest_n(self, w, n):
        if w not in self.word2vec:
            return []
        sortkey = lambda x: cosine_distance(x[1], self.word2vec[w])
        v_is_not_w = lambda x: x[0] != w
#        best_n = heapq.nsmallest(n, self.vectors, sortkey)
#        self.vectors.sort(key = sortkey)
#        return map(lambda x: x[0], best_n) #self.vectors[n])
        return map(lambda x: x[0], sorted(
            filter(v_is_not_w, self.vectors),
            key = sortkey)[:n])
#        return map(lambda x: x[0], self.vectors[:n])

