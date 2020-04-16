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
#include <functional>

#include "immintrin.h"

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

class LikeUnlikeTransformer {
    WVector comparison_point_cache;
    WVector plane_vec;
    bool negative;
    WordVecFloat plane_vec_square_sum;
    WordVecFloat comparison_point_norm;
    WordVecFloat translation_term;
    WordVecFloat projection_factor;
    
public:
    LikeUnlikeTransformer(
        const WVector & first_point,
        const WVector & second_point,
        bool is_negative,
        WordVecFloat vector_similarity_projection_factor = 1.0);

    Vector operator() (const Vector & original);

    const WVector & get_comparison_point(void) { return comparison_point_cache; }
};

struct WordEmbeddings: public WordEmbeddingVector {
    size_t dimension;
    
    void load_from_file(const std::string & filename,
                        float fraction);
    void load_from_file(const std::string & filename,
                        unsigned int limit = 0);
    void load_from_file(
        const std::string & filename,
        std::function<unsigned int (size_t lexicon_size)> limiter);
    WordEmbedding get(const std::string & word) const;
    WordEmbedding get_exact(const std::string & word) const;
    WordWithVector get_embedding(const std::string & word) const;
    WordVecFloat get_distance(const std::string& word1, const std::string& word2) const;

    ScoredEmbeddings get_top_n(
        const Vector & _comparison_point,
        size_t n = 10) const;

    ScoredEmbeddings get_top_n(
        const WordEmbedding & _comparison_point,
        size_t n = 10) const;

    ScoredWords get_words_at_distance_under(
        const std::string & comparison_word,
        WordVecFloat distance) const;

    ScoredEmbeddings get_top_n_in_transformed_space(
        size_t n,
        const WVector & comparison_point,
        const WVector & plane_vec,
        WordVecFloat translation_term,
        bool negative,
        WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredEmbeddings get_top_n_in_transformed_space(
        size_t n,
        LikeUnlikeTransformer transformer) const;

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
WordVecFloat norm(const WVector & v);

