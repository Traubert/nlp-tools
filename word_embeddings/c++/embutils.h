#pragma once

#include <time.h>
#include <iomanip>
#include <cmath>
#include <string>
#include <exception>
#include <vector>
#include <iostream>
#include <fstream>
#include <sstream>

struct WordEmbedding;
struct Vector;

typedef std::pair<std::string, std::string> StringPair;
typedef float WordVecFloat;
typedef std::vector<WordVecFloat> WVector;
typedef std::vector<std::string> StringVector;
typedef std::vector<WordEmbedding> WordEmbeddingVector;
typedef std::pair<WordEmbedding, WordVecFloat> ScoredEmbedding;
typedef std::vector<ScoredEmbedding> ScoredEmbeddings;
typedef std::pair<std::string, WordVecFloat> ScoredWord;
typedef std::vector<ScoredWord> ScoredWords;

// For swig
typedef std::pair<std::string, WVector> WordWithVector;

struct Vector: public WVector{
    WordVecFloat cached_norm;

    Vector(void);
    Vector(WVector v);
    void cache_norm(void);
    WordVecFloat get_norm(void) const { return cached_norm; }
    WordVecFloat cosine_distance(const Vector & other) const;
};

struct WordEmbedding {
    std::string word;
    Vector vector;

    WordVecFloat cosine_distance(const WordEmbedding & other) const;
    WordVecFloat cosine_distance(const Vector & other) const;
};

struct WordEmbeddings: public WordEmbeddingVector {
    void load_from_file(std::string filename);

    WordEmbedding get(const std::string & word) const;
    WordEmbedding get_exact(const std::string & word) const;
    WordWithVector get_embedding(const std::string & word) const;
    WordVecFloat get_distance(const std::string& word1, const std::string& word2) const;

    ScoredEmbeddings get_top_n(
        const Vector & comparison_point,
        size_t n = 10) const;

    ScoredEmbeddings get_top_n(
        const WordEmbedding & comparison_point,
        size_t n = 10) const;

    ScoredEmbeddings get_top_n_in_transformed_space(
        size_t n,
        const WVector & comparison_point,
        const WVector & plane_vec,
        WordVecFloat translation_term,
        bool negative,
        WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords get_top_n_words_in_transformed_space(
        size_t n,
        const WVector & comparison_point,
        const WVector & plane_vec,
        WordVecFloat translation_term,
        bool negative,
        WordVecFloat vector_similarity_projection_factor = 1.0) const;
    
    ScoredWords get_top_n_words(
        const Vector & comparison_point,
        size_t n = 10) const;

    ScoredWords get_top_n_words(
        const WordEmbedding & comparison_point,
        size_t n = 10) const;

    ScoredWords like(const std::string & word,
                     unsigned int nwords = 10) const;
    
    ScoredWords like(const std::string & word1, const std::string & word2,
                     unsigned int nwords, bool negative,
                     WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords like(const std::string & word1, const std::string & word2,
                     unsigned int nwords = 10, WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords unlike(const std::string & word1, const std::string & word2,
                       unsigned int nwords = 10, WordVecFloat vector_similarity_projection_factor = 1.0) const;
};

WordEmbedding operator-(WordEmbedding l, const WordEmbedding & r);
WordEmbedding operator+(WordEmbedding l, const WordEmbedding & r);
WVector operator-(WVector l, const WVector & r);
WVector operator+(WVector l, const WVector & r);
WVector pointwise_multiplication(WVector l, const WVector & r);
WVector scalar_multiplication(WordVecFloat l, WVector r);
WordVecFloat dot_product(const WVector & l, const WVector & r);
WordVecFloat square_sum(const Vector & v);
WordVecFloat square_sum(const WVector & v);
//WordVecFloat norm(const Vector & v);
WordVecFloat norm(const WVector & v);

